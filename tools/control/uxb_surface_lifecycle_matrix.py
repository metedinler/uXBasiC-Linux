#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Dict, List


REQUIRED_COLUMNS = [
    "surface_id",
    "surface_name",
    "surface_kind",
    "lifecycle_route",
    "implementation_owner",
    "compile_time_route",
    "runtime_route",
    "backend_route_x64",
    "backend_route_x86",
    "backend_route_js",
    "backend_route_wat",
    "backend_route_wasm",
    "test_positive",
    "test_negative",
]


def load_core(root: Path):
    core_path = root / "tools" / "audit" / "uxb_step1_surface_core.py"
    spec = importlib.util.spec_from_file_location("uxb_step1_surface_core", core_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load core: {core_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    ensure_dir(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def status_to_route(label: str, status: str) -> str:
    if not status:
        return f"{label}:EMPTY"
    return f"{label}:{status}"


def runtime_route(row: Dict[str, str]) -> str:
    parts = []
    for key, label in (
        ("ast_interpreter_status", "ast_interpreter"),
        ("mir_interpreter_status", "mir_interpreter"),
        ("browser_runtime_status", "browser_runtime"),
        ("library_binding_status", "library_binding"),
        ("runtime_status", "runtime"),
    ):
        value = row.get(key, "")
        if value and value not in {"MISSING", "N/A", "NOT_APPLICABLE"}:
            parts.append(f"{label}:{value}")
    return " | ".join(parts) if parts else "runtime:MISSING"


def compile_time_route(row: Dict[str, str]) -> str:
    parts = []
    for key, label in (
        ("lexer_status", "lexer"),
        ("parser_status", "parser"),
        ("ast_contract_status", "ast_contract"),
        ("semantic_status", "semantic"),
        ("type_binding_status", "type_binding"),
        ("layout_status", "layout"),
        ("hir_status", "hir"),
        ("mir_status", "mir"),
        ("mir_verify_status", "mir_verify"),
    ):
        parts.append(status_to_route(label, row.get(key, "")))
    return " | ".join(parts)


def lifecycle_route(row: Dict[str, str]) -> str:
    parts = [compile_time_route(row), runtime_route(row)]
    parts.extend(
        [
            status_to_route("x64", row.get("x64_mir_status", row.get("x64_status", ""))),
            status_to_route("x86", row.get("x86_status", "")),
            status_to_route("js", row.get("js_transpiler_status", row.get("js_status", ""))),
            status_to_route("wat", row.get("wasm_wat_status", row.get("wat_status", ""))),
            status_to_route("wasm", row.get("wasm_status", row.get("wasm_wat_status", ""))),
        ]
    )
    return " -> ".join(parts)


def matrix_row(row: Dict[str, str]) -> Dict[str, str]:
    return {
        "surface_id": row.get("id", ""),
        "surface_name": row.get("surface_name", ""),
        "surface_kind": row.get("surface_kind", ""),
        "lifecycle_route": lifecycle_route(row),
        "implementation_owner": row.get("owner", ""),
        "compile_time_route": compile_time_route(row),
        "runtime_route": runtime_route(row),
        "backend_route_x64": row.get("x64_mir_status", row.get("x64_status", "")),
        "backend_route_x86": row.get("x86_status", ""),
        "backend_route_js": row.get("js_transpiler_status", row.get("js_status", "")),
        "backend_route_wat": row.get("wasm_wat_status", row.get("wat_status", "")),
        "backend_route_wasm": row.get("wasm_status", row.get("wasm_wat_status", "")),
        "test_positive": row.get("source_file", "N/A"),
        "test_negative": row.get("required_action", "N/A"),
    }


def find_blockers(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    blockers: List[Dict[str, str]] = []
    for row in rows:
        evidence = row.get("source_file", "")
        final_decision = row.get("final_decision", "")
        backends = {
            "x64": row.get("x64_mir_status", row.get("x64_status", "")),
            "x86": row.get("x86_status", ""),
            "js": row.get("js_transpiler_status", row.get("js_status", "")),
            "wat": row.get("wasm_wat_status", row.get("wat_status", "")),
            "wasm": row.get("wasm_status", row.get("wasm_wat_status", "")),
        }
        if any(v.strip() == "" for v in matrix_row(row).values()):
            blockers.append({
                "surface_id": row.get("id", ""),
                "surface_name": row.get("surface_name", ""),
                "blocker_code": "EMPTY_CELL",
                "reason": "06 planinda zorunlu hucre bos",
                "recommended_step": "HUCRE_DOLDUR",
                "evidence_file": evidence or "N/A",
            })
        if final_decision == "IMPLEMENTED" and evidence in {"", "N/A"}:
            blockers.append({
                "surface_id": row.get("id", ""),
                "surface_name": row.get("surface_name", ""),
                "blocker_code": "FAKE_IMPLEMENTED",
                "reason": "IMPLEMENTED ama evidence_file yok",
                "recommended_step": row.get("required_action", "ADD_EVIDENCE_FILE"),
                "evidence_file": "N/A",
            })
        if final_decision in {"BROKEN", "MISSING"}:
            blockers.append({
                "surface_id": row.get("id", ""),
                "surface_name": row.get("surface_name", ""),
                "blocker_code": final_decision,
                "reason": f"final_decision={final_decision}",
                "recommended_step": row.get("required_action", "ADD_EXECUTION_PATH"),
                "evidence_file": evidence or "N/A",
            })
        for backend, status in backends.items():
            if status == "PARTIAL":
                blockers.append({
                    "surface_id": row.get("id", ""),
                    "surface_name": row.get("surface_name", ""),
                    "blocker_code": "PARTIAL_TARGET",
                    "reason": f"{backend} hedefinde PARTIAL var",
                    "recommended_step": row.get("required_action", "COMPLETE_BACKEND"),
                    "evidence_file": evidence or "N/A",
                })
    return blockers


def target_backend_blockers(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for row in rows:
        for backend, status in (
            ("x64", row.get("x64_mir_status", row.get("x64_status", ""))),
            ("x86", row.get("x86_status", "")),
            ("js", row.get("js_transpiler_status", row.get("js_status", ""))),
            ("wat", row.get("wasm_wat_status", row.get("wat_status", ""))),
            ("wasm", row.get("wasm_status", row.get("wasm_wat_status", ""))),
        ):
            if status in {"PARTIAL", "BROKEN", "MISSING"}:
                out.append({
                    "surface_id": row.get("id", ""),
                    "surface_name": row.get("surface_name", ""),
                    "backend": backend,
                    "status": status,
                    "recommended_step": row.get("required_action", "FIX_BACKEND"),
                })
    return out


def test_plan(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "surface_id": row.get("id", ""),
            "surface_name": row.get("surface_name", ""),
            "test_positive": row.get("source_file", "N/A"),
            "test_negative": row.get("required_action", "N/A"),
        }
        for row in rows
    ]


def gate_markdown(summary: Dict[str, object], blockers: List[Dict[str, str]]) -> str:
    lines = [
        "# Surface Lifecycle Gate",
        "",
        f"- status: {summary['status']}",
        f"- surface_count: {summary['surface_count']}",
        f"- blocker_count: {summary['blocker_count']}",
        f"- fake_implemented_count: {summary['fake_implemented_count']}",
        f"- backend_blocker_count: {summary['backend_blocker_count']}",
        "",
        "## Blockers",
    ]
    if not blockers:
        lines.append("- none")
    else:
        for row in blockers[:200]:
            lines.append(
                f"- {row['surface_id']} {row['surface_name']} {row['blocker_code']} :: {row['recommended_step']}"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    core = load_core(root)
    project_root = core.find_project_root(root)
    rows = core.build_surface_rows(project_root)

    out_dir = project_root / "reports" / "control" / "current"
    lifecycle_rows = [matrix_row(r) for r in rows]
    blockers = find_blockers(rows)
    backend_rows = target_backend_blockers(rows)
    test_rows = test_plan(rows)

    summary = {
        "status": "PASS" if not blockers else "FAIL",
        "surface_count": len(rows),
        "blocker_count": len(blockers),
        "fake_implemented_count": sum(1 for x in blockers if x["blocker_code"] == "FAKE_IMPLEMENTED"),
        "backend_blocker_count": len(backend_rows),
    }

    write_csv(out_dir / "surface_lifecycle_matrix.csv", lifecycle_rows, REQUIRED_COLUMNS)
    write_csv(
        out_dir / "surface_lifecycle_blockers.csv",
        blockers,
        ["surface_id", "surface_name", "blocker_code", "reason", "recommended_step", "evidence_file"],
    )
    write_csv(
        out_dir / "target_backend_blockers.csv",
        backend_rows,
        ["surface_id", "surface_name", "backend", "status", "recommended_step"],
    )
    write_csv(
        out_dir / "surface_test_plan.csv",
        test_rows,
        ["surface_id", "surface_name", "test_positive", "test_negative"],
    )
    ensure_dir(out_dir / "surface_lifecycle_summary.json")
    (out_dir / "surface_lifecycle_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "surface_lifecycle_gate.md").write_text(
        gate_markdown(summary, blockers),
        encoding="utf-8",
    )

    print(str(out_dir / "surface_lifecycle_summary.json"))
    print(f"SURFACE_COUNT={len(rows)}")
    print(f"BLOCKER_COUNT={len(blockers)}")
    if args.strict and blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
