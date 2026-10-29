#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = [
    "src/parser/parser/parser_stmt_dispatch.fbs",
    "src/semantic/ffi_signature_binding.fbs",
    "src/codegen/x64/ffi_call_backend.fbs",
    "src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs",
    "src/runtime/ffi/runtime_ffi.fbs",
    "src/runtime/exec/exec_ffi_bridge10.fbs",
    "src/runtime/exec/exec_ffi_runtime.fbs",
    "src/interpreter/mir/mir_interp_ffi.fbs",
    "runtime_ext/uxffi/uxffi.c",
    "runtime_ext/uxffi/uxffi.h",
    "runtime_ext/uxjsruntime/uxjsrt.c",
    "runtime_ext/uxjsruntime/uxjsrt.h",
    "runtime/js/common/ux_runtime_core.js",
    "runtime/js/quickjs/ux_runtime_quickjs.js",
    "src/codegen/js/js_emitter.fbs",
    "src/codegen/js/runtime/js_runtime_embedded_generated.fbs",
    "tests/probes/ffi_ptr64_probe.uxb",
    "tests/probes/ffi_bridge_contract_smoke.uxb",
    "tests/libraries/uxjsruntime/generated_js_e2e.uxb",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    checks: list[dict[str, object]] = []

    def check(ok: bool, message: str) -> None:
        checks.append({"ok": bool(ok), "check": message})
        print(("[PASS] " if ok else "[FAIL] ") + message)

    for rel in REQUIRED:
        check((root / rel).is_file(), f"exists {rel}")

    ffi = (root / "runtime_ext/uxffi/uxffi.c").read_text(encoding="utf-8")
    hdr = (root / "runtime_ext/uxffi/uxffi.h").read_text(encoding="utf-8")
    parser_src = (root / "src/parser/parser/parser_stmt_dispatch.fbs").read_text(encoding="utf-8")
    semantic = (root / "src/semantic/ffi_signature_binding.fbs").read_text(encoding="utf-8")
    x64_gate = (root / "src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs").read_text(encoding="utf-8")
    x64_backend = (root / "src/codegen/x64/ffi_call_backend.fbs").read_text(encoding="utf-8")
    exec_ffi = (root / "src/runtime/exec/exec_ffi_runtime.fbs").read_text(encoding="utf-8")
    rt_ffi = (root / "src/runtime/ffi/runtime_ffi.fbs").read_text(encoding="utf-8")
    mir = (root / "src/interpreter/mir/mir_interp_ffi.fbs").read_text(encoding="utf-8")
    core = (root / "runtime/js/common/ux_runtime_core.js").read_text(encoding="utf-8")
    emitter = (root / "src/codegen/js/js_emitter.fbs").read_text(encoding="utf-8")
    embedded = (root / "src/codegen/js/runtime/js_runtime_embedded_generated.fbs").read_text(encoding="utf-8")

    check(
        "return 120" in ffi and "uxffi_max_args" in ffi and "uxffi_max_args" in hdr,
        "uxffi contract v120/ABI10",
    )
    check(
        "UXFFI_HANDLE_GENERATION_MASK" in ffi
        and "stale or invalid interpreter pointer token" in ffi
        and "if ((value >> 32) != 0u) return 0;" in ffi,
        "generation-tagged stale-token rejection without Win64 pointer misclassification",
    )
    check(
        "case UXFFI_STRPTR:" in ffi and "values_ptr[i] = resolve_handle(arg_u64[i])" in ffi,
        "PTR and STRPTR tokens are resolved inside the bridge",
    )
    check(
        "prepare_freebasic_runtime" in ffi
        and "known_consuming_closes" in ffi
        and '"_free", "_destroy", "_release", "_dispose"' in ffi
        and '"uxconfig_close"' in ffi,
        "FreeBASIC readiness and ownership-safe token release policy",
    )
    check(
        "unsafe direct fallback is disabled" in exec_ffi and "[UXB_FFI_DEBUG]" not in exec_ffi,
        "pointer fallback is fail-closed and debug stdout is removed",
    )
    check(
        'Case "I64"' in exec_ffi
        and "I64 requires integer/pointer-token argument" in exec_ffi
        and 'Case "U32"' in exec_ffi
        and 'Case "U64"' in exec_ffi,
        "AST execution validates I64/U64 tokens and keeps U32 separate",
    )
    check(
        "versionFn() < 120" in rt_ffi
        and "versionFn() < 120" in mir
        and "uxffi_max_args" in rt_ffi
        and "uxffi_max_args" in mir,
        "runtime service and MIR reject stale/incomplete uxffi",
    )
    check(
        'returnKind = UXB_RTFFI_KIND_PTR' in rt_ffi,
        "runtime service PTR return uses opaque token kind",
    )
    check(
        "result.handleId = 0" in rt_ffi
        and "result.ptrValue = 0" in rt_ffi
        and "result.handleId = 0" in mir
        and "result.ptrValue = 0" in mir,
        "bridge tokens are never exposed as process pointers",
    )
    check(
        'UCase(Trim(serviceId)) = RT_API_CALL' in rt_ffi and 'dllName &= ".DLL"' in rt_ffi,
        "runtime service normalizes CALL(API) module suffix",
    )
    check(
        'argTypes(i) = "I32"' in mir and 'argTypes(i) = "I32"' in rt_ffi,
        "MIR and runtime-service legacy arguments default to I32",
    )
    check("bridgeKindIndex" not in rt_ffi, "runtime_ffi argument-count mismatch is removed")
    check(
        '"CALL_DLL_STMT", "CALL_API_STMT"' in parser_src
        and "UXB_FFI_MAX_RUNTIME_ARGS As Integer = 10" in parser_src
        and "argument type-list count mismatch" in parser_src,
        "parser validates normalized DLL/API nodes, ABI10 arity and type-list count",
    )
    check(
        "Const UXB_FFI_MAX_ARGS As Integer = 10" in semantic,
        "semantic FFI signature capacity matches ABI10",
    )
    check(
        "If sig.argCount > 10 Then" in x64_gate
        and "unsupported ABI10 return type" in x64_gate
        and "unsupported ABI10 argument type" in x64_gate,
        "x64 MIR gate rejects unsupported ABI10 signatures",
    )
    check(
        'resolvedCallKind = IIf(nodeKind = "CALL_API_STMT", "API", "DLL")' in x64_backend
        and 'entryOut.dllName &= ".dll"' in x64_backend,
        "x64 backend recognizes normalized API nodes and appends .dll",
    )
    check(
        "exports: Object.create(null)" in core
        and "globalThis.uxb.exports = __uxbUser" in emitter,
        "globalThis.uxb stable export registry",
    )
    generated_lines = [
        '    s &= "' + line.replace('"', '""') + '" & Chr(10)'
        for line in core.splitlines()
    ]
    check(
        all(line in embedded for line in generated_lines),
        "embedded JS runtime matches core source",
    )

    duplicate_trees = [
        rel
        for rel in ("runtime_ext/runtime_ext", "libsx/libsx", "manifests/manifests")
        if (root / rel).exists()
    ]
    # Deliberately report-only: automatic deletion can destroy newer user edits.
    check(True, "duplicate-tree audit: " + (", ".join(duplicate_trees) if duplicate_trees else "none"))

    ok = all(item["ok"] for item in checks)
    report = {
        "schema": "uxb.deep.fix.static.v2",
        "status": "PASS" if ok else "FAIL",
        "checks": checks,
        "duplicateTrees": duplicate_trees,
    }
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
