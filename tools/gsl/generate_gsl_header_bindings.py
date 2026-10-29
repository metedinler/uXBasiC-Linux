#!/usr/bin/env python3
"""Generate auditable UXGSL metadata and checked scalar wrappers from GSL headers.

This deliberately avoids pretending that every C declaration is equally safe.
It inventories every public GSL declaration, then generates wrappers only when
the header proves a scalar function has a matching ``*_e`` result API.  Those
wrappers preserve the UXGSL status contract instead of bypassing GSL errors.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_]*"
FUNCTION_RE = re.compile(
    rf"^(?P<return>.*?)\b(?P<name>gsl_[A-Za-z0-9_]+)\s*\((?P<args>.*)\)\s*$",
    re.DOTALL,
)
SIMPLE_TYPEDEF_RE = re.compile(
    rf"^typedef\s+(?!struct\b|union\b|enum\b)(?P<type>[^;{{}}()]+?)\s+(?P<name>{IDENT_RE})\s*$",
    re.DOTALL,
)
STRUCT_NAME_RE = re.compile(rf"\b(?:struct|union)\s+({IDENT_RE})\b")
ENUM_NAME_RE = re.compile(rf"\benum\s+({IDENT_RE})\b")


PRIMITIVE_TYPES = {
    "void": ("VOID", "VOID"),
    "char": ("I8", "I32"),
    "signed char": ("I8", "I32"),
    "unsigned char": ("U8", "U32"),
    "short": ("I16", "I32"),
    "short int": ("I16", "I32"),
    "unsigned short": ("U16", "U32"),
    "unsigned short int": ("U16", "U32"),
    "int": ("I32", "I32"),
    "signed": ("I32", "I32"),
    "signed int": ("I32", "I32"),
    "unsigned": ("U32", "U32"),
    "unsigned int": ("U32", "U32"),
    # Windows x64's MinGW/UCRT ABI keeps long at 32 bits.
    "long": ("I32", "I32"),
    "long int": ("I32", "I32"),
    "unsigned long": ("U32", "U32"),
    "unsigned long int": ("U32", "U32"),
    "long long": ("I64", "I64"),
    "long long int": ("I64", "I64"),
    "unsigned long long": ("U64", "U64"),
    "unsigned long long int": ("U64", "U64"),
    "size_t": ("U64", "U64"),
    "ptrdiff_t": ("I64", "I64"),
    "double": ("F64", "F64"),
    "float": ("F32", "F64"),
}


def squash(value: str) -> str:
    return " ".join(value.replace("\n", " ").replace("\t", " ").split())


def strip_source(text: str) -> str:
    text = COMMENT_RE.sub("", text)
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def top_level_statements(text: str) -> list[str]:
    statements: list[str] = []
    brace_depth = 0
    paren_depth = 0
    current: list[str] = []
    for char in text:
        current.append(char)
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
        elif char == ";" and brace_depth == 0 and paren_depth == 0:
            statements.append(squash("".join(current[:-1])))
            current.clear()
    return statements


def split_top_level(value: str) -> list[str]:
    rows: list[str] = []
    current: list[str] = []
    depth = 0
    for char in value:
        if char == "," and depth == 0:
            rows.append(squash("".join(current)))
            current.clear()
            continue
        current.append(char)
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
    tail = squash("".join(current))
    if tail:
        rows.append(tail)
    return rows


def normalize_type(value: str) -> str:
    value = squash(value)
    value = re.sub(r"\b(const|volatile|restrict|register|extern|static)\b", "", value)
    value = value.replace(" *", "*").replace("* ", "*")
    return squash(value)


def parse_argument(value: str) -> dict[str, str] | None:
    value = squash(value)
    if not value or value == "void" or value == "..." or "(*" in value or "[" in value:
        return None
    match = re.match(rf"^(?P<type>.+?)(?:\s+)(?P<name>{IDENT_RE})$", value)
    if not match:
        return None
    return {"name": match.group("name"), "type": normalize_type(match.group("type"))}


def canonical_type(value: str, aliases: dict[str, str]) -> str:
    value = normalize_type(value)
    if "*" in value:
        return value
    seen: set[str] = set()
    while value in aliases and value not in seen:
        seen.add(value)
        value = normalize_type(aliases[value])
    return value


def scalar_kind(value: str, aliases: dict[str, str]) -> tuple[str, str] | None:
    value = canonical_type(value, aliases)
    if "*" in value or value.startswith(("struct ", "union ", "enum ")):
        return None
    return PRIMITIVE_TYPES.get(value)


def basic_suffix(gsl_name: str) -> str:
    # gsl_sf_bessel_Jn -> SfBesselJn; preserves GSL's useful case distinctions.
    chunks = gsl_name.split("_")[1:]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


def basic_case_tag(gsl_name: str) -> str:
    """Encode C's case distinctions only when BASIC would collapse a name."""
    return "".join("Upper" + char if char.isupper() else char for char in gsl_name[4:])


def c_arguments(function: dict[str, object]) -> str:
    return ", ".join(f"{arg['canonical_type']} arg{index}" for index, arg in enumerate(function["args"]))


def c_call_arguments(function: dict[str, object]) -> str:
    return ", ".join(f"arg{index}" for index, _ in enumerate(function["args"]))


def basic_arguments(function: dict[str, object]) -> tuple[str, str]:
    decls: list[str] = []
    signature: list[str] = []
    for index, arg in enumerate(function["args"]):
        basic_type, abi_kind = arg["scalar"]
        decls.append(f"arg{index} AS {basic_type}")
        signature.append(abi_kind)
    return ", ".join(decls), ",".join(signature)


def parse_headers(header_dir: Path) -> tuple[dict[str, str], list[dict[str, object]], set[str], set[str]]:
    aliases: dict[str, str] = {}
    functions: list[dict[str, object]] = []
    structs: set[str] = set()
    enums: set[str] = set()
    for header in sorted(header_dir.glob("*.h")):
        source = strip_source(header.read_text(encoding="utf-8", errors="replace"))
        structs.update(STRUCT_NAME_RE.findall(source))
        enums.update(ENUM_NAME_RE.findall(source))
        for statement in top_level_statements(source):
            typedef = SIMPLE_TYPEDEF_RE.match(statement)
            if typedef:
                aliases[typedef.group("name")] = normalize_type(typedef.group("type"))
            match = FUNCTION_RE.match(statement)
            if not match or statement.startswith("typedef"):
                continue
            raw_args = split_top_level(match.group("args"))
            args: list[dict[str, str]] = []
            valid = True
            for raw_arg in raw_args:
                parsed = parse_argument(raw_arg)
                if parsed is None:
                    valid = False
                    break
                args.append(parsed)
            functions.append(
                {
                    "name": match.group("name"),
                    "return_type": normalize_type(match.group("return")),
                    "args": args,
                    "raw_args": raw_args,
                    "header": header.name,
                    "parseable_parameters": valid,
                }
            )
    for function in functions:
        function["canonical_return_type"] = canonical_type(function["return_type"], aliases)
        for argument in function["args"]:
            argument["canonical_type"] = canonical_type(argument["type"], aliases)
            argument["scalar"] = scalar_kind(argument["type"], aliases)
    return aliases, functions, structs, enums


def export_names(catalog: dict[str, object]) -> set[str]:
    return {name for module in catalog["modules"] for name in module["exports"] if name.startswith("gsl_")}


def checked_scalar_wrappers(functions: list[dict[str, object]], exports: set[str]) -> list[dict[str, object]]:
    by_name = {function["name"]: function for function in functions}
    wrappers: list[dict[str, object]] = []
    for function in functions:
        name = function["name"]
        if not name.startswith("gsl_sf_") or name.endswith("_e") or name not in exports:
            continue
        if function["canonical_return_type"] != "double" or not function["parseable_parameters"]:
            continue
        if any(argument["scalar"] is None for argument in function["args"]):
            continue
        checked = by_name.get(name + "_e")
        if checked is None or checked["name"] not in exports or not checked["parseable_parameters"]:
            continue
        if checked["canonical_return_type"] != "int" or len(checked["args"]) != len(function["args"]) + 1:
            continue
        if [arg["canonical_type"] for arg in checked["args"][:-1]] != [arg["canonical_type"] for arg in function["args"]]:
            continue
        last = checked["args"][-1]["canonical_type"].replace(" ", "")
        if last != "gsl_sf_result*":
            continue
        wrappers.append(
            {
                "gsl_name": name,
                "checked_gsl_name": checked["name"],
                "basic_name": basic_suffix(name),
                "c_symbol": "uxgsl_auto_" + name,
                "header": checked["header"],
                "args": function["args"],
                "wrapper_kind": "checked_scalar_adapter",
                "case_disambiguated": False,
            }
        )
    wrappers.sort(key=lambda row: row["gsl_name"])
    by_basic_name: dict[str, list[dict[str, object]]] = {}
    for wrapper in wrappers:
        by_basic_name.setdefault(wrapper["basic_name"].lower(), []).append(wrapper)
    for group in by_basic_name.values():
        if len(group) > 1:
            for wrapper in group:
                wrapper["basic_name"] += "_Gsl" + basic_case_tag(wrapper["gsl_name"])
                wrapper["case_disambiguated"] = True
    return wrappers


def emit_c_include(path: Path, wrappers: list[dict[str, object]]) -> None:
    headers = sorted({row["header"] for row in wrappers})
    lines = [
        "/* Generated by tools/gsl/generate_gsl_header_bindings.py; do not edit. */",
        "/* Checked GSL scalar adapters: result-valued APIs call their *_e peer. */",
        *[f"#include <gsl/{header}>" for header in headers],
        "",
    ]
    for row in wrappers:
        args = c_arguments(row)
        invoke = c_call_arguments(row)
        if invoke:
            invoke += ", "
        lines.extend(
            [
                f"UXGSL_API double {row['c_symbol']}({args}) {{",
                "    gsl_sf_result result;",
                "    uxgsl_initialize();",
                f"    uxgsl_set_gsl_status({row['checked_gsl_name']}({invoke}&result));",
                "    return uxgsl_last_status() == UXGSL_STATUS_OK ? result.val : NAN;",
                "}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def basic_function_lines(row: dict[str, object]) -> list[str]:
    args, signature = basic_arguments(row)
    call_args = ", ".join(f"arg{index}" for index, _ in enumerate(row["args"]))
    trailer = f', "{signature}"' if signature else ""
    if call_args:
        trailer += ", " + call_args
    return [
        f"FUNCTION {row['basic_name']}({args}) AS F64",
        f"    RETURN CALL(DLL, \"uxgsl.dll\", \"{row['c_symbol']}\", F64, CDECL{trailer})",
        "END FUNCTION",
        "",
    ]


def emit_basic_modules(module_dir: Path, module_header_dir: Path, wrappers: list[dict[str, object]]) -> None:
    groups: dict[str, list[dict[str, object]]] = {}
    for wrapper in wrappers:
        groups.setdefault(wrapper["header"], []).append(wrapper)
    module_dir.mkdir(parents=True, exist_ok=True)
    module_header_dir.mkdir(parents=True, exist_ok=True)
    for header, rows in sorted(groups.items()):
        stem = Path(header).stem
        lines = [
            "' Generated by tools/gsl/generate_gsl_header_bindings.py; do not edit.",
            f"' Checked scalar bindings from <gsl/{header}>.",
            "NAMESPACE uxgsl",
            "",
        ]
        for row in rows:
            lines.extend(basic_function_lines(row))
        lines.append("END NAMESPACE")
        (module_dir / f"{stem}.bas").write_text("\n".join(lines) + "\n", encoding="utf-8")
        header_lines = [
            "' Generated public forwarding header for one UXGSL special-function family.",
            'INCLUDE "include/modules/uxgsl.uxmh"',
            f'INCLUDE "libsx/uxgsl/generated/modules/{stem}.bas"',
            "",
        ]
        (module_header_dir / f"{stem}.uxmh").write_text("\n".join(header_lines), encoding="utf-8")


def emit_basic_include(path: Path, wrappers: list[dict[str, object]]) -> None:
    headers = sorted({row["header"] for row in wrappers})
    lines = [
        "' Generated UXGSL all-special-functions umbrella; explicit opt-in only.",
        "' Prefer a narrow include/modules/uxgsl_generated/<family>.uxmh header.",
        *[f'INCLUDE "libsx/uxgsl/generated/modules/{Path(header).stem}.bas"' for header in headers],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def emit_header_include(path: Path, wrappers: list[dict[str, object]]) -> None:
    lines = [
        "/* Generated by tools/gsl/generate_gsl_header_bindings.py; do not edit. */",
        "/* Public C declarations for source-generated checked scalar adapters. */",
        "",
    ]
    for row in wrappers:
        lines.append(f"UXGSL_API double {row['c_symbol']}({c_arguments(row)});")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate audited UXGSL bindings from installed public GSL headers")
    parser.add_argument("--headers", required=True, type=Path)
    parser.add_argument("--export-catalog", required=True, type=Path)
    parser.add_argument("--metadata-out", required=True, type=Path)
    parser.add_argument("--c-include-out", required=True, type=Path)
    parser.add_argument("--basic-include-out", required=True, type=Path)
    parser.add_argument("--basic-module-dir", required=True, type=Path)
    parser.add_argument("--module-header-dir", required=True, type=Path)
    parser.add_argument("--header-include-out", required=True, type=Path)
    args = parser.parse_args()

    aliases, functions, structs, enums = parse_headers(args.headers)
    catalog = json.loads(args.export_catalog.read_text(encoding="utf-8"))
    exports = export_names(catalog)
    wrappers = checked_scalar_wrappers(functions, exports)
    functions_by_name = {function["name"] for function in functions}
    public_export_functions = [function for function in functions if function["name"] in exports]
    unprototyped_exports = sorted(name for name in exports if name not in functions_by_name)
    payload = {
        "schema": "uxgsl.header-api.v1",
        "source": {"header_dir": str(args.headers), "export_catalog": str(args.export_catalog)},
        "header_count": len(list(args.headers.glob("*.h"))),
        "type_aliases": dict(sorted(aliases.items())),
        "struct_or_union_tags": sorted(structs),
        "enum_tags": sorted(enums),
        "function_count": len(functions),
        "exported_function_prototype_count": len(public_export_functions),
        "exported_symbol_without_public_function_prototype": unprototyped_exports,
        "function_categories": dict(sorted(Counter(function["header"] for function in public_export_functions).items())),
        "checked_scalar_adapter_count": len(wrappers),
        "case_disambiguated_basic_name_count": sum(1 for wrapper in wrappers if wrapper["case_disambiguated"]),
        "checked_scalar_adapters": wrappers,
        "policy": {
            "generated": "Only exported gsl_sf_* scalar functions with a verified *_e(gsl_sf_result*) peer.",
            "manual_or_future": "Pointers, buffers, structs, callbacks, complex values and unsupported scalar layouts remain metadata-only until a dedicated safe binding exists.",
            "abi": "Primitive mappings target the installed MSYS2 UCRT64/Windows x64 ABI."
        }
    }
    args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    emit_c_include(args.c_include_out, wrappers)
    emit_basic_modules(args.basic_module_dir, args.module_header_dir, wrappers)
    emit_basic_include(args.basic_include_out, wrappers)
    emit_header_include(args.header_include_out, wrappers)
    print(
        "UXGSL_HEADER_BINDINGS "
        f"headers={payload['header_count']} prototypes={payload['function_count']} "
        f"exported_prototypes={payload['exported_function_prototype_count']} checked_scalar={len(wrappers)} "
        f"unprototyped_exports={len(unprototyped_exports)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
