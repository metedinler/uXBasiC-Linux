#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adım 18 release gate.

Aggregates lifecycle matrix, blockers, tests, expected/actual comparison and
backend/release artifacts. It does not modify source code.
"""
from __future__ import annotations
import argparse, csv, json, shutil, time
from pathlib import Path
from typing import Dict, List, Any, Optional

RELEASE_FILES = [
    "reports/control/current/adim13_test_plan.csv",
    "reports/control/current/adim13_test_results.csv",
    "reports/control/current/adim13_expected_actual.csv",
]


def find_uxb_root(start: Path) -> Path:
    p = start.resolve()
    for c in [p] + list(p.parents):
        if (c / "src").is_dir() and (c / "tools").is_dir(): return c
        if (c / "uxb" / "src").is_dir(): return c / "uxb"
    raise SystemExit("uXBasic root not found")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists(): return []
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception: return {}


def latest_existing(paths: List[Path]) -> Optional[Path]:
    existing = [p for p in paths if p.exists()]
    if not existing: return None
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return existing[0]


def locate_matrix(root: Path) -> Optional[Path]:
    c = root / "reports" / "control" / "current"
    h = root / "reports" / "control" / "history"
    candidates = [c/"surface_lifecycle_matrix.csv", c/"keyword_layer_matrix.csv", root/"reports"/"step1"/"keyword_layer_matrix.csv"]
    if h.exists():
        candidates += list(h.glob("**/surface_lifecycle_matrix.csv"))
        candidates += list(h.glob("**/keyword_layer_matrix.csv"))
    return latest_existing(candidates)


def count_empty_cells(rows: List[Dict[str, str]]) -> int:
    n = 0
    for r in rows:
        for _, v in r.items():
            if str(v).strip() == "": n += 1
    return n


def count_status(rows: List[Dict[str, str]], bad: set[str]) -> int:
    n = 0
    for r in rows:
        for _, v in r.items():
            if str(v).strip().upper() in bad: n += 1
    return n


def load_blocker_csvs(root: Path) -> List[Path]:
    c = root / "reports" / "control" / "current"
    h = root / "reports" / "control" / "history"
    files = [c/"surface_lifecycle_blockers.csv", c/"target_backend_blockers.csv"]
    if h.exists():
        files += list(h.glob("**/surface_lifecycle_blockers.csv"))[-3:]
        files += list(h.glob("**/target_backend_blockers.csv"))[-3:]
    return [p for p in files if p.exists()]


def make_release_candidate(root: Path, report: Dict[str, Any]) -> None:
    dist = root / "dist" / "release_candidate"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "release_manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ["# uXBasic Release Candidate", "", f"- status: `{report['status']}`", f"- blocker_count: `{len(report['blockers'])}`", ""]
    md.append("## Reports")
    for f in RELEASE_FILES + ["reports/control/current/adim13_release_gate.json", "reports/control/current/adim13_release_gate.md"]:
        md.append(f"- `{f}`")
    (dist / "README.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--allow-skips", action="store_true")
    ap.add_argument("--require-backend-outputs", action="store_true")
    args = ap.parse_args()
    root = find_uxb_root(Path(args.root))
    current = root / "reports" / "control" / "current"
    current.mkdir(parents=True, exist_ok=True)
    blockers: List[str] = []
    warnings: List[str] = []

    for rel in RELEASE_FILES:
        if not (root / rel).exists(): blockers.append(f"missing required report: {rel}")

    matrix_path = locate_matrix(root)
    matrix_rows: List[Dict[str, str]] = []
    if matrix_path is None:
        blockers.append("surface lifecycle matrix not found")
    else:
        matrix_rows = read_csv(matrix_path)
        empty_cells = count_empty_cells(matrix_rows)
        broken_missing = count_status(matrix_rows, {"BROKEN", "MISSING"})
        partial = count_status(matrix_rows, {"PARTIAL"})
        if empty_cells > 0: blockers.append(f"matrix has empty cells: {empty_cells}")
        if broken_missing > 0: blockers.append(f"matrix has BROKEN/MISSING cells: {broken_missing}")
        if partial > 0: blockers.append(f"matrix has PARTIAL cells: {partial}")

    for bfile in load_blocker_csvs(root):
        b_rows = read_csv(bfile)
        if b_rows:
            blockers.append(f"blocker csv not empty: {bfile.name} rows={len(b_rows)}")

    test_results = read_json(current / "adim13_test_results.json")
    if test_results:
        if int(test_results.get("fail_count", 0) or 0) > 0:
            blockers.append(f"test failures: {test_results.get('fail_count')}")
        if int(test_results.get("skip_count", 0) or 0) > 0 and not args.allow_skips:
            blockers.append(f"test skips not allowed: {test_results.get('skip_count')}")
    else:
        blockers.append("adim13_test_results.json missing or invalid")

    exp_actual = read_json(current / "adim13_expected_actual.json")
    if exp_actual:
        if int(exp_actual.get("mismatch_count", 0) or 0) > 0:
            blockers.append(f"expected/actual mismatches: {exp_actual.get('mismatch_count')}")
    else:
        blockers.append("adim13_expected_actual.json missing or invalid")

    if args.require_backend_outputs:
        candidates = [root/"dist"/"native", root/"dist"/"web", root/"dist"/"wasm"]
        existing = [p for p in candidates if p.exists() and any(p.iterdir())]
        if not existing:
            blockers.append("backend output directories are empty/missing")

    status = "PASS" if not blockers else "FAIL"
    report = {
        "schema": "uxb-adim13-release-gate-1",
        "status": status,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "matrix": str(matrix_path) if matrix_path else "",
        "matrix_rows": len(matrix_rows),
        "blockers": blockers,
        "warnings": warnings,
        "test_summary": test_results,
        "expected_actual_summary": exp_actual,
    }
    (current / "adim13_release_gate.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ["# Adım 13 Release Gate", "", f"- status: `{status}`", f"- blockers: `{len(blockers)}`", f"- matrix_rows: `{len(matrix_rows)}`", ""]
    md.append("## Blockers")
    if blockers:
        for b in blockers[:200]: md.append(f"- {b}")
    else:
        md.append("- none")
    md.append("")
    md.append("## Warnings")
    if warnings:
        for w in warnings: md.append(f"- {w}")
    else:
        md.append("- none")
    (current / "adim13_release_gate.md").write_text("\n".join(md), encoding="utf-8")
    make_release_candidate(root, report)
    print("ADIM13_RELEASE_GATE=" + str(current / "adim13_release_gate.md"))
    print("STATUS=" + status)
    print("BLOCKER_COUNT=" + str(len(blockers)))
    return 0 if status == "PASS" or not args.strict else 1

if __name__ == "__main__":
    raise SystemExit(main())
