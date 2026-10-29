#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uXBasic merkezi test runner.
- Tek komutla Yama 1.1, Yama 2, Yama 3, Yama 4, Yama 5 testlerini çalıştırır.
- Her testin stdout/stderr çıktısını build/all_tests/logs altına yazar.
- JSON özetini build/all_tests/summary.json olarak üretir.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class TestCase:
    name: str
    args: List[str]
    run_id: str
    expect_fail: bool = False
    contains: List[str] = field(default_factory=list)
    not_contains: List[str] = field(default_factory=list)
    check_files: List[tuple[str, List[str], List[str]]] = field(default_factory=list)


def rel(path: str) -> str:
    return path.replace("/", os.sep)


def file_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def run_case(root: Path, exe: str, out_root: str, logs_dir: Path, case: TestCase) -> dict:
    exe_path = Path(exe)
    if not exe_path.is_absolute():
        exe_path = (root / exe_path).resolve()

    cmd = [str(exe_path)] + case.args + ["--out-root", out_root, "--run-id", case.run_id]
    log_path = logs_dir / f"{case.name}.log"

    result = {
        "name": case.name,
        "cmd": cmd,
        "run_id": case.run_id,
        "status": "UNKNOWN",
        "returncode": None,
        "log": str(log_path),
        "messages": [],
    }

    source_file = root / case.args[1] if len(case.args) > 1 else None
    if source_file is not None and not source_file.exists():
        result["status"] = "FAIL"
        result["messages"].append(f"Kaynak test dosyasi yok: {source_file}")
        log_path.write_text("\n".join(result["messages"]), encoding="utf-8")
        return result

    if not exe_path.exists():
        result["status"] = "FAIL"
        result["messages"].append(f"UXB exe bulunamadi: {exe_path}")
        log_path.write_text("\n".join(result["messages"]), encoding="utf-8")
        return result

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        result["status"] = "FAIL"
        result["messages"].append(f"Test timeout: {case.name}")
        log_path.write_text((exc.stdout or "") + "\n" + (exc.stderr or ""), encoding="utf-8", errors="replace")
        return result

    result["returncode"] = proc.returncode
    combined = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
    log_path.write_text(combined, encoding="utf-8", errors="replace")

    if case.expect_fail:
        if proc.returncode == 0:
            result["status"] = "FAIL"
            result["messages"].append("Bu test hata vermeliydi ama gecti.")
        else:
            result["status"] = "PASS"
            result["messages"].append("Beklenen negatif test hatasi alindi.")
            return result
    else:
        if proc.returncode != 0:
            result["status"] = "FAIL"
            result["messages"].append(f"Return code basarisiz: {proc.returncode}")

    for needle in case.contains:
        if needle not in combined:
            result["status"] = "FAIL"
            result["messages"].append(f"Stdout/stderr icinde beklenen metin yok: {needle}")

    for needle in case.not_contains:
        if needle in combined:
            result["status"] = "FAIL"
            result["messages"].append(f"Stdout/stderr icinde olmamasi gereken metin var: {needle}")

    for rel_file, must_have, must_not_have in case.check_files:
        rel_path = Path(rel_file)
        # Expected artifacts follow --out-root.  The old runner always looked
        # under build/, producing false failures whenever a custom report root
        # was requested.
        if rel_path.parts and rel_path.parts[0].lower() == "build":
            rel_path = Path(out_root).joinpath(*rel_path.parts[1:])
        fpath = root / rel_path
        text = file_text(fpath)
        if not fpath.exists():
            result["status"] = "FAIL"
            result["messages"].append(f"Beklenen cikti dosyasi yok: {rel_path}")
            continue
        for needle in must_have:
            if needle not in text:
                result["status"] = "FAIL"
                result["messages"].append(f"{rel_file} icinde beklenen metin yok: {needle}")
        for needle in must_not_have:
            if needle in text:
                result["status"] = "FAIL"
                result["messages"].append(f"{rel_file} icinde olmamasi gereken metin var: {needle}")

    if result["status"] == "UNKNOWN":
        result["status"] = "PASS"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="bin/uxb.exe")
    ap.add_argument("--out-root", default="build")
    ap.add_argument("--suite", default="all", choices=["all", "oop", "task", "slot", "trigger", "tasktable", "output"])
    args = ap.parse_args()

    root = Path.cwd()
    all_root = root / args.out_root / "all_tests"
    logs_dir = all_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    tests: list[TestCase] = []

    def add(case: TestCase, suites: list[str]):
        if args.suite == "all" or args.suite in suites:
            tests.append(case)

    add(TestCase("output_policy_smoke_ast", ["ast", rel("tests/output_policy/output_root_smoke.uxb")], "all_output_policy_smoke"), ["output"])

    add(TestCase("yama2_task_event_ast", ["ast", rel("tests/yama2_task_blocks/task_event_body_yama2.uxb")], "all_yama2_event_ast"), ["task"])
    add(TestCase("yama2_task_pipe_ast", ["ast", rel("tests/yama2_task_blocks/task_pipe_input_yama2.uxb")], "all_yama2_pipe_ast"), ["task"])
    add(TestCase("yama2_task_thread_paralel_ast", ["ast", rel("tests/yama2_task_blocks/task_thread_paralel_body_yama2.uxb")], "all_yama2_thread_paralel_ast"), ["task"])
    add(TestCase("yama2_task_nested_ast", ["ast", rel("tests/yama2_task_blocks/task_nested_qualified_yama2.uxb")], "all_yama2_nested_ast"), ["task"])

    add(TestCase("yama2_oop_magic_known_sem", ["sem", rel("tests/oop_contract/oop_magic_all_known_hooks_yama2.uxb")], "all_yama2_oop_magic_known"), ["oop"])
    add(TestCase("yama2_oop_magic_custom_sem", ["sem", rel("tests/oop_contract/oop_custom_magic_hash_yama2.uxb")], "all_yama2_oop_magic_custom"), ["oop"])
    add(TestCase("yama2_oop_dtor_int", ["int", rel("tests/oop_contract/oop_destructor_delete_chain_yama2.uxb")], "all_yama2_oop_dtor"), ["oop"])
    add(TestCase("yama2_oop_interface_virtual_sem", ["sem", rel("tests/oop_contract/oop_interface_virtual_super_yama2.uxb")], "all_yama2_oop_interface_virtual"), ["oop"])

    add(TestCase("yama3_slot_basic_ast", ["ast", rel("tests/yama3_slot_table/slot_table_basic_yama3.uxb")], "all_yama3_slot_basic_ast"), ["slot"])
    add(TestCase("yama3_slot_basic_sem", ["sem", rel("tests/yama3_slot_table/slot_table_basic_yama3.uxb")], "all_yama3_slot_basic_sem"), ["slot"])
    add(TestCase("yama3_slot_basic_int", ["int", rel("tests/yama3_slot_table/slot_table_basic_yama3.uxb")], "all_yama3_slot_basic_int"), ["slot"])
    add(TestCase("yama3_slot_infer_sem", ["sem", rel("tests/yama3_slot_table/slot_table_infer_kind_yama3.uxb")], "all_yama3_slot_infer_sem"), ["slot"])
    add(TestCase("yama3_slot_bad_id_negative", ["sem", rel("tests/yama3_slot_table/slot_table_bad_id_yama3.uxb")], "all_yama3_slot_bad_id", expect_fail=True), ["slot"])

    add(TestCase(
        "yama4_trigger_event_int",
        ["int", rel("tests/yama4_trigger/trigger_event_with_input_yama4.uxb"), "--interpreter-backend", "MIR"],
        "all_yama4_trigger_event",
        check_files=[(rel("build/all_yama4_trigger_event/json/execution/mir_program_output.txt"), ["EVENT_INPUT", "42"], [])],
    ), ["trigger"])
    add(TestCase("yama4_trigger_task_types_int", ["int", rel("tests/yama4_trigger/trigger_thread_paralel_pipe_yama4.uxb")], "all_yama4_trigger_task_types"), ["trigger"])
    add(TestCase("yama4_trigger_explicit_sem", ["sem", rel("tests/yama4_trigger/trigger_explicit_kind_yama4.uxb")], "all_yama4_trigger_explicit"), ["trigger"])
    add(TestCase("yama4_trigger_missing_slot_negative", ["sem", rel("tests/yama4_trigger/trigger_missing_slot_should_fail_yama4.uxb")], "all_yama4_trigger_missing_slot", expect_fail=True), ["trigger"])

    add(TestCase("yama5_tasktable_event_ast", ["ast", rel("tests/yama5_runtime_tasktable/tasktable_event_input_yama5.uxb")], "all_yama5_event_ast"), ["tasktable"])
    add(TestCase(
        "yama5_tasktable_event_int",
        ["int", rel("tests/yama5_runtime_tasktable/tasktable_event_input_yama5.uxb"), "--interpreter-backend", "MIR"],
        "all_yama5_event_int",
        check_files=[(rel("build/all_yama5_event_int/json/execution/mir_program_output.txt"), ["EVENT_INPUT", "42"], [])],
    ), ["tasktable"])
    add(TestCase(
        "yama5_tasktable_overwrite_int",
        ["int", rel("tests/yama5_runtime_tasktable/tasktable_slot_overwrite_yama5.uxb"), "--interpreter-backend", "MIR"],
        "all_yama5_overwrite",
        check_files=[(rel("build/all_yama5_overwrite/json/execution/mir_program_output.txt"), ["SON"], [])],
    ), ["tasktable"])
    add(TestCase(
        "yama5_tasktable_slot_off_int",
        ["int", rel("tests/yama5_runtime_tasktable/tasktable_slot_off_yama5.uxb"), "--interpreter-backend", "MIR"],
        "all_yama5_slot_off",
        check_files=[(rel("build/all_yama5_slot_off/json/execution/mir_program_output.txt"), ["DONE"], ["SHOULD_NOT_PRINT"])],
    ), ["tasktable"])
    add(TestCase(
        "yama5_tasktable_all_kinds_int",
        ["int", rel("tests/yama5_runtime_tasktable/tasktable_all_kinds_yama5.uxb"), "--interpreter-backend", "MIR"],
        "all_yama5_all_kinds",
        check_files=[(rel("build/all_yama5_all_kinds/json/execution/mir_program_output.txt"), ["PIPE_RUN", "THREAD_RUN", "PARALEL_RUN"], [])],
    ), ["tasktable"])
    add(TestCase("yama5_tasktable_missing_slot_negative", ["sem", rel("tests/yama5_runtime_tasktable/tasktable_missing_slot_should_fail_yama5.uxb")], "all_yama5_missing_slot", expect_fail=True), ["tasktable"])

    results = []
    fail_count = 0
    for i, case in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {case.name}")
        res = run_case(root, args.exe, args.out_root, logs_dir, case)
        results.append(res)
        print(f"    {res['status']}")
        for msg in res["messages"]:
            print(f"    - {msg}")
        if res["status"] != "PASS":
            fail_count += 1

    summary = {
        "schema": "uxb.all_tests.summary.v1",
        "suite": args.suite,
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": fail_count,
        "results": results,
    }
    (all_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTOPLAM: {summary['total']}  PASS: {summary['pass']}  FAIL: {summary['fail']}")
    print(f"Özet: {all_root / 'summary.json'}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
