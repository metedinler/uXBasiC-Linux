#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
passed: list[str] = []
failed: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    target = passed if condition else failed
    target.append(name if not detail else f"{name} :: {detail}")


def read(rel: str) -> str:
    path = ROOT / rel
    check(f"file {rel}", path.is_file())
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


required = {
    "src/parser/parser/parser_stmt_event_pipe.fbs": [
        "ParseParamList(ps, blockNode)",
        "return type is only valid for PIPE",
        "ParseSimpleStatement(ps)",
    ],
    "src/semantic/semantic_pass.fbs": [
        "SemValidateTaskRoutineSignature",
        "SemValidateTaskInvocation",
        "TRIGGER hedefi bulunamadi",
        "BYREF parametre desteklenmiyor",
    ],
    "src/runtime/exec/exec_call_dispatch_helpers.fbs": [
        "ExecInvokeRoutineByIndexOffset",
        "ExecApplyDeclaredType",
        "boundValues",
        'ExecSetVarValue es, "INPUT"',
        'ExecSetVarValue es, "OUTPUT"',
    ],
    "src/runtime/exec/exec_slot_manager.fbs": [
        "ExecInvokeTaskRoutineByIndex",
        "taskParamCount",
        "Legacy SLOT/native ABI v1 compatibility",
    ],
    "src/interpreter/ast/ast_interp_call.fbs": [
        "UXBAstInterpRunTaskRoutine",
        "routine arity mismatch",
        "UXBAstInterpExecSequenceChildren",
        "UXBInterpApplyDeclaredType",
    ],
    "src/semantic/mir_lower_slot_lane.fbs": [
        "MIRAppendFunctionParam",
        "__PIPE_RESULT",
        "taskArgCount",
        "MIR_OP_CALL",
    ],
    "src/semantic/mir.fbs": [
        "MIRNormalizeTaskResultAlias",
        "last assignment wins",
    ],
    "src/runtime/memory_exec.fbs": [
        "Type-name calls and typed routine parameters share one",
        "ExecApplyDeclaredType(scalarArgValue",
    ],
}

for rel, markers in required.items():
    content = read(rel)
    for marker in markers:
        check(f"marker {rel}: {marker}", marker in content)

# Function/Sub structural balance for every changed FreeBASIC source file.
try:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True
    ).splitlines()
except Exception as exc:
    changed = []
    check("git changed-file inventory", False, str(exc))

for rel in changed:
    if not rel.lower().endswith((".fbs", ".bas")):
        continue
    content = read(rel)
    functions = len(re.findall(r"^\s*(?:(?:Private|Public)\s+)?Function\b", content, re.I | re.M))
    end_functions = len(re.findall(r"^\s*End\s+Function\b", content, re.I | re.M))
    subs = len(re.findall(r"^\s*(?:(?:Private|Public)\s+)?Sub\b", content, re.I | re.M))
    end_subs = len(re.findall(r"^\s*End\s+Sub\b", content, re.I | re.M))
    check(
        f"balance {rel}",
        functions == end_functions and subs == end_subs,
        f"Function {functions}/{end_functions}, Sub {subs}/{end_subs}",
    )

# Specific regression gates.
slot = read("src/runtime/exec/exec_slot_manager.fbs")
check("typed header scan runtime", "Do While headerIdx <> -1" in slot and '"SLOT_HEADER_ARGS"' in slot)
mir_lane = read("src/semantic/mir_lower_slot_lane.fbs")
check("typed header scan MIR", "Do While headerNode <> -1" in mir_lane and '"SLOT_HEADER_ARGS"' in mir_lane)
ast_stmt = read("src/interpreter/ast/ast_interp_stmt.fbs")
check("AST routine node index", "resolvedTaskNode = taskRoutineIdx" in ast_stmt)
check("AST no invalid routine-array indexing", "ctx.routines(taskRoutineIdx).nodeIndex" not in ast_stmt)
mir_expr = read("src/semantic/mir_lower_expr.fbs")
mir_stmt = read("src/semantic/mir_lower_stmt.fbs")
check("MIR OUTPUT read alias", "MIRNormalizeTaskResultAlias(module, fnIdx, kwName)" in mir_expr)
check("MIR PIPE-name write alias", "MIRNormalizeTaskResultAlias(module, fnIdx, ps.ast.nodes(st.left).value)" in mir_stmt)

positive = sorted((ROOT / "tests/typed_task_routines").glob("0*.uxb"))
negative = sorted((ROOT / "tests/typed_task_routines").glob("negative_*.uxb"))
check("positive test inventory", len(positive) == 8, f"found {len(positive)}")
check("negative test inventory", len(negative) == 4, f"found {len(negative)}")

try:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True)
    check("git diff --check", result.returncode == 0, result.stdout + result.stderr)
except Exception as exc:
    check("git diff --check", False, str(exc))

print("UXB_TYPED_TASK_ROUTINES_REAL_20260728 static verification")
for item in passed:
    print(f"PASS  {item}")
for item in failed:
    print(f"FAIL  {item}")
print(f"SUMMARY pass={len(passed)} fail={len(failed)}")
sys.exit(1 if failed else 0)
