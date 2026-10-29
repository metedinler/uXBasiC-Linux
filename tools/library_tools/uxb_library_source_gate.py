#!/usr/bin/env python3
"""Static integrity gate for the uXBasic canonical library/ABI10 patch.

This gate is intentionally dependency-free. It does not replace a FreeBASIC or
Windows runtime build; it catches missing files, stale patch anchors, malformed
JSON, broken include forwarders and common source-regression errors before the
Windows build is attempted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Check:
    name: str
    status: str
    path: str
    message: str


def resolve_root(value: str) -> Path:
    p = Path(value).resolve()
    if (p / "src").is_dir() and (p / "runtime_ext").is_dir():
        return p
    if (p / "uxb" / "src").is_dir():
        return p / "uxb"
    raise SystemExit(f"uXBasic root not found: {p}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Static source gate for uXBasic library system")
    ap.add_argument("--root", default=".")
    ap.add_argument("--report-dir", default="reports/libraries/source_gate")
    args = ap.parse_args()
    root = resolve_root(args.root)
    report_dir = root / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    checks: list[Check] = []

    def add(name: str, ok: bool, path: Path | str, message: str) -> None:
        p = str(path)
        try:
            p = str(Path(path).resolve().relative_to(root)).replace("\\", "/")
        except (OSError, ValueError):
            p = str(Path(path).resolve()).replace("\\", "/")
        checks.append(Check(name, "PASS" if ok else "FAIL", p, message))

    required = [
        "manifests/uxb_library_system.json",
        "tools/library_tools/uxb_library_abi.py",
        "tools/library_tools/uxb_library_build.py",
        "tools/library_tools/uxb_library_export_audit.py",
        "tools/library_tools/uxb_library_layout_doctor.py",
        "runtime_ext/uxffi/uxffi.c",
        "runtime_ext/uxffi/uxffi.h",
        "runtime_ext/uxffi/build_uxffi_dll.bat",
        "runtime_ext/uxffi/fetch_uxffi_deps_msys2.bat",
        "native/uxb_runtime/uxb_runtime.h",
        "native/uxb_runtime/uxb_runtime.cpp",
        "native/uxb_runtime/uxb_runtime_state.cpp",
        "native/uxb_runtime/uxb_runtime_task.cpp",
        "native/uxb_runtime/uxb_runtime_shell.cpp",
        "native/uxb_runtime/build_runtime_dll.ps1",
        "native/uxb_runtime/build_runtime_dll.bat",
        "native/uxb_runtime/tests/runtime_smoke.cpp",
        "tools/tests/check_yama6_runtime_dll.py",
        "tools/tests/run_yama6_interpreter_tests.py",
        "src/runtime/exec/exec_ffi_bridge10.fbs",
        "src/runtime/exec/exec_ffi_runtime.fbs",
        "src/runtime/exec/exec_eval_builtin_categories.fbs",
        "src/interpreter/mir/mir_interp_ffi.fbs",
        "src/interpreter/mir/mir_interp_dispatch.fbs",
        "src/interpreter/mir/mir_interp_registry.fbs",
        "src/codegen/x64/stmt_emitters/x64_codegen_stmt_dll_ffi.fbs",
        "src/codegen/x64/ffi_call_backend.fbs",
        "tests/ecosystem/test_ecosystem_hardening.py",
        "tests/ecosystem/run_ecosystem_hardening.ps1",
        "tools/library_tools/uxb_ecosystem_doctor.py",
        "RUN_UXB_ECOSYSTEM_DOCTOR.bat",
        "compiler/scripts/build_libraries.ps1",
        "compiler/scripts/build_uxb_main_64.ps1",
        "compiler/scripts/build_uxb_main_64.bat",
        "compiler/scripts/resolve_uxb_toolchain.ps1",
        "compiler/scripts/build_uxb_library_system.ps1",
        "build_64.ps1",
        "build_64.bat",
        "compiler/scripts/run_library_abi10_smoke.ps1",
        "BUILD_UXB_LIBRARY_SYSTEM.ps1",
        "BUILD_UXB_LIBRARY_SYSTEM.bat",
        "libsx/uxllamax/uxllamax.bas",
        "include/modules/uxllamax.uxmh",
    ]
    for rel in required:
        p = root / rel
        add("required-file", p.is_file(), p, "exists" if p.is_file() else "missing")

    wrapper_marker = re.compile(r"\b(?:placeholder|stub|noop|no-op|not implemented|unimplemented|todo|fixme)\b", re.IGNORECASE)
    for p in sorted((root / "libsx").glob("*/*.bas")):
        text = p.read_text(encoding="utf-8", errors="replace")
        match = wrapper_marker.search(text)
        add("library-wrapper-real-source", match is None, p,
            "no inactive implementation marker" if match is None else f"forbidden marker={match.group(0)!r}")

    c_style_header_guard = re.compile(r"(?im)^\s*#(?:ifndef|define|endif)\b")
    for p in sorted((root / "include").rglob("*.uxmh")):
        text = p.read_text(encoding="utf-8", errors="replace")
        match = c_style_header_guard.search(text)
        add("uxmh-language-syntax", match is None, p,
            "uses uXBasic header syntax" if match is None else f"invalid C preprocessor line={match.group(0).strip()!r}")

    aggregate_header = root / "include/libs.uxmh"
    aggregate_text = aggregate_header.read_text(encoding="utf-8", errors="replace") if aggregate_header.is_file() else ""
    add("uxllamax-aggregate-forwarder", 'INCLUDE "include/modules/uxllamax.uxmh"' in aggregate_text,
        aggregate_header, "uxllamax is part of the standard library aggregate")

    manifest_path = root / "manifests/uxb_library_system.json"
    manifest: dict = {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        add("manifest-json", True, manifest_path, "valid JSON")
    except Exception as exc:
        add("manifest-json", False, manifest_path, str(exc))

    if manifest:
        abi = manifest.get("abi", {})
        add("abi-max-arguments", abi.get("max_arguments") == 10, manifest_path,
            f"max_arguments={abi.get('max_arguments')!r}")
        add("abi-target", "x64" in str(abi.get("target", "")).lower(), manifest_path,
            str(abi.get("target", "")))
        libraries = manifest.get("libraries", [])
        names = [str(x.get("name", "")).lower() for x in libraries]
        add("manifest-library-unique", len(names) == len(set(names)), manifest_path,
            f"libraries={len(names)} unique={len(set(names))}")
        uxffi_rows = [x for x in libraries if str(x.get("name", "")).lower() == "uxffi"]
        add("manifest-uxffi-core-required", len(uxffi_rows) == 1 and bool(uxffi_rows[0].get("required")), manifest_path,
            "uxffi must be required by the canonical core system build")
        for lib in libraries:
            name = str(lib.get("name", ""))
            for key in ("native_dir", "wrapper", "public_header"):
                rel = str(lib.get(key, "") or "")
                if not rel:
                    continue
                p = root / rel
                add(f"library-{key}", p.exists(), p, f"{name}: {'exists' if p.exists() else 'missing'}")
            native_header = str(lib.get("native_header", "") or "")
            if native_header:
                p = root / native_header
                add("library-native-header", p.is_file(), p, f"{name}: {'exists' if p.is_file() else 'missing'}")
            for rel in lib.get("build", []):
                p = root / rel
                add("library-build-script", p.is_file(), p, f"{name}: {'exists' if p.is_file() else 'missing'}")

    anchors: dict[str, list[str]] = {
        "src/parser/parser/parser_stmt_dispatch.fbs": [
            "supports at most 10 runtime arguments", 'Case "VOID", "I32", "U32", "I64", "U64"'
        ],
        "src/runtime/exec/exec_ffi_bridge10.fbs": [
            "ExecFfiBridge10Invoke", "ExecFfiBridge10CopyString", "argCount > 10"
        ],
        "src/runtime/exec/exec_ffi_runtime.fbs": [
            "ExecFfiBridge10Invoke", "gExecLastCallValueExValid = 1", 'fv.valueType = "FLOAT"'
        ],
        "src/runtime/exec/exec_eval_builtin_categories.fbs": [
            "ABI10 supports at most 10 runtime arguments",
            "requires library, symbol and return signature"
        ],
        "src/runtime/exec/exec_types.fbs": [
            "gExecLastCallValueEx", "callReturnValueEx As ExecValue"
        ],
        "src/interpreter/mir/mir_interp_ffi.fbs": [
            "UXBMIRInterpExecFfi", "uxffi_copy_string",
            "UXB_MIRFFI_MAX_ARGS As Long = 10"
        ],
        "src/interpreter/mir/mir_interp_dispatch.fbs": [
            '#include once "mir_interp_ffi.fbs"', "UXBMIRInterpIsFfiCall(ins)"
        ],
        "src/interpreter/mir/mir_interp_registry.fbs": [
            'If op = "MIR_NATIVE_ONLY" Or op = "INLINE" Then Return MIR_EXEC_NATIVE_ONLY'
        ],
        "src/runtime/memory_exec.fbs": [
            "gExecLastCallValueExValid", "typedCallReturn"
        ],
        "src/codegen/x64/stmt_emitters/x64_codegen_stmt_dll_ffi.fbs": [
            "If argCount > 10 Then", "32-byte shadow space"
        ],
        "runtime_ext/uxffi/uxffi.c": [
            "uxffi_invoke10", "uxffi_copy_string", "UXFFI_MAX_ARGS", "ffi_call"
        ],
        "compiler/scripts/build_uxb_main_64.ps1": [
            "tools\\FreeBASIC-1.10.1-win64", "fbc64.exe", "COMPILER_ARCH=x64", "bin\\uxb.exe"
        ],
        "compiler/scripts/resolve_uxb_toolchain.ps1": [
            "C:\\msys64\\ucrt64\\bin\\gcc.exe", "tools\\wabt\\bin\\wat2wasm.exe", "TOOLCHAIN_STATUS"
        ],
        "tools/library_tools/uxb_library_build.py": [
            "Native DLLs are built and deployed first", "build_compiler_x64", "build_order"
        ],
        "native/uxb_runtime/uxb_runtime.cpp": [
            "uxb_task_set_callback", "uxb_shell_run", "uxb_parallel_run"
        ],
        "src/runtime/native/uxb_runtime_bridge.fbs": [
            "UXBRtTaskSetCallbackFn", "uxb_runtime_backend_name", "uxb_slot_control"
        ],
        "src/runtime/exec/exec_slot_manager.fbs": [
            "ExecSlotNativeCallback", "uxb_runtime_native_callbacks_enabled", "uxb_parallel_run"
        ],
        "src/parser/parser/parser_stmt_basic.fbs": [
            'Case "NOWAIT"', 'Case "TIMEOUT", "RUNPATH", "OUTPATH", "ERRPATH"'
        ],
        "src/semantic/mir_lower_stmt.fbs": [
            '"SHELL_NOWAIT"', '"SHELL_" & shellOptName'
        ],
        "src/interpreter/mir/mir_interp.fbs": [
            'Case "SHELL_NOWAIT"', 'Case "SHELL"', "UXBMIRInterpRunShell"
        ],
    }
    for rel, needles in anchors.items():
        p = root / rel
        text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        for needle in needles:
            add("source-anchor", needle in text, p, f"anchor={needle!r}")

    forbidden: dict[str, list[str]] = {
        "src/runtime/exec/exec_ffi_runtime.fbs": ['fv.valueType = "DOUBLE"'],
        "src/runtime/exec/exec_eval_builtin_categories.fbs": ["expects at least 4 arguments"],
    }
    for rel, needles in forbidden.items():
        p = root / rel
        text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        for needle in needles:
            add("forbidden-regression", needle not in text, p, f"forbidden={needle!r}")

    # Manifest-owned public headers are source forwarders to real wrappers.
    # uXBasic uses the language-level INCLUDE statement in .uxmh files.
    for lib in manifest.get("libraries", []) if manifest else []:
        header_rel = str(lib.get("public_header", "") or "")
        wrapper_rel = str(lib.get("wrapper", "") or "")
        if not header_rel or not wrapper_rel:
            continue
        p = root / header_rel
        if p.suffix.lower() != ".uxmh":
            add("module-forwarder", False, p, "public_header must be a uXBasic .uxmh forwarder; use native_header for C/C++ headers")
            continue
        text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        matches = re.findall(r'(?im)^\s*INCLUDE\s+"([^"]+)"', text)
        if not matches:
            add("module-forwarder", False, p, "no language-level INCLUDE target")
            continue
        normalized = [x.replace("\\", "/") for x in matches]
        add("module-forwarder", wrapper_rel.replace("\\", "/") in normalized, p,
            f"wrapper={wrapper_rel.replace(chr(92), '/')} targets={normalized}")

    # Light preprocessor balance check for patched FBS files. It deliberately
    # ignores normal IF/END IF because FreeBASIC permits many single-line forms.
    fbs_paths = [root / rel for rel in anchors if rel.lower().endswith(".fbs")]
    for p in fbs_paths:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        starts = len(re.findall(r"(?im)^\s*#(?:if|ifdef|ifndef)\b", text))
        ends = len(re.findall(r"(?im)^\s*#endif\b", text))
        add("preprocessor-balance", starts == ends, p, f"open={starts} close={ends}")

    # ABI bridge C header/source agreement.
    h = root / "runtime_ext/uxffi/uxffi.h"
    c = root / "runtime_ext/uxffi/uxffi.c"
    expected_exports = ["uxffi_version", "uxffi_invoke10", "uxffi_copy_string", "uxffi_release_handle", "uxffi_clear_handles", "uxffi_shutdown"]
    ht = h.read_text(encoding="utf-8", errors="replace") if h.is_file() else ""
    ct = c.read_text(encoding="utf-8", errors="replace") if c.is_file() else ""
    for symbol in expected_exports:
        add("bridge-export-declared", symbol in ht, h, symbol)
        add("bridge-export-defined", symbol in ct, c, symbol)

    failures = [c for c in checks if c.status == "FAIL"]
    payload = {
        "schema": "uxb.library_source_gate.v1",
        "root": str(root),
        "status": "PASS" if not failures else "FAIL",
        "checks": [asdict(x) for x in checks],
        "summary": {"total": len(checks), "pass": len(checks) - len(failures), "fail": len(failures)},
    }
    (report_dir / "source_gate.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# uXBasic library source gate", "", f"Status: **{payload['status']}**", "",
             f"Checks: {len(checks)}; PASS: {len(checks)-len(failures)}; FAIL: {len(failures)}", ""]
    if failures:
        lines += ["## Failures", ""]
        for row in failures:
            lines.append(f"- `{row.name}` — `{row.path}` — {row.message}")
    else:
        lines.append("All static source-integrity checks passed.")
    (report_dir / "source_gate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"SOURCE_GATE status={payload['status']} checks={len(checks)} fail={len(failures)}")
    for row in failures[:25]:
        print(f"FAIL {row.name}: {row.path}: {row.message}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
