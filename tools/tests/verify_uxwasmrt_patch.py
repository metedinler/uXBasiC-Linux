#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    checks: list[dict[str, object]] = []

    def check(name: str, ok: object, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    files = [
        "runtime_ext/uxwasmrt/uxwasmrt.c",
        "runtime_ext/uxwasmrt/uxwasmrt.h",
        "runtime_ext/uxwasmrt/uxwasmrt.def",
        "runtime_ext/uxwasmrt/wasm_c_api_min.h",
        "runtime_ext/uxwasmrt/wasm.lock.json",
        "runtime_ext/uxwasmrt/build_uxwasmrt.ps1",
        "runtime_ext/uxwasmrt/fetch_wasm_deps.ps1",
        "libsx/uxwasmrt/uxwasmrt.bas",
        "include/modules/uxwasmrt.uxmh",
        "runtime/browser/ux_wasm_bridge.js",
        "tests/libraries/uxwasmrt/test_uxwasmrt.py",
        "tests/libraries/uxwasmrt/verify_distribution.py",
        "tests/libraries/uxwasmrt/reference_26_07/add.wasm",
        "tools/package_uxwasm_distribution.ps1",
        "run_uxwasmrt_gate.ps1",
    ]
    for relative in files:
        check("file:" + relative, (root / relative).is_file())

    required_for_content = [root / relative for relative in files]
    if any(not path.is_file() for path in required_for_content):
        report = {
            "schema": "uxb.uxwasmrt.static.v2",
            "status": "FAIL",
            "checks": checks,
            "pass": sum(1 for item in checks if item["ok"]),
            "fail": sum(1 for item in checks if not item["ok"]),
        }
        if args.json_out:
            output = pathlib.Path(args.json_out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    c_source = (root / "runtime_ext/uxwasmrt/uxwasmrt.c").read_text(encoding="utf-8")
    public_header = (root / "runtime_ext/uxwasmrt/uxwasmrt.h").read_text(encoding="utf-8")
    browser = (root / "runtime/browser/ux_wasm_bridge.js").read_text(encoding="utf-8")
    wrapper = (root / "libsx/uxwasmrt/uxwasmrt.bas").read_text(encoding="utf-8")
    lock = json.loads((root / "runtime_ext/uxwasmrt/wasm.lock.json").read_text(encoding="utf-8"))
    imports_source = (root / "src/codegen/wasm/wasm_host_imports.fbs").read_text(encoding="utf-8")
    emitter_source = (root / "src/codegen/wasm/wasm_emitter.fbs").read_text(encoding="utf-8")

    check("api-version-100", "UXWASMRT_API_VERSION 100" in public_header)
    check(
        "no-raw-pointer-public-api",
        not re.search(r"UXWASMRT_API[^;]*(?:void\s*\*|uintptr_t|uint64_t)", public_header),
    )
    check("generation-handle", "generation" in c_source and "decode_handle" in c_source)
    check("thread-owner-gate", "owner_thread" in c_source and "different thread" in c_source)
    check("module-size-limit", "UXWASMRT_MAX_MODULE_BYTES" in c_source and "64 MiB" in c_source)
    check("import-allowlist", "Unsupported WASM import" in c_source and "host_call4" in c_source)
    check("fail-closed-host", "host import is not bound" in c_source)
    check("deterministic-host-rng", "host_rng_next" in c_source and "nextRandomI32" in browser)
    check("checked-host-math", "host_double_to_i32" in c_source and "checkedI32" in browser)
    check("browser-host-call4", "host_call4" in browser)
    check("browser-globalThis-uxb", "globalThis.uxb" in browser)
    check("browser-provider", "browser-webassembly/core-i32" in browser)
    check("native-provider", "wasmtime-wasm-c-api/core-i32" in c_source)
    check("wasmtime-pin", lock.get("wasmtime", {}).get("tag") == "v45.0.3")
    check("wabt-pin", lock.get("wabt", {}).get("tag") == "1.0.41")
    check("compiler-host-call4", '"host_call4"' in imports_source)
    check("compiler-print-i32", '"print_i32"' in imports_source)
    check("compiler-print-f64", '"print_f64"' in imports_source)
    check("current-emitter-string-fail-close", "string linear-memory lowering is not implemented" in emitter_source)
    check("wrapper-i32-handles", "sessionHandle AS I32" in wrapper and " AS U64" not in wrapper)
    check("wrapper-max-call-arity-four", "WasmCallI32_4" in wrapper and "WasmCallI32_5" not in wrapper)
    check("quickjs-not-in-wasm-provider", "quickjs" not in c_source.lower() and "quickjs" not in browser.lower())

    failures = [item for item in checks if not item["ok"]]
    report = {
        "schema": "uxb.uxwasmrt.static.v2",
        "status": "PASS" if not failures else "FAIL",
        "profile": "core-i32",
        "checks": checks,
        "pass": len(checks) - len(failures),
        "fail": len(failures),
    }
    if args.json_out:
        output = pathlib.Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
