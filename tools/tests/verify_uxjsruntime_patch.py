#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REQUIRED = [
    "runtime_ext/uxjsruntime/uxjsrt.c",
    "runtime_ext/uxjsruntime/uxjsrt.h",
    "runtime_ext/uxjsruntime/quickjs.lock.json",
    "runtime/js/common/ux_runtime_core.js",
    "runtime/js/quickjs/ux_runtime_quickjs.js",
    "src/codegen/js/runtime/js_runtime_writer.fbs",
    "src/codegen/js/runtime/js_runtime_embedded_generated.fbs",
    "src/codegen/js/js_mir_runtime_emit.fbs",
    "src/codegen/js/js_emitter.fbs",
    "libsx/uxjsruntime/uxjsruntime.bas",
    "include/modules/uxjsruntime.uxmh",
    "tests/libraries/uxjsruntime/smoke.js",
]


def check(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        print(f"[PASS] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    failures: list[str] = []
    for rel in REQUIRED:
        check((root / rel).is_file(), f"exists: {rel}", failures)
    core = (root / "runtime/js/common/ux_runtime_core.js").read_text(encoding="utf-8")
    provider = (root / "runtime/js/quickjs/ux_runtime_quickjs.js").read_text(encoding="utf-8")
    c = (root / "runtime_ext/uxjsruntime/uxjsrt.c").read_text(encoding="utf-8")
    wrapper = (root / "libsx/uxjsruntime/uxjsruntime.bas").read_text(encoding="utf-8")
    preamble = (root / "src/codegen/js/js_mir_runtime_emit.fbs").read_text(encoding="utf-8")
    emitter = (root / "src/codegen/js/js_emitter.fbs").read_text(encoding="utf-8")
    check("globalThis.uxb" in core, "globalThis.uxb contract", failures)
    check("uxb.compat" in core and "globalObject.ux = compat" in core, "migration compatibility bridge", failures)
    check("get wasm()" in core and "set wasm(value)" in core, "existing JS/WASM bridge compatibility retained without adding WASM runtime", failures)
    check("__uxbNative" in provider, "QuickJS native provider binding", failures)
    check("const uxb = globalThis.uxb" in preamble, "generated preamble binds globalThis.uxb", failures)
    check("autoRun !== false" in emitter and "globalThis.uxbMain" in emitter, "QuickJS load does not auto-run generated entry twice", failures)
    check("uxb.autoRun = false" in provider, "QuickJS provider selects explicit host invocation", failures)
    check("uint64_t UXJSRT_CALL uxjs_runtime_create" not in c, "FFI handles do not expose raw U64 pointers", failures)
    check("int32_t UXJSRT_CALL uxjs_runtime_create" in c, "I32 opaque runtime handles", failures)
    check("JS_SetMemoryLimit" in c and "JS_SetInterruptHandler" in c, "resource limit hooks", failures)
    check("JS_ExecutePendingJob" in c, "pending job queue support", failures)
    check("uxjs_call_json_await" in c, "Promise-aware call path", failures)
    check('"I32,STRPTR,STRPTR,I32"' in wrapper, "uXBasic ABI10 wrapper signatures", failures)
    lock = json.loads((root / "runtime_ext/uxjsruntime/quickjs.lock.json").read_text())
    check(lock.get("version") == "2026-06-04", "QuickJS version pinned", failures)
    check(lock.get("sha256") == "b376e839b322978313d929fd20663b11ba58b75df5a46c126dd19ea2fa70ad2a", "QuickJS archive hash pinned", failures)

    node = shutil.which("node")
    if node:
        for rel in ["runtime/js/common/ux_runtime_core.js", "runtime/js/quickjs/ux_runtime_quickjs.js", "tests/libraries/uxjsruntime/smoke.js"]:
            proc = subprocess.run([node, "--check", str(root / rel)], capture_output=True, text=True)
            check(proc.returncode == 0, f"JavaScript syntax: {rel}", failures)
            if proc.returncode:
                print(proc.stderr)
    else:
        print("[SKIP] node --check unavailable")

    source_hash = hashlib.sha256(core.encode()).hexdigest()
    generated = (root / "src/codegen/js/runtime/js_runtime_embedded_generated.fbs").read_text(encoding="utf-8")
    check("GENERATED FILE" in generated and "globalThis.uxb" in generated, "embedded runtime generated from contract", failures)

    report = {
        "schema": "uxb.uxjsruntime.static.verify.v1",
        "status": "PASS" if not failures else "FAIL",
        "failureCount": len(failures),
        "failures": failures,
        "coreRuntimeSha256": source_hash,
    }
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
