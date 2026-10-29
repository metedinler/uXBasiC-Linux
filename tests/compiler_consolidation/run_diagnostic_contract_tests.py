"""Exercise diagnostic CLI output, requested logs and controlled I/O failures."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]


def json_records(text):
    records = []
    decoder = json.JSONDecoder()
    text = text.strip()
    while text:
        value, end = decoder.raw_decode(text)
        records.append(value)
        text = text[end:].lstrip()
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--runtime")
    parser.add_argument("--with-iff", action="store_true")
    args = parser.parse_args()
    compiler = Path(args.compiler).resolve()
    report = Path(args.report).resolve()
    runs = report.parent / (report.stem + "_runs")
    runs.mkdir(parents=True, exist_ok=True)
    sources = {name: Path(__file__).with_name('diagnostic_cases') / (name + '.uxb')
               for name in ('semantic', 'parser', 'success', 'iff_arity', 'many_parser_errors')}
    results = []
    paired = {}

    def invoke(name, source_kind, language="en", extra=()):
        case_dir = runs / name
        case_dir.mkdir(parents=True, exist_ok=True)
        source = sources[source_kind]
        log = case_dir / "requested_name.log"
        log_options = [] if "--error-log-out" in extra else ["--error-log-out", str(log)]
        process = subprocess.run([str(compiler), "run", str(source), "--message-lang", language,
                                  "--diag-format", "json", *log_options,
                                  "--out-root", str(case_dir / "artifacts"), *map(str, extra)],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=120)
        row = {"test": name, "source": str(source), "exit": process.returncode, "stdout": process.stdout,
               "stderr": process.stderr, "log": str(log)}
        results.append(row)
        return row, case_dir, log

    for kind in ("semantic", "parser"):
        for language in ("en", "tr"):
            row, case_dir, log = invoke(kind + "_" + language, kind, language)
            try:
                records = json_records(row["stdout"])
                row["records"] = records
                row["pass"] = (row["exit"] != 0 and bool(records) and log.is_file()
                               and all("code" in r and "message_en" in r and "message_tr" in r
                                       and "source" in r for r in records))
                paired[(kind, language)] = (row["exit"], [(r["code"], r["source"]["line"],
                                                         r["source"]["col"]) for r in records])
                diagnostic_file = next((case_dir / "artifacts").rglob("all_diagnostics.json"))
                diagnostics = json.loads(diagnostic_file.read_text(encoding="utf-8-sig"))
                payload = diagnostics.get("payload", diagnostics)
                row["diagnostics"] = payload
                # Unknown semantic coordinates are 0:0; parser coordinates come from tokens.
                entries = payload["diagnostics"]
                row["pass"] &= bool(entries) and all(d["source"]["known"] == (
                    d["source"]["line"] > 0 and d["source"]["col"] > 0) for d in entries)
                if kind == "semantic":
                    row["pass"] &= entries[0]["source"]["line"] == 0
                else:
                    row["pass"] &= entries[0]["source"]["line"] > 0
                    log_text = log.read_text(encoding="utf-8-sig")
                    location = entries[0]["source"]
                    row["pass"] &= ("source_line=" + str(location["line"])) in log_text
            except (ValueError, KeyError, StopIteration) as error:
                row["pass"] = False
                row["validation_error"] = str(error)
        results.append({"test": kind + "_language_invariance", "pass": (
            (kind, "en") in paired and paired.get((kind, "en")) == paired.get((kind, "tr")))})

    for option in ("--error-log-out", "--log-out"):
        blocked = runs / (option[2:] + "_directory")
        blocked.mkdir(exist_ok=True)
        row, _, _ = invoke(option[2:] + "_failure", "success", extra=(option, blocked))
        try:
            records = json_records(row["stdout"])
            row["records"] = records
            row["pass"] = row["exit"] == 22 and any(
                r["code"] == "UXB_DIAGNOSTIC_LOG_WRITE_FAILED" and r.get("path") == str(blocked)
                for r in records)
        except ValueError as error:
            row["pass"] = False
            row["validation_error"] = str(error)

    if args.with_iff:
        signatures = []
        for language in ("en", "tr"):
            row, _, _ = invoke("iff_arity_" + language, "iff_arity", language)
            try:
                records = json_records(row["stdout"])
                row["records"] = records
                first = records[0]
                row["pass"] = (row["exit"] != 0 and first["code"] == "UXB_IFF_ARGUMENT_COUNT"
                               and first["message"] == first["message_" + language]
                               and first["message_en"] != first["message_tr"]
                               and first["source"]["known"] and first["source"]["line"] == 1)
                signatures.append((row["exit"], first["code"], first["source"]["line"], first["source"]["col"]))
            except (ValueError, KeyError, IndexError) as error:
                row["pass"] = False
                row["validation_error"] = str(error)
        results.append({"test": "iff_arity_language_invariance", "pass": len(signatures) == 2 and signatures[0] == signatures[1]})

    parent_file = runs / "blocked_parent_file"
    parent_file.write_text("file, not a directory\n", encoding="utf-8")
    for option in ("--error-log-out", "--log-out"):
        row, _, _ = invoke(option[2:] + "_parent_failure", "success",
                           extra=(option, parent_file / "child.log"))
        try:
            records = json_records(row["stdout"])
            row["records"] = records
            row["pass"] = row["exit"] == 22 and any(
                r["code"] == "UXB_DIAGNOSTIC_LOG_WRITE_FAILED" for r in records)
        except ValueError as error:
            row["pass"] = False
            row["validation_error"] = str(error)

    catalog = runs / "catalog_utf8.csv"
    catalog.write_text("E.0300;Semantic;Custom semantic message;Türkçe özel ileti\n", encoding="utf-8")
    for language, wanted in (("en", "Custom semantic message"), ("tr", "Türkçe özel ileti")):
        row, _, _ = invoke("catalog_" + language, "semantic", language,
                           extra=("--error-language-file", catalog))
        try:
            records = json_records(row["stdout"])
            row["records"] = records
            row["pass"] = row["exit"] != 0 and records[0]["message"] == wanted
        except (ValueError, KeyError, IndexError) as error:
            row["pass"] = False
            row["validation_error"] = str(error)

    fb = ROOT / "tools" / "FreeBASIC-1.10.1-win64"
    probe_scratch = tempfile.TemporaryDirectory(prefix='uxb_diagnostic_probe_')
    helper = Path(probe_scratch.name) / "diagnostic_record_probe.exe"
    environment = os.environ.copy()
    environment["PATH"] = str(fb / "bin" / "win64") + os.pathsep + environment.get("PATH", "")
    compiled = subprocess.run([str(fb / "fbc64.exe"), "-lang", "fb", "-exx", "-x", str(helper),
                               "-o", str(helper.with_suffix('.o')),
                               str(Path(__file__).with_name("diagnostic_record_probe.bas"))],
                              cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120)
    for language in ("en", "tr"):
        log = runs / ("record_" + language + ".log")
        editor = runs / ("editor_" + language + ".json")
        row = {"test": "structured_record_" + language, "pass": False}
        if compiled.returncode == 0:
            process = subprocess.run([str(helper), language, str(log), str(editor)],
                                     capture_output=True, text=True, encoding="utf-8", timeout=30)
            row.update(exit=process.returncode, stdout=process.stdout, stderr=process.stderr)
            try:
                record = json.loads(process.stdout)
                entries = record["diagnostics"]
                editor_records = json.loads(editor.read_text(encoding="utf-8"))
                row["pass"] = (process.returncode == 0 and record["count"] == 3
                               and record["error_count"] == 3 and entries[0]["occurrences"] == 2
                               and entries[1]["source"]["line"] == 21
                               and all(d["source"]["known"] for d in entries)
                               and editor_records[0]["message"] == entries[0]["message_" + language]
                               and "source_line=10 source_col=3" in log.read_text(encoding="utf-8"))
            except (ValueError, KeyError, IndexError) as error:
                row["validation_error"] = str(error)
        else:
            row["compile_error"] = compiled.stdout + compiled.stderr
        results.append(row)

    for limit in (1, 2, 4):
        row, case_dir, _ = invoke("parser_error_limit_" + str(limit), "many_parser_errors",
                                  extra=("--error-limit", str(limit)))
        try:
            diagnostic_file = next((case_dir / "artifacts").rglob("all_diagnostics.json"))
            data = json.loads(diagnostic_file.read_text(encoding="utf-8-sig"))
            data = data.get("payload", data)
            row["diagnostics"] = data
            row["pass"] = (row["exit"] != 0 and data["error_limit"] == limit
                           and data["error_count"] == limit and data["error_limit_reached"]
                           and len([d for d in data["diagnostics"] if d["severity"] in ("error", "fatal")]) == limit)
        except (ValueError, KeyError, StopIteration) as error:
            row["pass"] = False
            row["validation_error"] = str(error)

    for value in ("0", "-1", "abc", "1000001"):
        row, _, _ = invoke("invalid_error_limit_" + value, "success",
                           extra=("--error-limit", value))
        try:
            records = json_records(row["stdout"])
            row["pass"] = row["exit"] == 2 and any(r["code"] == "UXB_INVALID_ERROR_LIMIT" for r in records)
        except ValueError as error:
            row["pass"] = False
            row["validation_error"] = str(error)

    schema_path = runs / "diagnostics.schema.json"
    row = {"test": "diagnostic_schema_and_record_limit", "pass": False}
    if compiled.returncode == 0:
        process = subprocess.run([str(helper), "en", str(runs / "record_limited.log"),
                                  str(runs / "editor_limited.json"), "2", str(schema_path)],
                                 capture_output=True, text=True, encoding="utf-8", timeout=30)
        try:
            data = json.loads(process.stdout)
            schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
            validator.validate(data)
            rejected = 0
            for mutation in ("missing_language", "unknown_coordinates", "bad_severity"):
                broken = json.loads(json.dumps(data))
                if mutation == "missing_language":
                    del broken["diagnostics"][0]["message_en"]
                elif mutation == "unknown_coordinates":
                    broken["diagnostics"][0]["source"]["line"] = 0
                else:
                    broken["diagnostics"][0]["severity"] = "success"
                try:
                    validator.validate(broken)
                except ValidationError:
                    rejected += 1
            row.update(exit=process.returncode, schema=str(schema_path), diagnostics=data,
                       rejected_mutations=rejected)
            row["pass"] = (process.returncode == 0 and data["count"] == 2
                           and data["error_count"] == 2 and data["error_limit_reached"]
                           and data["diagnostics"][0]["occurrences"] == 2 and rejected == 3)
        except (ValueError, KeyError, ValidationError) as error:
            row["validation_error"] = str(error)
    else:
        row["compile_error"] = compiled.stdout + compiled.stderr
    results.append(row)

    rotate_dir = runs / "rotation"
    rotate_dir.mkdir(exist_ok=True)
    rotated_log = rotate_dir / "requested_name.log"
    old_contents = "historic-log\n" * 6000
    backup_contents = "preserve-existing-backup\n"
    rotated_log.write_text(old_contents, encoding="utf-8")
    existing_backup = Path(str(rotated_log) + ".bak")
    existing_backup.write_text(backup_contents, encoding="utf-8")
    before = {p.name for p in rotate_dir.glob("requested_name.log.bak*")}
    row, _, _ = invoke("rotation", "success")
    preserved = [p for p in rotate_dir.glob("requested_name.log.bak*") if p.name not in before]
    row["pass"] = (row["exit"] == 0 and existing_backup.read_text() == backup_contents
                   and len(preserved) == 1 and preserved[0].read_text() == old_contents)

    if args.runtime:
        runtime = Path(args.runtime).resolve()
        code = ("import ctypes; dll=ctypes.CDLL(" + repr(str(runtime)) + "); "
                "fn=dll.__uxb_rt_host_call; fn.argtypes=[ctypes.c_char_p]; "
                "fn.restype=ctypes.c_int64; fn(b'UXB_TEST_MISSING_HOST'); print('UNREACHABLE')")
        process = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=30)
        results.append({"test": "native_unbound_host", "exit": process.returncode,
                        "stdout": process.stdout, "stderr": process.stderr,
                        "pass": process.returncode == 1 and "UXB_RUNTIME_HOST_UNBOUND" in process.stderr
                        and "UNREACHABLE" not in process.stdout})

    passed = sum(bool(row["pass"]) for row in results)
    probe_scratch.cleanup()
    report.write_text(json.dumps({"compiler": str(compiler), "results": results}, indent=2),
                      encoding="utf-8")
    for row in results:
        print(f"{'PASS' if row['pass'] else 'FAIL'} {row['test']}")
    print(f"Toplam: {len(results)} PASS: {passed} FAIL: {len(results) - passed}")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
