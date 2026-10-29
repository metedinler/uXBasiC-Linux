#!/usr/bin/env python3
"""Generate uXBasic uxcapi aggregate descriptor builders from MIR Full JSON v2."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCALAR_KIND = {
    "I8": "KIND_I8", "U8": "KIND_U8",
    "I16": "KIND_I16", "U16": "KIND_U16",
    "I32": "KIND_I32", "U32": "KIND_U32",
    "I64": "KIND_I64", "U64": "KIND_U64",
    "F32": "KIND_F32", "F64": "KIND_F64",
    "PTR": "KIND_PTR", "POINTER": "KIND_PTR",
}


def ident(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", text.strip())
    if not value or value[0].isdigit():
        value = "T_" + value
    return value.upper()


def extent_product(field: dict[str, Any]) -> int:
    result = 1
    for dim in field.get("dimensions", []):
        result *= int(dim.get("extent", 0))
    return result


def render(data: dict[str, Any], namespace: str) -> str:
    records = [
        r for r in data.get("module", {}).get("record_types", [])
        if str(r.get("abi", "")).lower() == "c"
    ]
    names = {str(r["name"]).upper(): r for r in records}
    lines: list[str] = [
        "' Generated from uxb-mir-full-json-2 record_types.",
        "' Natural C ABI STRUCT values may be passed by value through uxcapi.",
        "' UNION descriptors are layout metadata; pass UNION data by pointer or adapter.",
        'INCLUDE "include/modules/uxcapi.uxmh"',
        "",
        f"NAMESPACE {namespace}",
        "",
    ]
    for record in records:
        lines.append(f"DECLARE FUNCTION Build_{ident(record['name'])}() AS U64")
    lines.append("")

    for record in records:
        name = str(record["name"])
        fn = f"Build_{ident(name)}"
        kind = str(record.get("kind", "type")).lower()
        size = int(record.get("size", 0))
        align = int(record.get("alignment", 0))
        lines += [f"FUNCTION {fn}() AS U64", "    DIM result AS U64", "    DIM ok AS I32"]
        if kind == "union":
            lines += [
                f"    result = uxcapi.TypeUnionNew({size}, {align})",
                "    RETURN result",
                "END FUNCTION",
                "",
            ]
            continue
        if kind != "struct":
            lines += [
                f"    ' Unsupported record kind: {kind}",
                "    RETURN 0",
                "END FUNCTION",
                "",
            ]
            continue
        if record.get("ffi_by_value") is False:
            reason = str(record.get("ffi_by_value_reason", "requires pointer passing or a C adapter"))
            lines += [
                f"    ' Not directly callable by value: {reason}",
                "    RETURN 0",
                "END FUNCTION",
                "",
            ]
            continue
        lines.append("    result = uxcapi.TypeStructNew()")
        for field in record.get("fields", []):
            field_type = str(field.get("type", "")).upper()
            count = extent_product(field) if field.get("is_array") else 1
            if field_type in SCALAR_KIND:
                if count == 1:
                    lines.append(f"    ok = uxcapi.TypeAddField(result, uxcapi.{SCALAR_KIND[field_type]})")
                else:
                    lines.append(f"    ok = uxcapi.TypeAddArrayField(result, uxcapi.{SCALAR_KIND[field_type]}, {count})")
            elif field_type in names and str(names[field_type].get("kind", "")).lower() == "struct":
                nested = f"nested_{ident(field.get('name', 'field'))}"
                lines.append(f"    DIM {nested} AS U64")
                lines.append(f"    {nested} = Build_{ident(field_type)}()")
                if count == 1:
                    lines.append(f"    ok = uxcapi.TypeAddStructField(result, {nested})")
                else:
                    lines.append(f"    ok = uxcapi.TypeAddStructArrayField(result, {nested}, {count})")
                lines.append(f"    uxcapi.TypeFree({nested})")
            else:
                lines.append(f"    ' ERROR: unsupported by-value field {field.get('name')} AS {field_type}")
                lines.append("    uxcapi.TypeFree(result)")
                lines.append("    RETURN 0")
        lines += [
            f"    ok = uxcapi.TypeSetExpectedLayout(result, {size}, {align})",
            "    ok = uxcapi.TypeFinalize(result)",
            "    IF ok == 0 THEN",
            "        uxcapi.TypeFree(result)",
            "        RETURN 0",
            "    END IF",
            "    RETURN result",
            "END FUNCTION",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mir_json", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--namespace", default="uxcabi_records")
    args = parser.parse_args()
    data = json.loads(args.mir_json.read_text(encoding="utf-8"))
    if data.get("schema_version") != "uxb-mir-full-json-2":
        raise SystemExit("Expected schema_version uxb-mir-full-json-2")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data, ident(args.namespace)), encoding="utf-8", newline="\n")
    print(f"OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
