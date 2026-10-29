#!/usr/bin/env python3
"""Generate parser/semantic examples only for library APIs absent from tests."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/surface_example_gaps.json"
OUT = ROOT / "tests/library_surface_gaps"


def dummy_for(type_name: str) -> str:
    t = type_name.upper().replace("BYVAL", "").replace("BYREF", "").strip()
    if "STRING" in t or "ZSTRING" in t or "WSTRING" in t:
        return '""'
    if any(x in t for x in ("F32", "F64", "F80", "F128", "DOUBLE", "SINGLE")):
        return "0.0"
    return "0"


def declarations(path: Path) -> dict[str, tuple[str, str, list[str]]]:
    current_namespace = ""
    found: dict[str, tuple[str, str, list[str]]] = {}
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        ns = re.match(r"(?i)^\s*NAMESPACE\s+([A-Za-z_][A-Za-z0-9_]*)", raw)
        if ns:
            current_namespace = ns.group(1)
            continue
        match = re.match(
            r"(?i)^\s*(?:PUBLIC\s+|PRIVATE\s+)?(FUNCTION|SUB)\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)",
            raw,
        )
        if not match:
            continue
        kind, name, param_text = match.groups()
        args: list[str] = []
        if param_text.strip():
            for param in param_text.split(","):
                type_match = re.search(r"(?i)\bAS\s+(.+?)\s*$", param.strip())
                args.append(dummy_for(type_match.group(1) if type_match else "I32"))
        found[name] = (current_namespace, kind.upper(), args)
    return found


def main() -> int:
    payload = json.loads(REPORT.read_text(encoding="utf-8-sig"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "expected").mkdir(exist_ok=True)
    rows: list[dict[str, str]] = []

    for library, coverage in payload["libraries"].items():
        missing = coverage["missing"]
        if not missing:
            continue
        source = ROOT / coverage["source"]
        decls = declarations(source)
        include = ROOT / "include/modules" / f"{library}.uxmh"
        if not include.exists():
            # Some wrappers are distributed directly under libsx.
            include_text = source.relative_to(ROOT).as_posix()
        else:
            include_text = include.relative_to(ROOT).as_posix()

        include_lines: list[str] = []
        if library == "uxaimath":
            include_lines.append('INCLUDE "include/modules/uxtensor.uxmh"')
        include_lines.append(f'INCLUDE "{include_text}"')
        lines = [
            *include_lines,
            "",
            "MAIN",
            "    IF FALSE THEN",
        ]
        emitted: list[str] = []
        for name in missing:
            if name not in decls:
                continue
            namespace, kind, args = decls[name]
            prefix = f"{namespace}." if namespace else ""
            call = f"{prefix}{name}({', '.join(args)})"
            if kind == "FUNCTION":
                lines.append(f"        PRINT {call}")
            else:
                lines.append(f"        {call}")
            emitted.append(name)
        lines.extend([
            "    END IF",
            f'    PRINT "PASS_LIBRARY_SURFACE_{library.upper()}"',
            "END MAIN",
            "",
        ])
        test_name = f"{library}_missing_surface.uxb"
        expected_name = f"{library}_missing_surface.stdout.txt"
        (OUT / test_name).write_text("\n".join(lines), encoding="utf-8")
        (OUT / "expected" / expected_name).write_text(
            f"PASS_LIBRARY_SURFACE_{library.upper()}\n", encoding="utf-8"
        )
        rows.append({
            "library": library,
            "source": test_name,
            "expected": f"expected/{expected_name}",
            "api_count": str(len(emitted)),
            "apis": " ".join(emitted),
        })

    with (OUT / "library_surface_tests.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["library", "source", "expected", "api_count", "apis"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"generated={len(rows)} directory={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
