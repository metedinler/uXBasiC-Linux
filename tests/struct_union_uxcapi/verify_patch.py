#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_MARKERS = {
    "src/parser/lexer/lexer_keyword_table.fbs": ["struct", "union", "abi", "pack", "align"],
    "src/parser/parser/parser_stmt_decl_core.fbs": ["UXB_C_ABI_RECORDS_20260728", "recordContract", "IsEndRecordStart"],
    "src/parser/parser/parser_surface_coverage_gate.fbs": ["Return 219", "Case 214: Return \"ABI\"", "Case 218: Return \"UNION\""],
    "src/semantic/layout/layout_shared_core.fbs": ["recordKind As String", "packBytes As Integer", "explicitAlign As Integer"],
    "src/semantic/layout/layout_type_table.fbs": ["recordKind = \"UNION\"", "TypeLayoutDescribeGlobal", "uxb.semantic.layouts.v2"],
    "src/semantic/mir_full_exporter_json.fbs": ["record_types", "ffi_by_value", "explicit_alignment"],
    "runtime_ext/uxcapi/uxcapi.h": ["UXC_KIND_STRUCT", "UXC_KIND_UNION", "uxcapi_call_arg_struct", "uxcapi_result_struct_copy"],
    "runtime_ext/uxcapi/uxcapi.c": ["#define UXCAPI_VERSION 200", "uxcapi_type_finalize", "add_aggregate_argument", "result_storage"],
    "libsx/uxcapi/uxcapi.bas": ["KIND_STRUCT", "TypeStructNew", "ArgStruct", "ResultStructCopy"],
    "manifests/uxb_library_system.json": ["uxcabi.dll", "struct-by-value", "union-layout-byref"],
}

NEW_EXPORTS = [
    "uxcapi_type_struct_new", "uxcapi_type_union_new", "uxcapi_type_add_field",
    "uxcapi_type_add_struct_field", "uxcapi_type_add_array_field",
    "uxcapi_type_add_struct_array_field", "uxcapi_type_set_expected_layout",
    "uxcapi_type_finalize", "uxcapi_type_kind", "uxcapi_type_size",
    "uxcapi_type_alignment", "uxcapi_type_free", "uxcapi_call_set_return_struct",
    "uxcapi_call_arg_struct", "uxcapi_args_add_struct", "uxcapi_result_struct_size",
    "uxcapi_result_struct_copy",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    failures: list[str] = []

    for rel, markers in REQUIRED_MARKERS.items():
        path = root / rel
        if not path.is_file():
            failures.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in markers:
            if marker not in text:
                failures.append(f"missing marker {marker!r}: {rel}")

    manifest_path = root / "manifests/uxb_library_system.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = {x.get("name"): x for x in manifest.get("libraries", [])}
        item = entries.get("uxcapi")
        if not item:
            failures.append("manifest: uxcapi entry missing")
        else:
            if item.get("minimum_api_version") != 200:
                failures.append("manifest: uxcapi minimum_api_version != 200")
            if "uxcabi.dll" not in item.get("dll_aliases", []):
                failures.append("manifest: uxcabi.dll alias missing")
    except Exception as exc:
        failures.append(f"manifest JSON invalid: {exc}")

    header = (root / "runtime_ext/uxcapi/uxcapi.h").read_text(encoding="utf-8")
    source = (root / "runtime_ext/uxcapi/uxcapi.c").read_text(encoding="utf-8")
    wrapper = (root / "libsx/uxcapi/uxcapi.bas").read_text(encoding="utf-8")
    for name in NEW_EXPORTS:
        if not re.search(r"\b" + re.escape(name) + r"\s*\(", header):
            failures.append(f"header export missing: {name}")
        if not re.search(r"\b" + re.escape(name) + r"\s*\(", source):
            failures.append(f"source definition missing: {name}")
        if name not in wrapper:
            failures.append(f"uXBasic wrapper missing call: {name}")

    if source.count("{") != source.count("}"):
        failures.append("uxcapi.c brace count mismatch")

    for rel in [
        "src/parser/parser/parser_stmt_decl_core.fbs",
        "src/semantic/layout/layout_type_table.fbs",
        "libsx/uxcapi/uxcapi.bas",
    ]:
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        starts = len(re.findall(r"(?im)^\s*(?:private\s+|public\s+)?(?:function|sub)\b", text))
        ends = len(re.findall(r"(?im)^\s*end\s+(?:function|sub)\b", text))
        if starts != ends:
            failures.append(f"FreeBASIC block imbalance: {rel}: starts={starts}, ends={ends}")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("PASS: UXB_STRUCT_UNION_UXCAPI_20260728 static verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
