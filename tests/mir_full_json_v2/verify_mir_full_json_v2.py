#!/usr/bin/env python3
"""Static patch gate and runtime schema validator for uxb-mir-full-json-2."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPORTER_MARKERS = (
    "UXB_MIR_FULL_JSON_V2_20260728",
    '"uxb-mir-full-json-2"',
    '"source_files"',
    '"global_is_array"',
    '"global_symbols"',
    '"entry_block"',
    '"parameter_symbols"',
    '"local_symbols"',
    '"synthetic_label"',
    '"is_entry"',
    '"is_exit"',
    '"stored_block_id"',
    '"operand_records"',
    '"opcode_contract"',
    '"comment"',
    '"flags"',
    '"source_ast_node"',
    '"offset"',
    '"class_slot_counts"',
    '"entry_function_indexes"',
    '"classes"',
    '"entries"',
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_type(value: Any, expected: type, path: str) -> None:
    if not isinstance(value, expected):
        fail(f"{path}: expected {expected.__name__}, got {type(value).__name__}")


def static_gate(root: Path) -> None:
    exporter = root / "src" / "semantic" / "mir_full_exporter_json.fbs"
    mir_tail = root / "src" / "semantic" / "mir_tail.fbs"
    mir_facade = root / "src" / "semantic" / "mir.fbs"
    for path in (exporter, mir_tail, mir_facade):
        if not path.is_file():
            fail(f"missing file: {path}")

    exporter_text = exporter.read_text(encoding="utf-8", errors="replace")
    tail_text = mir_tail.read_text(encoding="utf-8", errors="replace")
    facade_text = mir_facade.read_text(encoding="utf-8", errors="replace")

    for marker in EXPORTER_MARKERS:
        if marker not in exporter_text:
            fail(f"missing exporter marker: {marker}")

    required_tail = (
        "moduleOut.sourceFileCount = 0",
        "Erase moduleOut.sourceFiles",
        "UXB_MIR_FULL_JSON_V2_20260728",
        "moduleOut.sourceFiles(0) = ps.lx.sourceFile",
        "moduleOut.sourceFileCount = 1",
    )
    for marker in required_tail:
        if marker not in tail_text:
            fail(f"missing MIR source-file marker: {marker}")

    for marker in ('#include once "mir_operand_role.fbs"', '#include once "mir_opcode_signature.fbs"'):
        if marker not in facade_text:
            fail(f"missing early MIR exporter dependency: {marker}")

    if "GetArgValue(\"--mir-full-json-out\"" not in (
        root / "src" / "main_program_entry.fbs"
    ).read_text(encoding="utf-8", errors="replace"):
        fail("existing --mir-full-json-out CLI route is missing")


def validate_source(source: Any, path: str) -> None:
    assert_type(source, dict, path)
    required = ("status", "origin", "file", "line", "column", "length", "offset", "lexeme")
    for key in required:
        if key not in source:
            fail(f"{path}.{key}: missing")


def validate_runtime_json(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert_type(data, dict, "root")
    if data.get("schema_version") != "uxb-mir-full-json-2":
        fail(f"schema_version mismatch: {data.get('schema_version')!r}")
    if "uxb-mir-full-json-1" not in data.get("schema_compatibility", []):
        fail("schema v1 compatibility marker missing")

    module = data.get("module")
    assert_type(module, dict, "module")

    source_files = module.get("source_files")
    assert_type(source_files, list, "module.source_files")
    if module.get("source_file_count") != len(source_files):
        fail("module.source_file_count does not match source_files")

    globals_ = module.get("globals")
    global_types = module.get("global_types")
    global_is_array = module.get("global_is_array")
    global_symbols = module.get("global_symbols")
    for name, value in (
        ("globals", globals_),
        ("global_types", global_types),
        ("global_is_array", global_is_array),
        ("global_symbols", global_symbols),
    ):
        assert_type(value, list, f"module.{name}")
    expected_globals = module.get("global_count")
    if not all(len(v) == expected_globals for v in (globals_, global_types, global_is_array, global_symbols)):
        fail("global parallel arrays/records have inconsistent lengths")

    functions = module.get("functions")
    assert_type(functions, list, "module.functions")
    if module.get("function_count") != len(functions):
        fail("module.function_count does not match functions")

    instruction_ids: list[int] = []
    counted_instructions = 0
    for fi, fn in enumerate(functions):
        assert_type(fn, dict, f"module.functions[{fi}]")
        for key in (
            "id", "name", "return_type", "entry_block", "block_count",
            "parameter_count", "local_count", "parameters", "parameter_types",
            "parameter_symbols", "locals", "local_types", "local_symbols", "declared_source", "source", "blocks",
        ):
            if key not in fn:
                fail(f"module.functions[{fi}].{key}: missing")
        validate_source(fn["declared_source"], f"module.functions[{fi}].declared_source")
        validate_source(fn["source"], f"module.functions[{fi}].source")

        if fn["parameter_count"] != len(fn["parameters"]) or fn["parameter_count"] != len(fn["parameter_types"]) or fn["parameter_count"] != len(fn["parameter_symbols"]):
            fail(f"function {fi}: parameter collections mismatch")
        if fn["local_count"] != len(fn["locals"]) or fn["local_count"] != len(fn["local_types"]) or fn["local_count"] != len(fn["local_symbols"]):
            fail(f"function {fi}: local collections mismatch")
        if fn["block_count"] != len(fn["blocks"]):
            fail(f"function {fi}: block_count mismatch")

        for bi, block in enumerate(fn["blocks"]):
            for key in (
                "index", "id", "label", "synthetic_label", "is_entry", "is_exit",
                "instruction_count", "predecessor_count", "successor_count",
                "predecessors", "successors", "instructions",
            ):
                if key not in block:
                    fail(f"function {fi} block {bi}.{key}: missing")
            if block["predecessor_count"] != len(block["predecessors"]):
                fail(f"function {fi} block {bi}: predecessor_count mismatch")
            if block["successor_count"] != len(block["successors"]):
                fail(f"function {fi} block {bi}: successor_count mismatch")
            if block["instruction_count"] != len(block["instructions"]):
                fail(f"function {fi} block {bi}: instruction_count mismatch")

            for ii, inst in enumerate(block["instructions"]):
                counted_instructions += 1
                for key in (
                    "id", "index", "function_id", "block_index", "block_id", "stored_block_id",
                    "block_id_matches", "opcode", "opcode_contract", "result", "type",
                    "result_descriptor", "operand_count", "operands", "operand_records",
                    "comment", "flags", "source_ast_node", "ffi_stub_id", "ffi_arg_start",
                    "ffi", "source", "links",
                ):
                    if key not in inst:
                        fail(f"function {fi} block {bi} instruction {ii}.{key}: missing")
                instruction_ids.append(inst["id"])
                if inst["index"] != ii or inst["function_id"] != fi or inst["block_index"] != bi:
                    fail(f"function {fi} block {bi} instruction {ii}: unstable index linkage")
                if inst["block_id"] != block["id"]:
                    fail(f"function {fi} block {bi} instruction {ii}: block_id mismatch")
                if inst["operand_count"] != len(inst["operands"]) or inst["operand_count"] != len(inst["operand_records"]):
                    fail(f"function {fi} block {bi} instruction {ii}: operand collections mismatch")
                validate_source(inst["source"], f"function {fi} block {bi} instruction {ii}.source")
                for oi, operand in enumerate(inst["operand_records"]):
                    for key in ("index", "value", "role_id", "role", "type", "type_source", "is_ffi_argument"):
                        if key not in operand:
                            fail(f"function {fi} block {bi} instruction {ii} operand {oi}.{key}: missing")
                    if operand["index"] != oi or operand["value"] != inst["operands"][oi]:
                        fail(f"function {fi} block {bi} instruction {ii} operand {oi}: linkage mismatch")

    if instruction_ids != list(range(len(instruction_ids))):
        fail("instruction ids are not stable/contiguous")

    link_report = module.get("link_report")
    assert_type(link_report, dict, "module.link_report")
    if link_report.get("instruction_count") != counted_instructions:
        fail("link_report.instruction_count mismatch")

    vtable = module.get("vtable")
    assert_type(vtable, dict, "module.vtable")
    for key in (
        "class_count", "entry_count", "class_names", "class_slot_counts", "class_slot_starts",
        "entry_keys", "entry_slots", "entry_class_indexes", "entry_function_indexes",
        "classes", "entries",
    ):
        if key not in vtable:
            fail(f"module.vtable.{key}: missing")
    if not all(len(vtable[k]) == vtable["class_count"] for k in ("class_names", "class_slot_counts", "class_slot_starts", "classes")):
        fail("vtable class collections mismatch")
    if not all(len(vtable[k]) == vtable["entry_count"] for k in ("entry_keys", "entry_slots", "entry_class_indexes", "entry_function_indexes", "entries")):
        fail("vtable entry collections mismatch")

    capabilities = data.get("capabilities")
    assert_type(capabilities, dict, "capabilities")
    for key in (
        "complete_mir_model_fields", "normalized_symbol_records", "operand_roles",
        "operand_type_hints", "source_offsets", "full_vtable", "stable_instruction_ids",
    ):
        if capabilities.get(key) is not True:
            fail(f"capabilities.{key} is not true")


def run_compiler(uxb: Path, source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(uxb), str(source), "--mir-full-json-out", str(output), "--quiet"]
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"compiler failed with exit code {completed.returncode}: {' '.join(cmd)}")
    if not output.is_file():
        fail(f"compiler did not create: {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", type=Path)
    parser.add_argument("--uxb", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    try:
        root = args.root.resolve()
        static_gate(root)
        print("PASS static MIR full JSON v2 patch gate")

        if args.uxb:
            source = (args.source or root / "tests" / "mir_full_json_v2" / "mir_full_json_v2_smoke.uxb").resolve()
            output = (args.out or root / "reports" / "mir_full_json_v2" / "mir_full_json_v2_smoke.json").resolve()
            run_compiler(args.uxb.resolve(), source, output)
            validate_runtime_json(output)
            print(f"PASS runtime MIR full JSON v2: {output}")
        elif args.json:
            validate_runtime_json(args.json.resolve())
            print(f"PASS runtime MIR full JSON v2: {args.json.resolve()}")
        return 0
    except (AssertionError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
