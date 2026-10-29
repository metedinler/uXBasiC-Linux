"""Run the existing isolated library suites with bounded independent workers."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--compiler", required=True)
parser.add_argument("--report", required=True)
parser.add_argument("--jobs", type=int, choices=range(1, 5), default=2)
args = parser.parse_args()
compiler = Path(args.compiler).resolve()
report = Path(args.report).resolve()
report.parent.mkdir(parents=True, exist_ok=True)
pwsh = shutil.which("pwsh")
if not pwsh:
    raise SystemExit("PowerShell 7 is required for the bounded library runners.")
cases = []
for library in ("uxsdl3", "uxraylib"):
    for source in sorted((ROOT / "tests/libraries" / library).glob("*.uxb")):
        if re.search(r'PRINT\s+"([A-Z0-9_]+_PASS)"', source.read_text(encoding="utf-8-sig")):
            cases.append((library, source))
# Establish the formerly failing clean-directory core case early.
cases.sort(key=lambda pair: ("core" not in pair[1].stem, pair[0], pair[1].stem))


def run_case(case):
    library, source = case
    limit = 420 if library == "uxsdl3" else 1200
    log = report.parent / (report.stem + "_" + source.stem + ".log")
    started = time.monotonic()
    command = [pwsh, "-NoProfile", "-File", str(source.parent / ("run_" + library + "_smoke_tests.ps1")),
               "-Uxb", str(compiler), "-TestRoot", str(source.parent),
               "-Only", source.stem, "-TimeoutSec", str(limit)]
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            code = process.wait(timeout=limit * 4 + 120)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            process.wait()
            code = -999
    text = log.read_text(encoding="utf-8", errors="replace")
    summary = re.search(r"Toplam:\s*(\d+)\s+PASS:\s*(\d+)\s+FAIL:\s*(\d+)", text)
    total, passed, failed = map(int, summary.groups()) if summary else (4, 0, 4)
    okay = code == 0 and total == 4 and passed == 4 and failed == 0
    if code != 0 and failed == 0:
        passed, failed = 0, total
    return {"library": library, "test": source.stem, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "exit": code, "total": total, "passed": passed, "failed": failed, "pass": okay,
            "seconds": round(time.monotonic() - started, 3), "log": str(log)}


results = []
started = time.monotonic()
compiler_hash = hashlib.sha256(compiler.read_bytes()).hexdigest()
with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    futures = [pool.submit(run_case, case) for case in cases]
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
        record = {"schema": "uxb.library_acceptance.v1", "compiler": str(compiler), "compiler_sha256": compiler_hash,
                  "requested_cases": len(cases), "completed_cases": len(results), "results": results,
                  "seconds": round(time.monotonic() - started, 3)}
        report.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{'PASS' if result['pass'] else 'FAIL'} {result['test']} {result['passed']}/{result['total']}", flush=True)
passed = sum(result["passed"] for result in results)
total = sum(result["total"] for result in results)
print(f"Toplam: {total} PASS: {passed} FAIL: {total - passed}")
raise SystemExit(0 if results and all(result["pass"] for result in results) else 1)
