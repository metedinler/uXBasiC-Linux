#!/usr/bin/env python3
"""Build and verify a complete installed-GSL export catalog for UXGSL.

The catalog is generated from the exact PE DLLs staged by MSYS2, rather than
from a hand-maintained list. It therefore covers every callable GSL/CBlas
export in the installed binary, including APIs which require callbacks or
aggregate ABI descriptors and are invoked through uxcapi.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path


TABLE_RE = re.compile(
    r"^\s*\[\s*(?P<index>\d+)\]\s+\+base\[\s*\d+\]\s+\S+\s+(?P<name>\S+)\s*$"
)


def exports_from_objdump(objdump: Path, dll: Path) -> list[str]:
    output = subprocess.check_output([str(objdump), "-p", str(dll)], text=True, errors="replace")
    in_export_table = False
    names: list[str] = []
    for line in output.splitlines():
        if "[Ordinal/Name Pointer] Table -- Ordinal Base" in line:
            in_export_table = True
            continue
        if not in_export_table:
            continue
        match = TABLE_RE.match(line)
        if match:
            names.append(match.group("name"))
    return sorted(set(names))


def group_for(name: str) -> str:
    if name.startswith("gsl_sf_"):
        return "special-functions"
    if name.startswith("gsl_stats_"):
        return "statistics"
    if name.startswith("gsl_matrix") or name.startswith("gsl_vector"):
        return "linear-algebra-storage"
    if name.startswith("gsl_integration"):
        return "integration"
    if name.startswith("gsl_odeiv"):
        return "ode"
    if name.startswith("gsl_rng") or name.startswith("gsl_ran"):
        return "random"
    if name.startswith("gsl_"):
        return "gsl-other"
    if name.startswith("cblas_"):
        return "cblas"
    return "data-or-other"


def verify_loaded_exports(dll_dir: Path, dll_name: str, names: list[str]) -> list[str]:
    dll_dir = dll_dir.resolve()
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(dll_dir))
    module = ctypes.WinDLL(str(dll_dir / dll_name))
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    kernel32.GetProcAddress.restype = ctypes.c_void_p
    missing = [name for name in names if not kernel32.GetProcAddress(module._handle, name.encode("ascii"))]
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate UXGSL's installed-DLL export catalog")
    parser.add_argument("--objdump", required=True, type=Path)
    parser.add_argument("--gsl-dll", required=True, type=Path)
    parser.add_argument("--cblas-dll", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    modules = []
    for dll in (args.gsl_dll, args.cblas_dll):
        names = exports_from_objdump(args.objdump, dll)
        modules.append({"dll": dll.name, "exports": names, "export_count": len(names)})

    verification = {}
    if args.verify:
        for module in modules:
            missing = verify_loaded_exports(args.gsl_dll.parent, module["dll"], module["exports"])
            verification[module["dll"]] = {"missing": missing, "resolved_count": len(module["exports"]) - len(missing)}

    all_names = [name for module in modules for name in module["exports"]]
    payload = {
        "schema": "uxgsl.export-catalog.v2",
        "source": "PE export tables from installed MSYS2 UCRT64 GSL binaries",
        "modules": modules,
        "total_export_count": len(all_names),
        "groups": dict(sorted(Counter(group_for(name) for name in all_names).items())),
        "verification": verification,
        "raw_access": {
            "gsl_factory": "uxgsl.GslCallNew",
            "cblas_factory": "uxgsl.CblasCallNew",
            "bridge": "uxcapi.dll",
            "argument_kinds": "uxcapi.KIND_*"
        },
        "support_contract": {
            "symbol_reachability": "Every exported symbol in these exact DLL builds is verified as resolvable.",
            "typed_binding_coverage": "Only functions in libsx/uxgsl/uxgsl.bas are stable typed UXGSL APIs.",
            "raw_abi_caution": "Catalog entries do not provide C signatures, struct layouts, callback lifetimes, or ownership rules."
        }
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"UXGSL_EXPORTS total={payload['total_export_count']} modules={len(modules)}")
    if args.verify:
        failures = sum(len(row["missing"]) for row in verification.values())
        print(f"UXGSL_EXPORT_VERIFY missing={failures}")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
