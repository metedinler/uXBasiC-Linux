#!/usr/bin/env python3
"""uXBasic native library ABI auditor and wrapper normalizer.

The tool is intentionally dependency-free. It treats runtime_ext C headers/sources
as the ABI source of truth and validates every CALL(DLL) in libsx wrappers.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

MAX_RUNTIME_ARGS = 10
VALID_TYPES = {"VOID", "I8", "U8", "I16", "U16", "I32", "U32", "I64", "U64", "F32", "F64", "LONGDOUBLE", "PTR", "STRPTR", "WSTRPTR", "STRUCT", "UNION", "BYREF"}

@dataclass(frozen=True)
class CPrototype:
    symbol: str
    return_c: str
    params_c: tuple[str, ...]
    source: str

@dataclass
class AuditRow:
    wrapper: str
    line: int
    dll: str
    symbol: str
    expected_return: str
    actual_return: str
    expected_args: str
    actual_args: str
    arity: int
    status: str
    message: str


def strip_c_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//.*", " ", text)


C_ABI_MACRO_RE = re.compile(
    r"\b(?:UX_EXPORT|UXB_CALL|UXCAPI_CALL|UXFFI_CALL|UX[A-Z0-9_]*(?:_API|_EXPORT|_IMPORT|_CALL)|"
    r"WINAPI|APIENTRY|CALLBACK|NTAPI)\b"
)


def strip_c_abi_macros(text: str) -> str:
    return C_ABI_MACRO_RE.sub(" ", text)


def split_top_level(text: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    depth = 0
    quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            quote = not quote
            current.append(ch)
        elif not quote and ch == '(':
            depth += 1
            current.append(ch)
        elif not quote and ch == ')':
            depth -= 1
            current.append(ch)
        elif not quote and depth == 0 and ch == ',':
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    if ''.join(current).strip():
        result.append(''.join(current).strip())
    return result


def normalize_c_decl(text: str, *, parameter: bool = False) -> str:
    text = re.sub(r"__declspec\s*\([^)]*\)", " ", text)
    text = strip_c_abi_macros(text)
    text = re.sub(r"\b(?:extern|static|inline|__inline|__cdecl|__stdcall|WINAPI|APIENTRY|CALLBACK|NTAPI)\b", " ", text)
    text = ' '.join(text.replace('\n', ' ').replace('\t', ' ').split())
    if parameter:
        if text == '...':
            return text
        text = re.sub(r"\[[^\]]*\]\s*$", " *", text)
        match = re.match(r"^(.*?)([A-Za-z_]\w*)$", text)
        if match and match.group(1).strip():
            prefix = match.group(1)
            if prefix[-1].isspace() or prefix[-1] == '*':
                text = prefix.strip()
    text = re.sub(r"\b(?:const|volatile|restrict|struct|enum)\b", " ", text)
    return ' '.join(text.split()).strip()


def collect_c_prototypes(root: Path) -> dict[str, CPrototype]:
    """Collect exported ABI declarations from C/C++ and FreeBASIC runtimes.

    The ecosystem deliberately contains both GCC-built C DLLs and FreeBASIC-
    built Windows DLLs.  Auditing only C files produced hundreds of false
    missing-symbol reports, which hid real signature mismatches.
    """
    pattern = re.compile(
        r"(?m)(?:^|[;{}]\s*)\s*"
        r"((?:__declspec\s*\([^)]*\)\s*)?"
        r"(?:[A-Z][A-Z0-9_]*(?:_API|_EXPORT|_IMPORT|_CALL)\s*)?"
        r"(?:extern\s+)?(?:static\s+)?[A-Za-z_][\w\s\*]*?)\s+"
        r"([A-Za-z_]\w*)\s*\(([^;{}()]*(?:\([^)]*\)[^;{}()]*)*)\)\s*(?=;|\{)"
    )
    prototypes: dict[str, CPrototype] = {}
    paths = []
    for suffix in ("*.c", "*.h", "*.cpp", "*.hpp", "*.cc", "*.cxx"):
        paths.extend(root.glob(f"runtime_ext/**/{suffix}"))
        paths.extend(root.glob(f"native/**/{suffix}"))
    for path in paths:
        text = strip_c_abi_macros(strip_c_comments(path.read_text(encoding="utf-8", errors="ignore")))
        # Many C APIs spell pointer returns as `const char *name(...)` without
        # whitespace between `*` and the symbol.  Normalize that spelling for
        # the declaration matcher instead of losing all STRPTR-return exports.
        text = re.sub(r"(\*+)([A-Za-z_]\w*\s*\()", r"\1 \2", text)
        for match in pattern.finditer(text):
            symbol = match.group(2)
            if symbol in {"if", "for", "while", "switch", "return", "sizeof"}:
                continue
            ret = normalize_c_decl(match.group(1))
            raw_params = match.group(3).strip()
            params = () if raw_params in {"", "void"} else tuple(
                normalize_c_decl(item, parameter=True) for item in split_top_level(raw_params)
            )
            proto = CPrototype(symbol, ret, params, str(path.relative_to(root)).replace('\\', '/'))
            if symbol not in prototypes or path.suffix.lower() in {".h", ".hpp"}:
                prototypes[symbol] = proto

    prototypes.update(collect_freebasic_prototypes(root, prototypes))
    return prototypes


def fb_type_to_c(type_text: str, *, byref: bool = False) -> str:
    raw = ' '.join(type_text.strip().split())
    low = raw.lower()
    if byref or low.endswith(' ptr') or low == 'any ptr':
        if low.startswith('zstring') or low.startswith('string'):
            return 'char *'
        return 'void *'
    mapping = {
        'void': 'void', 'long': 'int32_t', 'integer': 'int32_t', 'bool': 'int32_t',
        'ulong': 'uint32_t', 'uint': 'uint32_t', 'dword': 'uint32_t',
        'short': 'int16_t', 'ushort': 'uint16_t', 'byte': 'int8_t', 'ubyte': 'uint8_t',
        'longint': 'int64_t', 'ulongint': 'uint64_t',
        'uxb_i64': 'int64_t', 'uxb_u64': 'uint64_t', 'uxb_handle': 'uint64_t',
        'single': 'float', 'double': 'double',
    }
    if low in mapping:
        return mapping[low]
    if low.startswith('zstring') or low == 'string':
        return 'char *'
    if low.endswith(' ptr'):
        return 'void *'
    # FreeBASIC UDT values are not directly ABI10-safe.  Treat named handle-like
    # aliases as integer handles and all other opaque values as int32 enums.
    if low.endswith('handle') or low.endswith('_handle'):
        return 'uint64_t'
    return 'int32_t'


def collect_freebasic_prototypes(root: Path, existing: dict[str, CPrototype]) -> dict[str, CPrototype]:
    result: dict[str, CPrototype] = {}
    decl = re.compile(
        r"(?im)^\s*public\s+(function|sub)\s+[A-Za-z_]\w*\s+alias\s+\"([^\"]+)\"\s*"
        r"\((.*?)\)\s*(?:as\s+([A-Za-z_][\w ]*(?:\s+ptr)?))?\s+UXB_EXPORT\b"
    )
    for path in root.glob('runtime_ext/**/*.bas'):
        text = path.read_text(encoding='utf-8', errors='ignore')
        # Declarations in this tree are single-line by contract; collapse explicit
        # FreeBASIC continuation lines without disturbing normal statement lines.
        text = re.sub(r"_\s*\r?\n\s*", " ", text)
        for match in decl.finditer(text):
            kind, symbol, raw_params, return_fb = match.groups()
            params: list[str] = []
            for item in split_top_level(raw_params):
                item = item.strip()
                if not item:
                    continue
                pm = re.match(r"(?i)^(byval|byref)?\s*([A-Za-z_]\w*)\s+as\s+(.+)$", item)
                if not pm:
                    continue
                mode, _name, fb_type = pm.groups()
                params.append(fb_type_to_c(fb_type, byref=(mode or '').lower() == 'byref'))
            ret = 'void' if kind.lower() == 'sub' else fb_type_to_c(return_fb or 'long')
            proto = CPrototype(symbol, ret, tuple(params), str(path.relative_to(root)).replace('\\', '/'))
            if symbol not in existing:
                result[symbol] = proto
    return result


def c_type_to_uxb(c_type: str, expression: str = "", wrapper_types: dict[str, str] | None = None, *, return_position: bool = False) -> str:
    wrapper_types = wrapper_types or {}
    c = ' '.join(c_type.replace('\t', ' ').split())
    low = c.lower().replace(' ', '')
    expr = expression.strip()
    expr_type = wrapper_types.get(expr.lower(), "").upper()

    if c == '...':
        raise ValueError("variadic C functions are not supported by CALL(DLL)")
    # uxclz deliberately exposes integer generation handles rather than raw
    # pointers. Preserve its public typedef contract when normalizing wrappers.
    if low in {"uxclz_handle"}:
        return "U64"
    if low in {"uxclz_type_id", "uxclz_method_id"}:
        return "U32"
    if low in {"uxclz_destructor_fn", "uxclz_method_fn", "uxclz_multimethod_fn"}:
        return "PTR"
    if '*' in c or low.endswith('handle') or 'handle*' in low:
        base = low.replace('*', '')
        if 'char' in base and (return_position or expr_type == "STRING" or (len(expr) >= 2 and expr[0] == '"' and expr[-1] == '"')):
            return "STRPTR"
        return "PTR"
    if low in {"void"}:
        return "VOID"
    if "double" in low or low in {"longdouble"}:
        return "F64"
    if "float" in low:
        # uXBasic's current native ABI transports floating arguments as F64.
        return "F64"
    if any(token in low for token in ("uint64_t", "unsignedlonglong", "size_t", "uintptr_t")):
        return "U64"
    if any(token in low for token in ("int64_t", "longlong", "intptr_t")):
        return "I64"
    if any(token in low for token in ("uint32_t", "unsignedint", "unsignedlong", "unsignedchar", "uint16_t", "uint8_t")):
        return "U32"
    if any(token in low for token in ("int32_t", "signedint", "int", "long", "short", "bool")):
        return "I32"
    # Opaque typedef values and enums are integer-sized unless they are named handles.
    if re.match(r"^[A-Za-z_]\w*$", c):
        if c.lower().endswith("handle"):
            return "PTR"
        return "I32"
    raise ValueError(f"unmapped C type: {c_type}")


def parse_wrapper_constants(lines: list[str]) -> dict[str, str]:
    constants: dict[str, str] = {}
    for line in lines:
        match = re.match(r"\s*CONST\s+([A-Za-z_]\w*)\s*=\s*\"([^\"]+)\"", line, re.I)
        if match:
            constants[match.group(1).upper()] = match.group(2)
    return constants


def parse_declared_types(lines: list[str]) -> list[dict[str, str]]:
    """Return a type environment for every source line."""
    env: dict[str, str] = {}
    result: list[dict[str, str]] = []
    for line in lines:
        head = re.match(r"\s*(?:FUNCTION|SUB)\s+[A-Za-z_][\w.]*\s*\((.*)\)", line, re.I)
        if head:
            env = {}
            for item in split_top_level(head.group(1)):
                arg = re.match(r"\s*([A-Za-z_]\w*)\s+AS\s+([A-Za-z_][\w]*)", item, re.I)
                if arg:
                    env[arg.group(1).lower()] = arg.group(2).upper()
        dim = re.match(r"\s*DIM\s+([A-Za-z_]\w*)\s+AS\s+([A-Za-z_][\w]*)", line, re.I)
        if dim:
            env[dim.group(1).lower()] = dim.group(2).upper()
        result.append(dict(env))
        if re.match(r"\s*END\s+(?:FUNCTION|SUB)\b", line, re.I):
            env = {}
    return result


def find_call_span(line: str) -> tuple[int, int] | None:
    match = re.search(r"CALL\s*\(\s*DLL\s*,", line, re.I)
    if not match or line.lstrip().startswith("'"):
        return None
    start = match.start()
    depth = 0
    quote = False
    for index in range(match.start(), len(line)):
        ch = line[index]
        if ch == '"':
            quote = not quote
        elif not quote and ch == '(':
            depth += 1
        elif not quote and ch == ')':
            depth -= 1
            if depth == 0:
                return start, index + 1
    return None


def parse_existing_call(call_text: str, constants: dict[str, str]) -> tuple[str, str, list[str]]:
    inner = call_text[call_text.find('(') + 1 : -1]
    parts = split_top_level(inner)
    if len(parts) < 3 or parts[0].upper() != "DLL":
        raise ValueError("not a CALL(DLL) expression")
    dll_expr = parts[1]
    if dll_expr.startswith('"') and dll_expr.endswith('"'):
        dll = dll_expr[1:-1]
    else:
        dll = constants.get(dll_expr.upper(), "")
    if not dll:
        raise ValueError(f"DLL name is not a literal or known CONST: {dll_expr}")
    symbol_expr = parts[2]
    if not (symbol_expr.startswith('"') and symbol_expr.endswith('"')):
        raise ValueError("symbol must be a string literal")
    symbol = symbol_expr[1:-1]
    return dll, symbol, parts[3:]


def infer_runtime_args(existing_tail: list[str]) -> list[str]:
    if not existing_tail:
        return []
    pos = 0
    if existing_tail[pos].upper() in VALID_TYPES | {"BYVAL"}:
        pos += 1
        if pos < len(existing_tail) and existing_tail[pos].upper() in {"CDECL", "STDCALL"}:
            pos += 1
        if pos < len(existing_tail) and existing_tail[pos].startswith('"') and existing_tail[pos].endswith('"'):
            candidate = existing_tail[pos][1:-1]
            if all(piece.strip().upper() in VALID_TYPES | {"BYVAL"} for piece in candidate.split(',')):
                pos += 1
    return existing_tail[pos:]


def canonical_call(dll: str, proto: CPrototype, runtime_args: list[str], env: dict[str, str]) -> tuple[str, str, list[str]]:
    ret = c_type_to_uxb(proto.return_c, return_position=True)
    if len(proto.params_c) != len(runtime_args):
        raise ValueError(f"arity mismatch C={len(proto.params_c)} wrapper={len(runtime_args)}")
    if len(runtime_args) > MAX_RUNTIME_ARGS:
        raise ValueError(f"arity {len(runtime_args)} exceeds ABI{MAX_RUNTIME_ARGS}")
    arg_types = [c_type_to_uxb(c, expr, env) for c, expr in zip(proto.params_c, runtime_args)]
    metadata = ["DLL", f'"{dll}"', f'"{proto.symbol}"', ret, "CDECL"]
    if arg_types:
        metadata.append('"' + ','.join(arg_types) + '"')
    metadata.extend(runtime_args)
    return "CALL(" + ", ".join(metadata) + ")", ret, arg_types


def normalize_wrappers(root: Path, *, write: bool, report_csv: Path | None = None, report_json: Path | None = None) -> tuple[list[AuditRow], int]:
    prototypes = collect_c_prototypes(root)
    rows: list[AuditRow] = []
    changed_files = 0
    for wrapper in sorted(root.glob("libsx/*/*.bas")):
        if "PLACEHOLDER" in wrapper.name.upper():
            continue
        lines = wrapper.read_text(encoding="utf-8", errors="ignore").splitlines()
        constants = parse_wrapper_constants(lines)
        envs = parse_declared_types(lines)
        out_lines = list(lines)
        file_changed = False
        for index, line in enumerate(lines):
            span = find_call_span(line)
            if span is None:
                continue
            start, end = span
            call_text = line[start:end]
            try:
                dll, symbol, tail = parse_existing_call(call_text, constants)
                proto = prototypes.get(symbol)
                if proto is None:
                    raise ValueError("symbol not found in runtime_ext C headers/sources")
                runtime_args = infer_runtime_args(tail)
                new_call, expected_ret, expected_args = canonical_call(dll, proto, runtime_args, envs[index])
                # Parse current metadata for audit display.
                actual_ret = tail[0].upper() if tail and tail[0].upper() in VALID_TYPES | {"BYVAL"} else "MISSING"
                actual_convention = ""
                actual_types = ""
                if len(tail) >= 2 and tail[1].upper() in {"CDECL", "STDCALL"}:
                    actual_convention = tail[1].upper()
                    if len(tail) >= 3 and tail[2].startswith('"'):
                        actual_types = tail[2].strip('"').upper().replace(' ', '')
                elif len(tail) >= 2 and tail[1].startswith('"'):
                    actual_types = tail[1].strip('"').upper().replace(' ', '')
                expected_types_text = ','.join(expected_args).upper().replace(' ', '')
                semantic_ok = (
                    actual_ret == expected_ret and
                    (actual_convention in {"", "CDECL"}) and
                    actual_types == expected_types_text
                )
                needs_rewrite = not semantic_ok
                status = "OK" if semantic_ok else ("FIXED" if write else "MISMATCH")
                if write and needs_rewrite:
                    out_lines[index] = line[:start] + new_call + line[end:]
                    file_changed = True
                rows.append(AuditRow(
                    str(wrapper.relative_to(root)).replace('\\', '/'), index + 1, dll, symbol,
                    expected_ret, actual_ret, ','.join(expected_args), actual_types,
                    len(runtime_args), status, ""
                ))
            except Exception as exc:  # report every failure instead of aborting early
                rows.append(AuditRow(
                    str(wrapper.relative_to(root)).replace('\\', '/'), index + 1, "", "",
                    "", "", "", "", 0, "ERROR", str(exc)
                ))
        if file_changed:
            wrapper.write_text('\n'.join(out_lines) + '\n', encoding="utf-8")
            changed_files += 1

    if report_csv:
        report_csv.parent.mkdir(parents=True, exist_ok=True)
        with report_csv.open('w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(AuditRow.__dataclass_fields__))
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
    if report_json:
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_json.write_text(json.dumps({
            "schema": "uxb.library_abi_audit.v1",
            "max_runtime_args": MAX_RUNTIME_ARGS,
            "total_calls": len(rows),
            "errors": sum(row.status == "ERROR" for row in rows),
            "mismatches": sum(row.status == "MISMATCH" for row in rows),
            "fixed": sum(row.status == "FIXED" for row in rows),
            "max_observed_arity": max((row.arity for row in rows), default=0),
            "rows": [asdict(row) for row in rows],
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    failures = sum(row.status in {"ERROR", "MISMATCH"} for row in rows)
    return rows, changed_files if write else failures


def resolve_root(value: str) -> Path:
    candidate = Path(value).resolve()
    if (candidate / "runtime_ext").is_dir() and (candidate / "libsx").is_dir():
        return candidate
    if (candidate / "uxb" / "runtime_ext").is_dir():
        return candidate / "uxb"
    raise SystemExit(f"uXBasic root not found under: {candidate}")


def write_ffi_allowlist(rows: list[AuditRow], path: Path) -> None:
    entries = {
        (row.dll.upper(), row.symbol.upper(), row.expected_return.upper())
        for row in rows
        if row.status != "ERROR" and row.dll and row.symbol and row.expected_return
    }
    # Canonical runtime and release-gate calls do not live in libsx wrappers,
    # but they are part of the supported ABI10 surface.  Keep them in the
    # generated policy so normal production/test execution is warning-free.
    entries.update({
        ("KERNEL32.DLL", "GETCURRENTPROCESSID", "U32"),
        ("KERNEL32.DLL", "SLEEP", "VOID"),
        ("UXB_FFI_CONTRACT_TEST.DLL", "UXB_FFI_F64_FROM_I32", "F64"),
        ("UXB_FFI_CONTRACT_TEST.DLL", "UXB_FFI_SUM10_I32", "I64"),
        ("UXB_FFI_CONTRACT_TEST.DLL", "UXB_FFI_ECHO", "STRPTR"),
        ("UXCONFIG.DLL", "UXCONFIG_OPEN", "PTR"),
        ("UXCONFIG.DLL", "UXCONFIG_SET_STRING", "I32"),
        ("UXCONFIG.DLL", "UXCONFIG_GET_STRING", "STRPTR"),
        ("UXCONFIG.DLL", "UXCONFIG_PATH", "STRPTR"),
        ("UXCONFIG.DLL", "UXCONFIG_CLOSE", "VOID"),
        ("UXDATETIME.DLL", "UXDATETIME_UNIX_MS_UTC", "I64"),
        ("UXSYSTEM.DLL", "UXSYSTEM_CPU_COUNT", "I32"),
    })
    entries = sorted(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "UXB_FFI_ALLOWLIST_V1",
        "# Generated from ABI-verified libsx wrappers plus canonical ABI10 runtime calls.",
        "# Format: dll|symbol|return_type",
    ]
    lines.extend("|".join(entry) for entry in entries)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit/fix uXBasic CALL(DLL) wrappers against C ABI")
    parser.add_argument("--root", default=".", help="uxb directory or its parent")
    parser.add_argument("--fix", action="store_true", help="rewrite wrappers to canonical ABI syntax")
    parser.add_argument("--report-dir", default="reports/libraries/abi")
    parser.add_argument("--allowlist", default="build/manual/config/ffi_allowlist.txt",
                        help="write the runtime FFI allowlist after a clean ABI audit")
    args = parser.parse_args()
    root = resolve_root(args.root)
    report_dir = root / args.report_dir
    rows, result = normalize_wrappers(
        root, write=args.fix,
        report_csv=report_dir / "wrapper_abi_audit.csv",
        report_json=report_dir / "wrapper_abi_audit.json",
    )
    errors = sum(row.status == "ERROR" for row in rows)
    mismatches = sum(row.status == "MISMATCH" for row in rows)
    fixed = sum(row.status == "FIXED" for row in rows)
    print(f"ABI calls={len(rows)} errors={errors} mismatches={mismatches} fixed={fixed} max_arity={max((r.arity for r in rows), default=0)}")
    if args.fix:
        # Re-audit after writing; the build gate must see zero mismatches.
        verify_rows, _ = normalize_wrappers(root, write=False)
        verify_failures = sum(row.status in {"ERROR", "MISMATCH"} for row in verify_rows)
        print(f"ABI verify failures={verify_failures}")
        if verify_failures == 0:
            allowlist_path = root / args.allowlist
            write_ffi_allowlist(verify_rows, allowlist_path)
            print(f"FFI allowlist entries={len(set((r.dll.upper(), r.symbol.upper(), r.expected_return.upper()) for r in verify_rows))} path={allowlist_path}")
        return 0 if verify_failures == 0 else 1
    if errors == 0 and mismatches == 0:
        allowlist_path = root / args.allowlist
        write_ffi_allowlist(rows, allowlist_path)
        print(f"FFI allowlist entries={len(set((r.dll.upper(), r.symbol.upper(), r.expected_return.upper()) for r in rows))} path={allowlist_path}")
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
