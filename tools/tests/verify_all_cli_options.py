#!/usr/bin/env python3
"""Verify every canonical CLI registry option against help and live parsing."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


VALUE_OVERRIDES = {
    "--target": "x64",
    "--stop-after": "par",
    "--diag-format": "json",
    "--error-limit": "20",
    "--codegen-source": "MIR",
    "--x64-mode": "MIR",
    "--interpreter-backend": "AST",
    "--pp": "A",
    "--preprocessor": "A",
    "--console-mode": "plain",
    "--message-lang": "en",
    "--language": "en",
    "--run-id": "cli_contract",
    "--source": "smoke.uxb",
    "-s": "smoke.uxb",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--uxb", default="bin/uxb.exe")
    parser.add_argument("--runtime", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    surface_path = root / "vscode-extension/generated/language-surface.json"
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    options = [item for item in surface["cliOptions"] if not item.get("removed")]
    uxb = (root / args.uxb).resolve()
    help_run = subprocess.run([str(uxb), "--help"], cwd=root, text=True, capture_output=True)
    help_text = help_run.stdout + help_run.stderr

    rows: list[dict] = []
    seen: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="uxb_cli_contract_") as tmp:
        tmp_path = Path(tmp)
        for index, item in enumerate(options):
            name = item["name"]
            duplicate = name.lower() in seen
            seen.add(name.lower())
            in_help = name in help_text
            live_exit = None
            live_ok = None
            detail = ""
            if args.runtime:
                command = [str(uxb), "--help", name]
                if item.get("needsValue"):
                    value = VALUE_OVERRIDES.get(name)
                    if value is None:
                        extension = str(item.get("expectedExtension", "")).strip()
                        suffix = extension if extension.startswith(".") else ".out"
                        value = str(tmp_path / f"option_{index:03d}{suffix}")
                    command.append(value)
                proc = subprocess.run(command, cwd=root, text=True, capture_output=True)
                combined = proc.stdout + proc.stderr
                live_exit = proc.returncode
                live_ok = proc.returncode == 0 and "Bilinmeyen CLI" not in combined and "Unknown CLI" not in combined
                if not live_ok:
                    detail = combined[-500:]
            status = "PASS" if in_help and not duplicate and (live_ok is not False) else "FAIL"
            rows.append({
                "name": name,
                "short": item.get("short", ""),
                "layer": item.get("layer", ""),
                "needs_value": bool(item.get("needsValue")),
                "produces_file": bool(item.get("producesFile")),
                "in_help": in_help,
                "duplicate": duplicate,
                "live_exit": live_exit,
                "live_ok": live_ok,
                "status": status,
                "detail": detail,
            })

    failures = [row for row in rows if row["status"] != "PASS"]
    report_dir = root / "reports/cli"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "uxbasic.cli_all_options.verify.v1",
        "status": "PASS" if not failures and help_run.returncode == 0 else "FAIL",
        "registry_count": len(options),
        "help_exit": help_run.returncode,
        "runtime_checked": args.runtime,
        "failures": len(failures),
        "rows": rows,
    }
    (report_dir / "all_cli_options_verify.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"CLI_VERIFY status={report['status']} options={len(options)} failures={len(failures)} runtime={args.runtime}")
    for row in failures[:20]:
        print(f"FAIL {row['name']}: help={row['in_help']} duplicate={row['duplicate']} live={row['live_ok']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
