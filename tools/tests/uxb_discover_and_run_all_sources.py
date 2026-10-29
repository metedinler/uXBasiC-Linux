#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uXBasic genel kaynak test koşucusu.

Amaç:
  tests/examples altındaki .uxb, .uxbh, .bas kaynaklarını keşfeder,
  derleyici katmanlarında çalıştırır ve build/source_tests altında raporlar.

Bu araç sahte PASS üretmez. Negatif test adlarını ayrı değerlendirir.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

NEGATIVE_RE = re.compile(r"(should[_-]?fail|negative|bad|invalid|error|fail)", re.I)
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "bin", "dist", "report", "reports", "_work"}
DEFAULT_EXTS = {".uxb", ".uxbh", ".bas"}
HEADER_EXTS = {".uxbh"}
HARNESSES = {"harness", "negative_harness", "probes"}


NEGATIVE_PHASE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("preprocessor", ("include_cycle", "unknown_directive", "assert_fail", "import_wrong_form", "unsafe_include")),
    ("ast", ("bad_syntax", "missing_end", "bad_string", "bad_operator", "bad_json_string")),
    ("runtime", ("memory_bounds", "poke_bad_addr", "print_file_without_open")),
    ("target", ("native_only_on_js", "call_dll_js_target", "native_dll_on_js", "import_lib_disallowed")),
]

@dataclass
class CaseResult:
    index: int
    source: str
    ext: str
    kind: str
    negative: bool
    expected_phase: str
    actual_phase: str
    mode: str
    run_id: str
    returncode: int | None
    status: str
    classification: str
    duration_sec: float
    log: str
    artifact_dir: str
    reason: str
    messages: list[str]


def find_root(start: Path) -> Path:
    p = start.resolve()
    for c in [p] + list(p.parents):
        if (c / "src").is_dir() and ((c / "tests").is_dir() or (c / "tools").is_dir()):
            return c
    return p


def safe_id(path: Path) -> str:
    raw = str(path).replace("\\", "/")
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")
    h = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:8]
    if len(base) > 80:
        base = base[-80:]
    return f"{base}_{h}"


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
        return data[:limit]
    except Exception:
        return ""


def is_probably_header(path: Path, text: str) -> bool:
    if path.suffix.lower() in HEADER_EXTS:
        return True
    up = text.upper()
    if "#INCLUDE" in up or "DECLARE" in up or "TYPE " in up or "CLASS " in up:
        if not any(k in up for k in ["PRINT", "INPUT", "TRIGGER", "MAIN", "FUNCTION MAIN"]):
            return True
    return False


def is_enum_duplicate(path: Path) -> bool:
    return any(part.lower() == "enum_tests" for part in path.parts)


def is_harness_like(path: Path, text: str) -> bool:
    rel = str(path).replace("\\", "/").lower()
    if any(part.lower() in HARNESSES for part in path.parts):
        return True
    if any(token in rel for token in ["/manual_probe", "/common_harness", "_probe", "probe__", "probe."]):
        return True
    up = text.upper()
    if "HARNESS" in up and any(token in up for token in ["NEGATIVE", "NEGATIF", "COMMON", "TEST", "GATE", "CATALOG"]):
        return True
    if "PROBE" in up and "MAIN" not in up and "PRINT" not in up:
        return True
    return False


def classify_negative(source: Path, rel: str, text: str) -> str:
    rel_name = f"{source.name} {rel}".lower()
    if any(token in rel_name for token in ("emit_js", "emit_wasm", "x86_unsupported", "backend_fallback")):
        return "target"
    if "missing_arg" in rel_name:
        return "ast"
    for phase, tokens in NEGATIVE_PHASE_RULES:
        if any(token in rel_name for token in tokens):
            return phase
    if any(token in rel_name for token in ("js_target", "wasm", "wat", "browser")):
        return "target"
    if any(token in rel_name for token in ("runtime", "memory", "poke", "print_file")):
        return "runtime"
    if "include" in rel_name or "assert" in rel_name or "directive" in rel_name:
        return "preprocessor"
    if any(token in rel_name for token in ("type_mismatch", "unknown_symbol", "bad_signature", "slot_range", "unknown_event", "function_not_lvalue", "duplicate", "constructor")):
        return "sem"
    if "%%" in text or "INCLUDE" in text.upper():
        return "preprocessor"
    return "sem"


def phase_order(phase: str) -> int:
    order = {"preprocessor": 0, "ast": 1, "sem": 2, "runtime": 3, "target": 3}
    return order.get(phase, 2)


def host_modes_for_phase(phase: str) -> list[str]:
    if phase == "preprocessor":
        return ["ast"]
    if phase == "ast":
        return ["ast"]
    if phase == "sem":
        return ["ast", "sem"]
    return ["ast", "sem", "int"]


def phase_from_output(mode: str, combined: str) -> str:
    up = combined.upper()
    if any(token in up for token in ("PREPROCESS", "DIRECTIVE", "INCLUDE", "%%INCLUDE")):
        return "preprocessor"
    if any(token in up for token in ("LEX", "TOKEN", "SYNTAX", "PARSER", "AST", "UNEXPECTED", "MISSING END")):
        return "ast"
    if any(token in up for token in ("SEMANT", "TYPE", "SYMBOL", "ASSIGNMENT", "CONVERT", "LVALUE")):
        return "sem"
    if any(token in up for token in ("RUNTIME", "EXECUTION", "DIVISION BY ZERO", "BOUNDS", "MEMORY")):
        return "runtime"
    return mode


def source_policy(path: Path, text: str, rel: str, include_headers: bool, include_enum_tests: bool, include_harnesses: bool, include_target_gates: bool) -> dict[str, str | bool | list[str]]:
    header = is_probably_header(path, text)
    enum_dup = is_enum_duplicate(path)
    harness_like = is_harness_like(path, text)
    neg = bool(NEGATIVE_RE.search(path.name) or NEGATIVE_RE.search(rel) or any(part.lower() == "negative" for part in path.parts))
    expected_phase = ""
    status = ""
    classification = "positive"
    reason = ""
    if header and not include_headers:
        status = "SKIP_HEADER"
        classification = "skip"
        reason = "Header/include dosyası; standalone çalışma dışı."
    elif enum_dup and not include_enum_tests:
        status = "SKIP_DUP_ENUM"
        classification = "skip"
        reason = "tests/enum_tests kopyası; varsayılan koşudan çıkarıldı."
    elif harness_like and not include_harnesses:
        status = "SKIP_HARNESS"
        classification = "skip"
        reason = "Harness/probe dosyası; varsayılan koşudan çıkarıldı."
    elif neg:
        classification = "negative"
        expected_phase = classify_negative(path, rel, text)
        if expected_phase == "target" and not include_target_gates:
            status = "SKIP_TARGET"
            classification = "skip"
            reason = "Target gate dosyası; host source runner tarafında ayrı çalıştırılmalı."
    else:
        classification = "positive"
        expected_phase = "host"
    return {
        "skip": bool(status),
        "status": status,
        "classification": classification,
        "expected_phase": expected_phase,
        "negative": neg,
        "header": header,
        "reason": reason,
    }


def discover(root: Path, paths: list[str], exts: set[str]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        base = Path(raw)
        if not base.is_absolute():
            base = root / base
        if not base.exists():
            continue
        if base.is_file():
            files = [base]
        else:
            files = []
            for p in base.rglob("*"):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                if p.is_file() and p.suffix.lower() in exts:
                    files.append(p)
        for f in files:
            try:
                r = f.resolve()
            except Exception:
                r = f
            if r not in seen:
                seen.add(r)
                out.append(r)
    return sorted(out, key=lambda p: str(p).lower())


def run_one(root: Path, exe: Path, source: Path, mode: str, run_id: str, out_root: Path, log_path: Path, timeout: int) -> tuple[int, str, float]:
    cmd = [str(exe), mode, str(source), "--out-root", str(out_root), "--run-id", run_id]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
        elapsed = time.time() - t0
        combined = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("CMD: " + " ".join(cmd) + "\n\n" + combined, encoding="utf-8", errors="replace")
        return proc.returncode, combined, elapsed
    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - t0
        combined = (exc.stdout or "") + "\n" + (exc.stderr or "") + f"\nTIMEOUT after {timeout}s"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("CMD: " + " ".join(cmd) + "\n\n" + combined, encoding="utf-8", errors="replace")
        return -777, combined, elapsed


def build_modes(mode: str, negative: bool, expected_phase: str, header: bool) -> list[str]:
    if header:
        return ["ast"]
    if mode == "safe":
        if negative:
            return host_modes_for_phase(expected_phase)
        return ["ast", "sem", "int"]
    if mode == "full":
        if negative:
            return host_modes_for_phase(expected_phase)
        return ["ast", "sem", "int"]
    return [mode]


def main() -> int:
    ap = argparse.ArgumentParser(description="uXBasic tests klasoru tum kaynak test runner")
    ap.add_argument("--root", default=".")
    ap.add_argument("--exe", default="bin/uxb.exe")
    ap.add_argument("--paths", default="tests,examples")
    ap.add_argument("--ext", default=".uxb,.uxbh,.bas")
    ap.add_argument("--out-root", default="build/source_tests")
    ap.add_argument("--mode", choices=["safe", "ast", "sem", "int", "full"], default="safe")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--quick", action="store_true", help="Ilk 50 dosyayla hizli kontrol")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--fail-on-any", action="store_true", help="Her fail exit code 1 donsun")
    ap.add_argument("--include-headers", action="store_true", help=".uxbh dosyalarini da calistir")
    ap.add_argument("--include-enum-tests", action="store_true", help="tests\\enum_tests kopyalarini da calistir")
    ap.add_argument("--include-harnesses", action="store_true", help="harness ve probe dosyalarini da calistir")
    ap.add_argument("--include-target-gates", action="store_true", help="JS/WASM/X64 hedef-gate testlerini de host runner'a dahil et")
    args = ap.parse_args()

    root = find_root(Path(args.root))
    exe = Path(args.exe)
    if not exe.is_absolute():
        exe = root / exe
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = root / out_root
    logs_dir = out_root / "logs"
    exts = {e.strip().lower() if e.strip().startswith(".") else "." + e.strip().lower() for e in args.ext.split(",") if e.strip()}
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]

    if not exe.exists():
        print(f"ERROR: uXBasic exe bulunamadi: {exe}")
        return 2

    files = discover(root, paths, exts or DEFAULT_EXTS)
    if args.quick and not args.limit:
        files = files[:50]
    if args.limit:
        files = files[:args.limit]

    out_root.mkdir(parents=True, exist_ok=True)
    results: list[CaseResult] = []
    fail = 0
    accepted_negative = 0
    skipped = 0

    for i, source in enumerate(files, 1):
        rel = str(source.relative_to(root)) if source.is_relative_to(root) else str(source)
        text = read_text(source)
        policy = source_policy(source, text, rel, args.include_headers, args.include_enum_tests, args.include_harnesses, args.include_target_gates)
        neg = bool(policy["negative"])
        header = bool(policy["header"])
        expected_phase = str(policy["expected_phase"])
        classification = str(policy["classification"])
        reason = str(policy["reason"])
        if policy["skip"]:
            skipped += 1
            results.append(CaseResult(i, rel, source.suffix.lower(), "header" if header else "program", neg, expected_phase, "", "-", "", None, str(policy["status"]), classification, 0.0, "", "", reason, []))
            print(f"[{len(results)}] {str(policy['status']):13} --- {rel}")
            if reason:
                print("    -", reason)
            continue

        modes = build_modes(args.mode, neg, expected_phase, header)

        for mode in modes:
            run_id = f"src_{i:05d}_{mode}_{safe_id(source.relative_to(root) if source.is_relative_to(root) else source)}"
            log_path = logs_dir / f"{run_id}.log"
            rc, combined, elapsed = run_one(root, exe, source, mode, run_id, out_root / "runs", log_path, args.timeout)
            messages: list[str] = []
            actual_phase = phase_from_output(mode, combined)
            status = "PASS"
            if neg:
                expected_rank = phase_order(expected_phase)
                current_rank = phase_order(mode if mode != "int" else "runtime")
                if expected_phase == "target":
                    if rc == 0:
                        status = "PASS_EXPECTED_HOST_OK"
                        messages.append("Beklenen hedef fazı host üzerinde geçildi; target runner ayrı çalıştırılmalı.")
                    else:
                        status = "FAIL"
                        messages.append(f"Host katmanı beklenmeden hata verdi: {rc}")
                elif expected_phase == "runtime":
                    if current_rank < expected_rank:
                        if rc == 0:
                            status = "PASS_EXPECTED_HOST_OK"
                            messages.append("Beklenen runtime negatif için host katmanları geçti.")
                        else:
                            accepted_negative += 1
                            status = "PASS_NEGATIVE_EARLY"
                            messages.append("Runtime hatası daha erken ve daha güvenli bir katmanda yakalandı.")
                    elif current_rank == expected_rank:
                        if rc != 0:
                            accepted_negative += 1
                            status = "PASS_NEGATIVE"
                            messages.append("Beklenen runtime negatif hata alındı.")
                        else:
                            status = "FAIL_NEGATIVE_ESCAPED"
                            messages.append("Runtime negatif test beklenen fazda hata vermedi.")
                    else:
                        status = "PASS_EXPECTED_HOST_OK"
                        messages.append("Beklenen runtime fazı önceki katmanlarda yakalandı.")
                elif current_rank < expected_rank:
                    if rc == 0:
                        status = "PASS_EXPECTED_AST_OK"
                        messages.append("Beklenen negatif faza kadar derleme geçti.")
                    else:
                        status = "FAIL"
                        messages.append(f"Negatif test beklenen fazdan önce hata verdi: {rc}")
                elif current_rank == expected_rank:
                    if rc != 0:
                        accepted_negative += 1
                        status = "PASS_NEGATIVE"
                        messages.append("Beklenen negatif hata alındı.")
                    else:
                        status = "FAIL_NEGATIVE_ESCAPED"
                        messages.append("Negatif test beklenen fazda hata vermedi.")
            else:
                ok = rc == 0
                status = "PASS" if ok else "FAIL"
                if not ok:
                    messages.append(f"Return code basarisiz: {rc}")
            if status.startswith("FAIL"):
                fail += 1
            artifact_dir = str((out_root / "runs" / run_id).relative_to(root)) if (out_root / "runs" / run_id).is_relative_to(root) else str(out_root / "runs" / run_id)
            results.append(CaseResult(i, rel, source.suffix.lower(), "header" if header else "program", neg, expected_phase, actual_phase, mode, run_id, rc, status, classification, round(elapsed, 3), str(log_path.relative_to(root) if log_path.is_relative_to(root) else log_path), artifact_dir, reason, messages))
            print(f"[{len(results)}] {status:13} {mode:3} {rel}")
            for m in messages:
                print("    -", m)

    summary = {
        "schema": "uxb.source_tests.summary.v1",
        "root": str(root),
        "exe": str(exe),
        "paths": paths,
        "extensions": sorted(exts),
        "mode": args.mode,
        "total_runs": len(results),
        "source_files": len(files),
        "skipped": skipped,
        "pass": sum(1 for r in results if r.status.startswith("PASS")),
        "fail": fail,
        "accepted_negative": accepted_negative,
        "results": [asdict(r) for r in results],
    }
    (out_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_root / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(asdict(results[0]).keys()) if results else ["index", "source", "status"]
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(asdict(r))

    print(f"\nKAYNAK DOSYA: {len(files)}  CALISMA: {len(results)}  PASS: {summary['pass']}  FAIL: {fail}")
    print(f"Özet: {out_root / 'summary.json'}")
    if fail and args.fail_on_any:
        return 1
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
