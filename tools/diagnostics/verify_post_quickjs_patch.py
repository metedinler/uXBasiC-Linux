from __future__ import annotations

import argparse
import json
import pathlib
import re

REQUIRED_VERSION = 131


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    required_files = [
        "runtime_ext/uxffi/uxffi.c",
        "runtime_ext/uxffi/uxffi.h",
        "runtime_ext/uxffi/build_uxffi_dll.bat",
        "src/runtime/exec/exec_ffi_bridge10.fbs",
        "src/runtime/exec/exec_ffi_runtime.fbs",
        "src/runtime/ffi/runtime_ffi.fbs",
        "src/interpreter/mir/mir_interp_ffi.fbs",
        "tests/libraries/ffi_final/ffi_freebasic_roundtrip.uxb",
        "tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py",
        "tests/libraries/uxjsruntime/generated_e2e.uxb",
        "tests/libraries/uxjsruntime/test_generated_js_e2e.py",
    ]
    missing = [path for path in required_files if not (root / path).is_file()]
    check("required_patch_files", not missing, ", ".join(missing))
    if missing:
        report = {"schema": "uxb.post-quickjs-static.v2", "status": "FAIL", "checks": checks}
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.json_out:
            out = pathlib.Path(args.json_out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 1

    c = (root / "runtime_ext/uxffi/uxffi.c").read_text(encoding="utf-8")
    h = (root / "runtime_ext/uxffi/uxffi.h").read_text(encoding="utf-8")
    build = (root / "runtime_ext/uxffi/build_uxffi_dll.bat").read_text(encoding="utf-8")
    bridge = (root / "src/runtime/exec/exec_ffi_bridge10.fbs").read_text(encoding="utf-8")
    executor = (root / "src/runtime/exec/exec_ffi_runtime.fbs").read_text(encoding="utf-8")
    runtime = (root / "src/runtime/ffi/runtime_ffi.fbs").read_text(encoding="utf-8")
    mir = (root / "src/interpreter/mir/mir_interp_ffi.fbs").read_text(encoding="utf-8")
    native_test = (root / "tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py").read_text(encoding="utf-8")
    js_test = (root / "tests/libraries/uxjsruntime/test_generated_js_e2e.py").read_text(encoding="utf-8")

    check("uxffi_api_131", "UXFFI_API_VERSION 131" in h and "return UXFFI_API_VERSION" in c)
    check("uxffi_abi10_export", "UXFFI_MAX_ARGS 10" in h and "uxffi_max_args(void)" in c)
    check(
        "uxffi_complete_exports",
        all(name in h and name in c for name in [
            "uxffi_version", "uxffi_max_args", "uxffi_invoke10", "uxffi_string_length",
            "uxffi_copy_string", "uxffi_release_handle", "uxffi_clear_handles", "uxffi_shutdown",
        ]),
    )
    check("build_export_gate", all(name in build for name in ["uxffi_string_length", "uxffi_max_args", "pei-x86-64", "-Werror"]))
    check("freebasic_warmup", "uxfb_runtime_ready" in c and "is_required_freebasic_module" in c and "uxconfig.dll" in c)
    check("generation_checked_tokens", all(token in c for token in ["UXFFI_HANDLE_GENERATION_MASK", "decode_token", "next_generation", "stale or invalid pointer handle token"]))
    check("owned_strptr_snapshot", all(token in c for token in ["duplicate_bounded_string", "ReadProcessMemory", "VirtualQuery", "store_handle(copy, 1)"]))
    check("freebasic_calls_serialized", "return_kind == UXFFI_STRPTR || is_required_freebasic_module(dll_name)" in c)
    check("exact_strptr_protocol", "uxffi_string_length" in c and "out_capacity > length" in c and "length + 1u" in c)
    check("copy_failure_does_not_consume", c.find("if (!ok) return 0;") < c.find("uxffi_release_handle(token);"))
    check("close_consumes_first_ptr_token", "release_like_symbol" in c and "break;" in c[c.find("if (release_like_symbol"):])
    check("null_strptr_is_empty", "if (token == 0u) return 1;" in c and "If tokenValue = 0 Then Return 1" in bridge)

    for name, text, constant in [
        ("executor_version_gate", bridge, "UXFFI_REQUIRED_VERSION As Long = 131"),
        ("runtime_version_gate", runtime, "UXB_RTFFI_REQUIRED_VERSION As Long = 131"),
        ("mir_version_gate", mir, "UXB_MIRFFI_REQUIRED_VERSION As Long = 131"),
    ]:
        check(name, constant in text and "uxffi_max_args" in text)

    check("executor_fail_closed", "Typed ABI10 execution is fail-closed" in bridge and "ABI10 requires bin\\uxffi.dll API 131" in bridge)
    check("all_consumers_exact_string_copy", all("uxffi_string_length" in text and "CAllocate(requiredBytes)" in text for text in [bridge, runtime, mir]))
    check("runtime_ptr_return_kind", 'Case "PTR"\n        returnKind = UXB_RTFFI_KIND_PTR' in runtime)
    check("runtime_token_not_raw_pointer", "result.ptrValue = 0" in runtime)
    check("runtime_resolve_arg_arity_fix", "bridgeKindIndex" not in runtime and "UXBRuntimeFfiResolveArg(args.values(argStart + i), argTypes(i), keepAlive(i), argKinds(i), argU64(i), argF64(i), errText)" in runtime)
    check("runtime_unique_winapi_aliases", all(name in runtime for name in ["UXBRuntimeFfiLoadLibraryA", "UXBRuntimeFfiGetProcAddress", "UXBRuntimeFfiGetModuleFileNameA", "UXBRuntimeFfiFreeLibrary"]))
    check("runtime_legacy_i32_contract", "legacy CALL(DLL/API) records" in runtime and 'argTypes(i) = "I32"' in runtime)
    check("mir_legacy_i32_contract", "Legacy calls without an explicit ABI10 type list are integer calls" in mir and 'argTypes(i) = "I32"' in mir)
    check("robust_loader_parity", all("GetModuleFileNameA" in text and "dist\\runtime_ext\\uxffi.dll" in text for text in [bridge, runtime, mir]))
    check("executor_u32_rejects_ptr_token", 'Case "U32"' in executor and 'U32 requires a 32-bit integer argument' in executor)
    check("executor_wide_arg_uses_u64", "u64Out = ExecValueToU64(iv)" in executor)
    check("debug_print_removed", "[UXB_FFI_DEBUG]" not in executor)
    check("native_test_api_131", "REQUIRED_UXFFI_VERSION = 131" in native_test)
    check("native_test_long_string", "12000" in native_test and "undersized buffer" in native_test and "generationChanged" in native_test)
    check("generated_js_real_emitter_e2e", "--emit-js" in js_test and "globalThis.uxbMain" in js_test and "globalThis.uxb" in js_test and "uxjs_call_json_await" in js_test)
    check(
        "nested_stale_tree_absent",
        not (root / "runtime_ext/runtime_ext").exists() and not (root / "libsx/libsx").exists(),
        "Run Move-StaleNestedTrees.ps1 -Apply if this fails",
    )

    # The current root uxconfig source already contains the necessary defensive contract.
    config_source = root / "runtime_ext/uxconfig/uxconfig.bas"
    if config_source.is_file():
        config = config_source.read_text(encoding="utf-8", errors="replace")
        check("uxconfig_null_guards_present", "if h=0 then return" in config.lower())
        check("uxconfig_fixed_return_buffer", "g_text as zstring * 65536" in config.lower())
        check("uxconfig_fb_ready_include", "fb_common/uxb_fb_common.bi" in config.replace("\\", "/"))

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    report = {"schema": "uxb.post-quickjs-static.v2", "status": status, "checks": checks}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        out = pathlib.Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
