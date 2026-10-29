import argparse
import json
import re
from pathlib import Path
from run_consolidation_tests import invoke

NAMES = ["surface_backend_matrix", "builtin_backend_matrix", "type_backend_matrix",
         "library_target_matrix", "design_semantics_matrix"]
ap = argparse.ArgumentParser()
ap.add_argument("--compiler", required=True)
ap.add_argument("--report", required=True)
args = ap.parse_args()
compiler = Path(args.compiler).resolve()
report = Path(args.report).resolve()
root = report.parent / (report.stem + "_runs")
root.mkdir(parents=True, exist_ok=True)
rows = []
for name in ("default", "explicit_root_with_spaces", "unwritable_target"):
    case = root / name
    case.mkdir(parents=True, exist_ok=True)
    output = case / "custom root" if name != "default" else case / "build"
    extra = ["--out-root", output] if name != "default" else []
    if name == "unwritable_target":
        output.mkdir(parents=True, exist_ok=True)
        blocked = output / "matrix_blocked"
        blocked.mkdir(parents=True, exist_ok=True)
        (blocked / "matrices").write_text("obstruction", encoding="utf-8")
        extra += ["--run-id", "matrix_blocked"]
    result = invoke([compiler, "mtx", *extra], case)
    if name == "unwritable_target":
        ok = result["exit"] != 0 and "PASS" not in result["stdout"]
    else:
        found = []
        match = re.search(r"matris dosyasi uretildi -> (.+)", result["stdout"])
        matrix_dir = Path(match[1].strip()) if match else output / "matrices"
        if not matrix_dir.is_absolute():
            matrix_dir = case / matrix_dir
        assert matrix_dir.resolve().is_relative_to(output.resolve())
        for base in NAMES:
            path = matrix_dir / (base + ".json")
            if path.is_file() and isinstance(json.loads(path.read_text(encoding="utf-8")), (dict, list)):
                found.append(str(path))
        result["files"] = found
        ok = result["exit"] == 0 and len(found) == 5 and "PASS" in result["stdout"]
    result.update(test=name, **{"pass": ok})
    rows.append(result)
    print(f"{'PASS' if ok else 'FAIL'} {name} exit={result['exit']}", flush=True)
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps({"compiler": str(compiler), "results": rows}, indent=2), encoding="utf-8")
passed = sum(r["pass"] for r in rows)
print(f"Toplam: {len(rows)} PASS: {passed} FAIL: {len(rows)-passed}")
raise SystemExit(0 if passed == len(rows) else 1)
