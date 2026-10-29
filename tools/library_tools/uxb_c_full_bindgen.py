#!/usr/bin/env python3
"""Generate complete raw uXBasic bindings from a public C header surface.

The generator does not hand-pick convenience methods.  It scans every public
FunctionDecl matching the library manifest, verifies the actual PE DLL export
table, emits one uXBasic routine per C function, and emits C shims for public
static-inline functions.

Private symbols and function-like preprocessor macros are outside the DLL
function surface.  Variadic functions are represented by their original name
plus a final uxcapi Args handle.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

KIND = {
    "VOID": 0,
    "I8": 1,
    "U8": 2,
    "I16": 3,
    "U16": 4,
    "I32": 5,
    "U32": 6,
    "I64": 7,
    "U64": 8,
    "F32": 9,
    "F64": 10,
    "PTR": 11,
    "STRPTR": 12,
    "WSTRPTR": 13,
    "LONGDOUBLE": 14,
}

UXB_KEYWORDS = {
    "AS", "CALL", "CASE", "CLASS", "CONST", "DIM", "DO", "ELSE", "END",
    "EVENT", "EXIT", "FOR", "FUNCTION", "GOTO", "IF", "IN", "INPUT",
    "INTERFACE", "LOOP", "MAIN", "METHOD", "MODULE", "NAMESPACE", "NEXT",
    "ON", "OUTPUT", "PARALEL", "PIPE", "PRINT", "RETURN", "SELECT", "SET",
    "SLOT", "STEP", "SUB", "THEN", "THREAD", "TO", "TRIGGER", "TYPE",
    "USING", "WEND", "WHILE",
}


@dataclass
class CType:
    original: str
    canonical: str
    uxb_type: str
    kind_name: str
    arg_method: str
    result_method: str
    pointer: bool
    string_pointer: bool
    wstring_pointer: bool
    supported: bool
    reason: str = ""
    indirect: bool = False
    aggregate: bool = False


@dataclass
class Parameter:
    name: str
    c_type: str
    canonical_type: str
    mapped: CType


@dataclass
class Function:
    name: str
    return_type: str
    return_canonical: str
    return_mapped: CType
    parameters: list[Parameter]
    variadic: bool
    inline: bool
    storage: str
    exported: bool
    symbol: str
    dll_name: str
    source: str
    supported: bool
    reason: str = ""
    requires_shim: bool = False
    indirect_return: bool = False


@dataclass
class RecordField:
    name: str
    c_type: str
    canonical_type: str
    mapped: CType


@dataclass
class RecordInfo:
    c_type: str
    safe_name: str
    fields: list[RecordField]


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )
    return result


def walk(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield node
    for child in node.get("inner", []):
        if isinstance(child, dict):
            yield from walk(child)


def matches_any(name: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, name) for pattern in patterns)


def sanitize_identifier(name: str, index: int) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", name or "")
    if not value:
        value = f"arg{index + 1}"
    if value[0].isdigit():
        value = "p_" + value
    if value.upper() in UXB_KEYWORDS:
        value = "p_" + value
    if not value.startswith("p_"):
        value = "p_" + value
    return value


def clean_type(text: str) -> str:
    text = text or ""
    text = re.sub(r"\b(__cdecl|__stdcall|__fastcall|__thiscall)\b", " ", text)
    text = re.sub(r"__attribute__\s*\(\(.*?\)\)", " ", text)
    text = re.sub(r"\b(_Nonnull|_Nullable|_Null_unspecified)\b", " ", text)
    text = re.sub(r"\b(__restrict|restrict)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_define(item: str) -> str:
    if "=" in item:
        name, value = item.split("=", 1)
        return f"#define {name.strip()} {value.strip()}"
    return f"#define {item}"


def is_const_char_pointer(original: str, canonical: str) -> bool:
    text = f"{original} {canonical}".lower()
    if "*" not in text:
        return False
    if re.search(r"\b(const\s+)?(signed\s+)?char\s*\*", text):
        # char ** is an out pointer, not a direct string.
        stars = max(original.count("*"), canonical.count("*"))
        return stars == 1 and "const" in text
    return False


def is_wchar_pointer(original: str, canonical: str) -> bool:
    text = f"{original} {canonical}".lower()
    if "*" not in text:
        return False
    return ("wchar_t" in text or "wchar" in text) and max(
        original.count("*"), canonical.count("*")
    ) == 1


def map_c_type(original: str, canonical: str, *, is_return: bool) -> CType:
    original = clean_type(original)
    canonical = clean_type(canonical or original)
    low = canonical.lower()
    original_low = original.lower()

    # Function pointers and every ordinary pointer are passed as raw PTR,
    # except a single const char* / wchar_t* string surface.
    if "(*" in low or re.search(r"\(\s*\*\s*\)", low):
        return CType(original, canonical, "U64", "PTR", "ArgPtr", "ResultPtr",
                     True, False, False, True)

    pointer = "*" in low or "[" in low or "*" in original_low or "[" in original_low
    if pointer:
        if is_const_char_pointer(original, canonical):
            return CType(original, canonical, "STRING", "STRPTR", "ArgString",
                         "ResultString", True, True, False, True)
        if is_wchar_pointer(original, canonical) and "const" in f"{original_low} {low}":
            if is_return:
                # Returned wide strings stay raw because uXBasic string encoding
                # conversion must not assume ownership or lifetime.
                return CType(original, canonical, "U64", "PTR", "ArgPtr",
                             "ResultPtr", True, False, True, True)
            return CType(original, canonical, "STRING", "WSTRPTR", "ArgWString",
                         "ResultPtr", True, False, True, True)
        return CType(original, canonical, "U64", "PTR", "ArgPtr", "ResultPtr",
                     True, False, False, True)

    if re.match(r"^(struct|union)\s+", low):
        return CType(
            original, canonical, "U64", "PTR", "ArgPtr", "ResultPtr",
            False, False, False, True,
            "aggregate value is adapted through a generated C shim",
            indirect=True,
            aggregate=True,
        )

    # Strip qualifiers and common tags.
    scalar = re.sub(r"\b(const|volatile|signed)\b", " ", low)
    scalar = re.sub(r"\b(enum|struct|union)\s+", "", scalar)
    scalar = re.sub(r"\s+", " ", scalar).strip()

    if scalar == "void":
        return CType(original, canonical, "VOID", "VOID", "", "", False, False, False, True)
    if scalar in {"_bool", "bool"}:
        return CType(original, canonical, "I32", "U8", "ArgU8", "ResultI32",
                     False, False, False, True)
    if scalar in {"char", "signed char", "int8_t", "__int8"}:
        return CType(original, canonical, "I8", "I8", "ArgI8", "ResultI32",
                     False, False, False, True)
    if scalar in {"unsigned char", "uint8_t", "u_int8_t", "byte", "__uint8"}:
        return CType(original, canonical, "U8", "U8", "ArgU8", "ResultU32",
                     False, False, False, True)
    if scalar in {"short", "short int", "int16_t", "__int16"}:
        return CType(original, canonical, "I16", "I16", "ArgI16", "ResultI32",
                     False, False, False, True)
    if scalar in {"unsigned short", "unsigned short int", "uint16_t", "__uint16"}:
        return CType(original, canonical, "U16", "U16", "ArgU16", "ResultU32",
                     False, False, False, True)
    if scalar in {
        "int", "long", "long int", "int32_t", "__int32", "ssize_t",
        "intptr_t", "ptrdiff_t"
    }:
        # Target is x86_64-w64-windows-gnu: C long remains 32 bit.
        if scalar in {"ssize_t", "intptr_t", "ptrdiff_t"} and any(
            token in original_low for token in ("ssize_t", "intptr_t", "ptrdiff_t")
        ):
            return CType(original, canonical, "I64", "I64", "ArgI64", "ResultI64",
                         False, False, False, True)
        return CType(original, canonical, "I32", "I32", "ArgI32", "ResultI32",
                     False, False, False, True)
    if scalar in {
        "unsigned", "unsigned int", "unsigned long", "unsigned long int",
        "uint32_t", "__uint32", "dword"
    }:
        if "size_t" in original_low or "uintptr_t" in original_low:
            return CType(original, canonical, "U64", "U64", "ArgU64", "ResultU64",
                         False, False, False, True)
        return CType(original, canonical, "U32", "U32", "ArgU32", "ResultU32",
                     False, False, False, True)
    if scalar in {
        "long long", "long long int", "int64_t", "__int64",
        "signed long long", "signed long long int"
    }:
        return CType(original, canonical, "I64", "I64", "ArgI64", "ResultI64",
                     False, False, False, True)
    if scalar in {
        "unsigned long long", "unsigned long long int", "uint64_t", "__uint64",
        "size_t", "uintptr_t"
    }:
        return CType(original, canonical, "U64", "U64", "ArgU64", "ResultU64",
                     False, False, False, True)
    if scalar == "float":
        return CType(original, canonical, "F32", "F32", "ArgF32", "ResultF64",
                     False, False, False, True)
    if scalar == "double":
        return CType(original, canonical, "F64", "F64", "ArgF64", "ResultF64",
                     False, False, False, True)
    if scalar == "long double":
        return CType(
            original, canonical, "U64", "PTR", "ArgPtr", "ResultPtr",
            False, False, False, True,
            "long double value is adapted by address through a generated C shim",
            indirect=True,
            aggregate=False,
        )

    # Named enum typedefs often remain as their typedef spelling in AST.
    if low.startswith("enum ") or original_low.startswith("enum "):
        return CType(original, canonical, "I32", "I32", "ArgI32", "ResultI32",
                     False, False, False, True)

    # Most C API typedef scalars ultimately appear with a desugared type. If
    # they do not, keep the build fail-closed instead of guessing ABI width.
    return CType(
        original, canonical, "U64", "U64", "ArgU64", "ResultU64",
        False, False, False, False,
        f"unmapped C scalar type: original={original!r} canonical={canonical!r}",
    )


def extract_return_type(function_type: str) -> str:
    function_type = clean_type(function_type)
    marker = function_type.find(" (")
    if marker >= 0:
        return function_type[:marker].strip()
    # Fallback for forms such as `const char *(void)`.
    depth = 0
    for index, char in enumerate(function_type):
        if char == "(" and depth == 0:
            return function_type[:index].strip()
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
    return function_type


def parse_exports(objdump: str, dll: Path) -> set[str]:
    if not dll.is_file():
        return set()
    result = run([objdump, "-p", str(dll)])
    exports: set[str] = set()
    in_name_table = False
    found_name = False

    for raw in result.stdout.splitlines():
        if "[Ordinal/Name Pointer] Table" in raw:
            in_name_table = True
            found_name = False
            continue
        if not in_name_table:
            continue

        line = raw.rstrip()
        if found_name and (
            line.startswith("The Function Table")
            or line.startswith("The .pdata")
            or line.startswith("Dump of")
        ):
            break

        match = re.search(
            r"\[\s*\d+\]\s+\+base\[\s*\d+\]\s+"
            r"[0-9A-Fa-f]+\s+([^\s]+)\s*$",
            line,
        )
        if not match:
            match = re.match(
                r"^\s*\[\s*\d+\]\s+([A-Za-z_?@$][^\s]*)\s*$",
                line,
            )
        if match:
            name = match.group(1).strip()
            if name:
                exports.add(name)
                found_name = True

    return exports


def enum_value(node: dict[str, Any]) -> str | None:
    for child in node.get("inner", []):
        if child.get("kind") == "ConstantExpr" and "value" in child:
            return str(child["value"])
        if "value" in child:
            return str(child["value"])
    return None


def parse_simple_macros(text: str, patterns: list[str]) -> tuple[dict[str, str], int]:
    values: dict[str, str] = {}
    skipped = 0
    for raw in text.splitlines():
        if not raw.startswith("#define "):
            continue
        rest = raw[len("#define "):].strip()
        if not rest:
            continue
        first, _, value = rest.partition(" ")
        if "(" in first:
            # Function-like macro, not a DLL function.
            skipped += 1
            continue
        name = first.strip()
        value = value.strip()
        if not matches_any(name, patterns) or not value:
            continue

        if re.fullmatch(r'"(?:\\.|[^"\\])*"', value):
            values[name] = value
            continue

        # Only literal integers are emitted as uXBasic CONST. Complex C
        # expressions remain in the report; they are not silently mistranslated.
        stripped = value
        while stripped.startswith("(") and stripped.endswith(")"):
            stripped = stripped[1:-1].strip()
        numeric = re.fullmatch(
            r"([-+]?(?:0[xX][0-9A-Fa-f]+|[0-9]+))(?:[uUlL]+)?",
            stripped,
        )
        if numeric:
            token = numeric.group(1)
            try:
                number = int(token, 0)
                values[name] = str(number)
            except ValueError:
                skipped += 1
        else:
            skipped += 1
    return values, skipped


def clang_ast(
    clang: str,
    include_root: Path,
    headers: list[str],
    defines: list[str],
    extra_args: list[str],
    work: Path,
    target: str,
) -> tuple[dict[str, Any], str]:
    source = work / "uxb_binding_scan.c"
    lines = [format_define(item) for item in defines]
    lines += [f"#include <{header}>" for header in headers]
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")

    common = [
        clang,
        *([] if target == "host" else ["-target", target]),
        "-x", "c",
        "-std=c11",
        "-fsyntax-only",
        f"-I{include_root}",
        *extra_args,
        str(source),
    ]
    ast_command = common[:-1] + ["-Xclang", "-ast-dump=json", common[-1]]
    ast = json.loads(run(ast_command).stdout)

    macro_source = work / "uxb_macro_scan.c"
    macro_source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    macro_command = [
        clang,
        *([] if target == "host" else ["-target", target]),
        "-x", "c",
        "-std=c11",
        f"-I{include_root}",
        *extra_args,
        "-dM", "-E",
        str(macro_source),
    ]
    macros = run(macro_command).stdout
    return ast, macros


def build_typedef_map(ast: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in walk(ast):
        if node.get("kind") != "TypedefDecl":
            continue
        name = clean_type(node.get("name", ""))
        info = node.get("type", {})
        underlying = clean_type(
            info.get("qualType", "") or info.get("desugaredQualType", "")
        )
        if name and underlying and underlying != name:
            result[name] = underlying
    return result


def resolve_typedef(text: str, typedefs: dict[str, str]) -> str:
    current = clean_type(text)
    seen: set[str] = set()
    while current in typedefs and current not in seen:
        seen.add(current)
        current = clean_type(typedefs[current])
    return current


def safe_type_name(c_type: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", clean_type(c_type))
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "anonymous_type"


def find_owned_record_id(node: dict[str, Any]) -> str | None:
    owned = node.get("ownedTagDecl")
    if isinstance(owned, dict) and owned.get("kind") == "RecordDecl":
        return owned.get("id")
    for child in node.get("inner", []):
        if isinstance(child, dict):
            found = find_owned_record_id(child)
            if found:
                return found
    return None


def build_record_map(
    ast: dict[str, Any],
    typedefs: dict[str, str],
) -> dict[str, RecordInfo]:
    nodes_by_id = {
        node.get("id"): node
        for node in walk(ast)
        if node.get("id")
    }
    result: dict[str, RecordInfo] = {}

    def make_info(c_type: str, record: dict[str, Any]) -> RecordInfo:
        fields: list[RecordField] = []
        for child in record.get("inner", []):
            if child.get("kind") != "FieldDecl":
                continue
            field_type = child.get("type", {})
            original = clean_type(field_type.get("qualType", ""))
            canonical = clean_type(field_type.get("desugaredQualType", ""))
            if not canonical:
                canonical = resolve_typedef(original, typedefs)
            fields.append(
                RecordField(
                    name=child.get("name", ""),
                    c_type=original,
                    canonical_type=canonical,
                    mapped=map_c_type(original, canonical, is_return=False),
                )
            )
        return RecordInfo(
            c_type=c_type,
            safe_name=safe_type_name(c_type),
            fields=fields,
        )

    for node in walk(ast):
        if node.get("kind") == "TypedefDecl":
            alias = clean_type(node.get("name", ""))
            record_id = find_owned_record_id(node)
            record = nodes_by_id.get(record_id or "")
            if alias and record and record.get("completeDefinition"):
                info = make_info(alias, record)
                result[alias] = info
                result[resolve_typedef(alias, typedefs)] = info

    for node in walk(ast):
        if (
            node.get("kind") == "RecordDecl"
            and node.get("completeDefinition")
            and node.get("name")
        ):
            c_type = f"{node.get('tagUsed', 'struct')} {node['name']}"
            result.setdefault(c_type, make_info(c_type, node))

    return result


def lookup_record(
    original: str,
    canonical: str,
    records: dict[str, RecordInfo],
) -> RecordInfo | None:
    return records.get(clean_type(original)) or records.get(clean_type(canonical))


def function_from_node(
    node: dict[str, Any],
    exports: set[str],
    dll_name: str,
    module_name: str,
    typedefs: dict[str, str],
) -> Function:
    name = node.get("name", "")
    ftype = node.get("type", {})
    return_original = extract_return_type(ftype.get("qualType", ""))
    return_canonical = extract_return_type(
        ftype.get("desugaredQualType", "")
    )
    if not return_canonical:
        return_canonical = resolve_typedef(return_original, typedefs)
    mapped_return = map_c_type(
        return_original, return_canonical, is_return=True
    )

    parameters: list[Parameter] = []
    supported = mapped_return.supported
    reasons: list[str] = []
    if not mapped_return.supported:
        reasons.append(mapped_return.reason)

    for index, child in enumerate(node.get("inner", [])):
        if child.get("kind") != "ParmVarDecl":
            continue
        ctype = child.get("type", {})
        original = clean_type(ctype.get("qualType", ""))
        canonical = clean_type(ctype.get("desugaredQualType", ""))
        if not canonical:
            canonical = resolve_typedef(original, typedefs)
        mapped = map_c_type(original, canonical, is_return=False)
        param = Parameter(
            name=sanitize_identifier(child.get("name", ""), index),
            c_type=original,
            canonical_type=canonical,
            mapped=mapped,
        )
        parameters.append(param)
        if not mapped.supported:
            supported = False
            reasons.append(f"{param.name}: {mapped.reason}")

    inline = bool(node.get("inline")) or node.get("storageClass") == "static"
    variadic = bool(node.get("variadic"))
    requires_shim = (
        inline
        or mapped_return.indirect
        or any(param.mapped.indirect for param in parameters)
    )
    exported = name in exports if exports else not inline

    if exports and not inline and not exported:
        supported = False
        reasons.append("function declaration has no matching DLL export")

    if variadic and requires_shim:
        supported = False
        reasons.append(
            "variadic function also requires aggregate/long-double adaptation"
        )

    if requires_shim:
        symbol = f"uxb_shim_{name}"
        call_dll = f"{module_name}_uxshim.dll"
    else:
        symbol = name
        call_dll = dll_name

    return Function(
        name=name,
        return_type=return_original,
        return_canonical=return_canonical,
        return_mapped=mapped_return,
        parameters=parameters,
        variadic=variadic,
        inline=inline,
        storage=node.get("storageClass", ""),
        exported=exported,
        symbol=symbol,
        dll_name=call_dll,
        source=str(node.get("loc", {}).get("file", "")),
        supported=supported,
        reason="; ".join(dict.fromkeys(reasons)),
        requires_shim=requires_shim,
        indirect_return=mapped_return.indirect,
    )


def default_value(mapped: CType) -> str:
    if mapped.uxb_type == "STRING":
        return '""'
    if mapped.uxb_type in {"F32", "F64"}:
        return "0.0"
    return "0"


def emit_failure(lines: list[str], function: Function, indent: str = "    ") -> None:
    if function.return_mapped.kind_name == "VOID":
        lines.append(indent + "uxcapi.CallFree(uxc_call)")
        lines.append(indent + "EXIT SUB")
    else:
        lines.append(indent + "uxcapi.CallFree(uxc_call)")
        lines.append(indent + f"RETURN {default_value(function.return_mapped)}")


def emit_indirect_return_function(function: Function) -> str:
    params = [
        f"{param.name} AS {param.mapped.uxb_type}"
        for param in function.parameters
    ]
    signature = ", ".join(params)
    safe = safe_type_name(function.return_type)
    lines = [
        f"FUNCTION {function.name}({signature}) AS U64",
        "    DIM uxc_out AS U64",
        "    DIM uxc_call AS U64",
        "    DIM uxc_ok AS I32",
        f"    uxc_out = uxcapi.MemoryCalloc(1, UXBSizeOf_{safe}())",
        "    IF uxc_out = 0 THEN RETURN 0",
        (
            "    uxc_call = uxcapi.CallNew("
            f'"{function.dll_name}", "{function.symbol}", '
            f"uxcapi.KIND_I32, 0, {len(function.parameters) + 1})"
        ),
        "    IF uxc_call = 0 THEN",
        "        uxcapi.MemoryFree(uxc_out)",
        "        RETURN 0",
        "    END IF",
        "    IF uxcapi.ArgPtr(uxc_call, uxc_out) = 0 THEN",
        "        uxcapi.CallFree(uxc_call)",
        "        uxcapi.MemoryFree(uxc_out)",
        "        RETURN 0",
        "    END IF",
    ]
    for param in function.parameters:
        lines += [
            f"    IF uxcapi.{param.mapped.arg_method}(uxc_call, {param.name}) = 0 THEN",
            "        uxcapi.CallFree(uxc_call)",
            "        uxcapi.MemoryFree(uxc_out)",
            "        RETURN 0",
            "    END IF",
        ]
    lines += [
        "    IF uxcapi.Invoke(uxc_call) = 0 THEN",
        "        uxcapi.CallFree(uxc_call)",
        "        uxcapi.MemoryFree(uxc_out)",
        "        RETURN 0",
        "    END IF",
        "    uxc_ok = uxcapi.ResultI32(uxc_call)",
        "    uxcapi.CallFree(uxc_call)",
        "    IF uxc_ok = 0 THEN",
        "        uxcapi.MemoryFree(uxc_out)",
        "        RETURN 0",
        "    END IF",
        "    RETURN uxc_out",
        "END FUNCTION",
    ]
    return "\n".join(lines)


def emit_function(function: Function) -> str:
    if function.indirect_return:
        return emit_indirect_return_function(function)

    ret = function.return_mapped
    params = [
        f"{param.name} AS {param.mapped.uxb_type}"
        for param in function.parameters
    ]
    if function.variadic:
        params.append("varArgs AS U64")
    signature = ", ".join(params)
    lines: list[str] = []

    if ret.kind_name == "VOID":
        lines.append(f"SUB {function.name}({signature})")
    else:
        lines.append(f"FUNCTION {function.name}({signature}) AS {ret.uxb_type}")

    lines.append("    DIM uxc_call AS U64")
    if ret.kind_name != "VOID":
        lines.append(f"    DIM uxc_result AS {ret.uxb_type}")
    lines.append(
        "    uxc_call = uxcapi.CallNew("
        + f'"{function.dll_name}", "{function.symbol}", '
        + f"uxcapi.KIND_{ret.kind_name}, {1 if function.variadic else 0}, "
        + f"{len(function.parameters)})"
    )
    lines.append("    IF uxc_call = 0 THEN")
    if ret.kind_name == "VOID":
        lines.append("        EXIT SUB")
    else:
        lines.append(f"        RETURN {default_value(ret)}")
    lines.append("    END IF")

    for param in function.parameters:
        lines.append(
            f"    IF uxcapi.{param.mapped.arg_method}(uxc_call, {param.name}) = 0 THEN"
        )
        emit_failure(lines, function, "        ")
        lines.append("    END IF")

    if function.variadic:
        lines.append("    IF varArgs <> 0 THEN")
        lines.append("        IF uxcapi.CallAppendArgs(uxc_call, varArgs) = 0 THEN")
        emit_failure(lines, function, "            ")
        lines.append("        END IF")
        lines.append("    END IF")

    lines.append("    IF uxcapi.Invoke(uxc_call) = 0 THEN")
    emit_failure(lines, function, "        ")
    lines.append("    END IF")

    if ret.kind_name == "VOID":
        lines.append("    uxcapi.CallFree(uxc_call)")
        lines.append("END SUB")
    else:
        lines.append(f"    uxc_result = uxcapi.{ret.result_method}(uxc_call)")
        lines.append("    uxcapi.CallFree(uxc_call)")
        lines.append("    RETURN uxc_result")
        lines.append("END FUNCTION")
    return "\n".join(lines)


def c_parameter_declaration(c_type: str, name: str) -> str:
    if "(*)" in c_type:
        return c_type.replace("(*)", f"(*{name})")
    return f"{c_type} {name}"


def c_shim_parameter(param: Parameter, name: str) -> tuple[str, str]:
    if param.mapped.indirect:
        return f"const void *{name}", f"*(const {param.c_type} *){name}"
    return c_parameter_declaration(param.c_type, name), name


def indirect_types(
    functions: list[Function],
    records: dict[str, RecordInfo],
) -> dict[str, RecordInfo | None]:
    result: dict[str, RecordInfo | None] = {}
    for fn in functions:
        if not fn.supported:
            continue
        if fn.return_mapped.indirect:
            result.setdefault(
                fn.return_type,
                lookup_record(fn.return_type, fn.return_canonical, records),
            )
        for param in fn.parameters:
            if param.mapped.indirect:
                result.setdefault(
                    param.c_type,
                    lookup_record(param.c_type, param.canonical_type, records),
                )
    return result


def emit_inline_shim(
    manifest: dict[str, Any],
    functions: list[Function],
    headers: list[str],
    defines: list[str],
    records: dict[str, RecordInfo],
) -> str:
    shim_functions = [
        fn for fn in functions if fn.requires_shim and fn.supported
    ]
    used_types = indirect_types(functions, records)
    lines = [
        "#include <stdint.h>",
        "#include <stddef.h>",
        "#if defined(_WIN32)",
        "#define UXB_SHIM_API __declspec(dllexport)",
        "#define UXB_SHIM_CALL __cdecl",
        "#else",
        "#define UXB_SHIM_API __attribute__((visibility(\"default\")))",
        "#define UXB_SHIM_CALL",
        "#endif",
    ]
    for define in defines:
        lines.append(format_define(define))
    for header in headers:
        lines.append(f"#include <{header}>")
    lines.append("")

    for c_type, record in sorted(
        used_types.items(), key=lambda item: safe_type_name(item[0])
    ):
        safe = safe_type_name(c_type)
        lines.append(
            f"UXB_SHIM_API uint64_t UXB_SHIM_CALL "
            f"uxb_sizeof_{safe}(void) {{"
        )
        lines.append(f"    return (uint64_t)sizeof({c_type});")
        lines.append("}")
        if record:
            for field in record.fields:
                if not field.name:
                    continue
                field_safe = safe_type_name(field.name)
                lines.append(
                    f"UXB_SHIM_API uint64_t UXB_SHIM_CALL "
                    f"uxb_offsetof_{safe}_{field_safe}(void) {{"
                )
                lines.append(
                    f"    return (uint64_t)offsetof({c_type}, {field.name});"
                )
                lines.append("}")
        lines.append("")

    for fn in shim_functions:
        declarations: list[str] = []
        call_names: list[str] = []
        if fn.indirect_return:
            declarations.append("void *uxb_out_result")
        for index, param in enumerate(fn.parameters):
            declaration, call_name = c_shim_parameter(param, f"p{index}")
            declarations.append(declaration)
            call_names.append(call_name)
        params = ", ".join(declarations) if declarations else "void"
        call_args = ", ".join(call_names)

        if fn.indirect_return:
            lines.append(
                f"UXB_SHIM_API int32_t UXB_SHIM_CALL "
                f"{fn.symbol}({params}) {{"
            )
            lines.append("    if (!uxb_out_result) return 0;")
            lines.append(
                f"    *({fn.return_type} *)uxb_out_result = "
                f"{fn.name}({call_args});"
            )
            lines.append("    return 1;")
        else:
            lines.append(
                f"UXB_SHIM_API {fn.return_type} UXB_SHIM_CALL "
                f"{fn.symbol}({params}) {{"
            )
            if fn.return_mapped.kind_name == "VOID":
                lines.append(f"    {fn.name}({call_args});")
            else:
                lines.append(f"    return {fn.name}({call_args});")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def emit_u64_zero_arg_call(
    public_name: str,
    dll_name: str,
    symbol: str,
) -> str:
    return "\n".join([
        f"FUNCTION {public_name}() AS U64",
        "    DIM uxc_call AS U64",
        "    DIM uxc_result AS U64",
        (
            "    uxc_call = uxcapi.CallNew("
            f'"{dll_name}", "{symbol}", uxcapi.KIND_U64, 0, 0)'
        ),
        "    IF uxc_call = 0 THEN RETURN 0",
        "    IF uxcapi.Invoke(uxc_call) = 0 THEN",
        "        uxcapi.CallFree(uxc_call)",
        "        RETURN 0",
        "    END IF",
        "    uxc_result = uxcapi.ResultU64(uxc_call)",
        "    uxcapi.CallFree(uxc_call)",
        "    RETURN uxc_result",
        "END FUNCTION",
    ])


def field_memory_methods(mapped: CType) -> tuple[str, str, str] | None:
    table = {
        "I8": ("MemoryReadI8", "MemoryWriteI8", "I32"),
        "U8": ("MemoryReadU8", "MemoryWriteU8", "U32"),
        "I16": ("MemoryReadI16", "MemoryWriteI16", "I32"),
        "U16": ("MemoryReadU16", "MemoryWriteU16", "U32"),
        "I32": ("MemoryReadI32", "MemoryWriteI32", "I32"),
        "U32": ("MemoryReadU32", "MemoryWriteU32", "U32"),
        "I64": ("MemoryReadI64", "MemoryWriteI64", "I64"),
        "U64": ("MemoryReadU64", "MemoryWriteU64", "U64"),
        "F32": ("MemoryReadF32", "MemoryWriteF32", "F64"),
        "F64": ("MemoryReadF64", "MemoryWriteF64", "F64"),
        "PTR": ("MemoryReadPtr", "MemoryWritePtr", "U64"),
        "STRPTR": ("MemoryReadPtr", "MemoryWritePtr", "U64"),
        "WSTRPTR": ("MemoryReadPtr", "MemoryWritePtr", "U64"),
    }
    return table.get(mapped.kind_name)


def emit_type_helpers(
    functions: list[Function],
    records: dict[str, RecordInfo],
    shim_dll: str,
) -> list[str]:
    lines: list[str] = []
    for c_type, record in sorted(
        indirect_types(functions, records).items(),
        key=lambda item: safe_type_name(item[0]),
    ):
        safe = safe_type_name(c_type)
        size_name = f"UXBSizeOf_{safe}"
        lines.append(
            emit_u64_zero_arg_call(
                size_name, shim_dll, f"uxb_sizeof_{safe}"
            )
        )
        lines.append("")
        lines += [
            f"FUNCTION UXBAlloc_{safe}() AS U64",
            f"    RETURN uxcapi.MemoryCalloc(1, {size_name}())",
            "END FUNCTION",
            "",
        ]
        if record:
            for field in record.fields:
                if not field.name:
                    continue
                field_safe = safe_type_name(field.name)
                offset_name = f"UXBOffsetOf_{safe}_{field_safe}"
                lines.append(
                    emit_u64_zero_arg_call(
                        offset_name,
                        shim_dll,
                        f"uxb_offsetof_{safe}_{field_safe}",
                    )
                )
                lines.append("")
                if "[" in field.c_type or field.mapped.indirect:
                    continue
                methods = field_memory_methods(field.mapped)
                if not methods:
                    continue
                read_method, write_method, uxb_type = methods
                lines += [
                    f"FUNCTION UXBGet_{safe}_{field_safe}(p_struct AS U64) AS {uxb_type}",
                    (
                        f"    RETURN uxcapi.{read_method}("
                        f"p_struct, {offset_name}())"
                    ),
                    "END FUNCTION",
                    "",
                    (
                        f"FUNCTION UXBSet_{safe}_{field_safe}("
                        f"p_struct AS U64, value AS {uxb_type}) AS I32"
                    ),
                    (
                        f"    RETURN uxcapi.{write_method}("
                        f"p_struct, {offset_name}(), value)"
                    ),
                    "END FUNCTION",
                    "",
                ]
    if lines:
        lines += [
            "SUB UXBStructFree(p_struct AS U64)",
            "    uxcapi.MemoryFree(p_struct)",
            "END SUB",
            "",
        ]
    return lines


def emit_module(
    manifest: dict[str, Any],
    functions: list[Function],
    constants: dict[str, str],
    dll_name: str,
    records: dict[str, RecordInfo],
) -> str:
    namespace = manifest["namespace"]
    shim_dll = f"{manifest['name']}_uxshim.dll"
    lines = [
        f"' Generated complete raw C API for {manifest['name']}.",
        "' Do not edit manually; regenerate from installed public headers.",
        'INCLUDE "include/modules/uxcapi.uxmh"',
        "",
        f"NAMESPACE {namespace}",
        "",
        f'CONST UXB_VENDOR_DLL = "{dll_name}"',
        f'CONST UXB_SHIM_DLL = "{shim_dll}"',
        "",
        "FUNCTION UXBLastError() AS STRING",
        "    RETURN uxcapi.LastError()",
        "END FUNCTION",
        "",
    ]
    for name, value in sorted(constants.items()):
        lines.append(f"CONST {name} = {value}")
    if constants:
        lines.append("")

    lines += emit_type_helpers(functions, records, shim_dll)

    for fn in sorted(
        (f for f in functions if f.supported),
        key=lambda x: x.name.lower(),
    ):
        lines.append(emit_function(fn))
        lines.append("")
    lines.append(f"END NAMESPACE")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--clang", required=True)
    parser.add_argument("--objdump", required=True)
    parser.add_argument("--include-root", required=True)
    parser.add_argument("--dll", required=True)
    parser.add_argument("--profile", choices=["stable", "experimental"], default="stable")
    parser.add_argument("--target", default="x86_64-w64-windows-gnu")
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--allow-no-exports", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    include_root = Path(args.include_root).resolve()
    dll = Path(args.dll).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    defines = list(manifest.get("defines", []))
    if args.profile == "experimental":
        defines += list(manifest.get("experimental_defines", []))
    extra_args = list(manifest.get("clang_args", []))

    with tempfile.TemporaryDirectory(prefix="uxb_c_bindgen_") as temp:
        ast, macro_text = clang_ast(
            args.clang,
            include_root,
            manifest["headers"],
            defines,
            extra_args,
            Path(temp),
            args.target,
        )

    exports = parse_exports(args.objdump, dll)
    if not exports and not args.allow_no_exports:
        raise SystemExit(f"No PE exports parsed from {dll}")

    typedefs = build_typedef_map(ast)
    records = build_record_map(ast, typedefs)

    functions: list[Function] = []
    seen: set[str] = set()
    function_patterns = manifest.get("function_patterns", [])
    excludes = manifest.get("exclude_function_patterns", [])
    for node in walk(ast):
        if node.get("kind") != "FunctionDecl":
            continue
        name = node.get("name", "")
        if not name or name in seen:
            continue
        if not matches_any(name, function_patterns):
            continue
        if excludes and matches_any(name, excludes):
            continue
        if node.get("isImplicit"):
            continue
        function = function_from_node(
            node,
            exports,
            dll.name,
            manifest["name"],
            typedefs,
        )
        functions.append(function)
        seen.add(name)

    constants: dict[str, str] = {}
    for node in walk(ast):
        if node.get("kind") != "EnumConstantDecl":
            continue
        name = node.get("name", "")
        if not name or not matches_any(
            name, manifest.get("constant_patterns", [])
        ):
            continue
        value = enum_value(node)
        if value is not None:
            constants[name] = value

    macro_constants, skipped_macros = parse_simple_macros(
        macro_text, manifest.get("constant_patterns", [])
    )
    for name, value in macro_constants.items():
        constants.setdefault(name, value)

    module_text = emit_module(
        manifest, functions, constants, dll.name, records
    )
    module_path = root / "libsx" / manifest["name"] / f"{manifest['name']}.bas"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(module_text, encoding="utf-8")

    include_path = root / "include" / "modules" / f"{manifest['name']}.uxmh"
    include_path.parent.mkdir(parents=True, exist_ok=True)
    include_lines = [
        f'INCLUDE "libsx/{manifest["name"]}/{manifest["name"]}.bas"',
    ]
    easy_path = (
        root / "libsx" / manifest["name"]
        / f"{manifest['name']}_easy.bas"
    )
    if easy_path.exists():
        include_lines.append(
            f'INCLUDE "libsx/{manifest["name"]}/{manifest["name"]}_easy.bas"'
        )
    include_path.write_text("\n".join(include_lines) + "\n", encoding="utf-8")

    shim_text = emit_inline_shim(
        manifest, functions, manifest["headers"], defines, records
    )
    shim_path = (
        root / "runtime_ext" / "c_full_generated"
        / manifest["name"] / f"{manifest['name']}_uxshim.c"
    )
    shim_path.parent.mkdir(parents=True, exist_ok=True)
    shim_path.write_text(shim_text, encoding="utf-8")

    unsupported = [fn for fn in functions if not fn.supported]
    inline_count = sum(1 for fn in functions if fn.inline and fn.supported)
    shim_count = sum(
        1 for fn in functions if fn.requires_shim and fn.supported
    )
    aggregate_return_count = sum(
        1 for fn in functions
        if fn.indirect_return and fn.return_mapped.aggregate and fn.supported
    )
    indirect_parameter_count = sum(
        1 for fn in functions for param in fn.parameters
        if param.mapped.indirect and fn.supported
    )
    variadic_count = sum(1 for fn in functions if fn.variadic and fn.supported)
    exported_count = sum(1 for fn in functions if fn.exported and not fn.inline)
    report = {
        "schema": "uxb.c.full_api.surface.v1",
        "module": manifest["name"],
        "namespace": manifest["namespace"],
        "engine": manifest.get("engine", ""),
        "license": manifest.get("license", ""),
        "homepage": manifest.get("homepage", ""),
        "profile": args.profile,
        "vendor_dll": dll.name,
        "header_function_count": len(functions),
        "generated_function_count": len(functions) - len(unsupported),
        "exported_function_count": exported_count,
        "inline_shim_count": shim_count,
        "header_inline_function_count": inline_count,
        "aggregate_return_adapter_count": aggregate_return_count,
        "indirect_parameter_adapter_count": indirect_parameter_count,
        "variadic_function_count": variadic_count,
        "constant_count": len(constants),
        "skipped_function_like_or_complex_macro_count": skipped_macros,
        "unbound_function_count": len(unsupported),
        "unbound_functions": [
            {
                "name": fn.name,
                "reason": fn.reason,
                "return_type": fn.return_type,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.c_type,
                        "canonical": p.canonical_type,
                    }
                    for p in fn.parameters
                ],
            }
            for fn in unsupported
        ],
        "functions": [asdict(fn) for fn in functions],
    }
    report_path = report_dir / f"{manifest['name']}_surface.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"{manifest['name']}: headers={len(functions)} "
        f"generated={len(functions)-len(unsupported)} "
        f"shims={shim_count} variadic={variadic_count} "
        f"unbound={len(unsupported)}"
    )
    return 0 if not unsupported else 3


if __name__ == "__main__":
    raise SystemExit(main())
