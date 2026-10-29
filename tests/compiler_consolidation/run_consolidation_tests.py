"""Run real compiler/native processes, compare exact output and preserve JSON evidence."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import time
import shutil
import hashlib
import tempfile
from contextlib import nullcontext

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)

ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
EXPECTED = {
    "ffi_optional_metadata": "-1\n7\n4",
    "magic_dispatch_values": "11\n5\n[8]\n[8]\n1\n2026\ntext",
    "type_prefix_names": "7\n7\n1",
    "enum_arrays": "-128\n127\n-128\n127\n18446744073709551615\n18446744073709551615",
    "enum_casts": "-128\n-1\n-1\n18446744073709551615\n-1",
    "continue_finally_scope": "1",
    "numeric_conditions": "4\n3",
    "continue_finally_transfer": "1\n2\n2",
    "static_routine_scopes": "1\n2\n13",
    "mid_class_receiver": "aXYdef\nother\n1\naXZZef",
    "static_tasks": "901\n1\n800",
    "continue_collections": "1\n3\n11\n13\na\nç\n2",
    "float_integer_casts": "2\n-2\n127\n-1\n254\n-32768\n3000000000\n9223372036854775808\n3\n2\n4\n-3\n-2\n-3",
    "mid_assignment": "aXYdef\naXYde1\naXYde1\naQYde1\naQcdef\naaQdef\naXYdef\naXYdef\n4",
    "mid_assignment_byref": "abZZef",
    "static_locals": "11\n12\n1\n101\n102\n4\n6\nab\nabb\n6\n8",
    "enum_named": "1\n1\n-128\n127\n4294967295\n4\n1\n4\n18446744073709551615",
    "continue_loops": "1\n2\n4\n5\n13\n11\n23\n33\n44\n51\n53\n61\n63",
    "continue_finally": "1\n11\n2\n12\n30\n40\n50",
    "continue_lock": "3",
    "instr_start": "1\n4\n7\n0",
    "file_eof_lof": "0\n-1\n3\n-1",
    "string_repeat": "aaa\nAAA\n0\nxx",
    "radix_formats": "FF\n10\n101\n0\n0\n100000000",
    "radix_literals": "255\n15\n5\n18\n4294967295",
    "select_cases": "range\nreversed\nstring\nordered",
    "select_numeric_ranges": "float\nunsigned\nwide",
    "select_mixed_snapshot": "snapshot\n100\nmixed\nunsigned-is",
    "file_read_lines": "[a b]\n[]\n[ c ]\n3",
    "large_local_frame": "20",
    "callee_saved_callback": "0",
    "callee_saved_numeric_callback": "0",
    "dim_reentry": "1a\n2a\n3a",
    "forward_declarations": "10\n7",
    "forward_plain": "8\n7",
    "deftype_ranges": "12\n9",
    "print_zones": "1             2             3\nabcdefghijklmn              x\nab            c\nd",
    "float_text_rounding": "3.333333333333333\n0.1428571428571428\n3.333333333333333\n0.3333333",
    "property_typed": "3\n7",
    "stable_cells_growth": "254\n255\n256\n1023",
    "stable_cells_byref_pointer": "23\n23\n23",
    "literal_integer_ranges": "-128\n127\n255\n-32768\n32767\n65535\n-2147483648\n4294967295\n-9223372036854775808\n9223372036854775807\n18446744073709551615\n-127\n254\n-1",
    "return_declared_types": "-128\n7\n0.3333333\n2147483648\ntyped",
    "inline_if_one_branch": "1\n11",
    "literal_small_web": "-128\n255\n-32768\n65535\n127\n-1\n0",
    "iff_lazy_values": "1\n2\n2\nyes\nright\n5\n2.5\n7\n9\n-1\n-2",
    "iff_lazy_web": "1\n2\n2\n7\n-1\n-2",
    "typed_builtin_arithmetic": "9\n9\n2.5\n6",
}
EXPECTED_ERROR = {
    "enum_outside_base": "enum: value out of range for TYPE_I8",
    "mid_assignment_bad_target": "assign: left side is not writable: CALL_EXPR",
    "enum_identity_mismatch": "assignment requires explicit cast SHAPE to PALETTE",
    "continue_outside_loop": "CONTINUE used outside matching loop",
    "forward_decl_bad_param": "semantic: declaration signature mismatch",
    "forward_decl_bad_return": "semantic: declaration signature mismatch",
    "forward_decl_duplicate_definition": "semantic: duplicate overload signature",
    "literal_outside_i8": "integer literal out of range for TYPE_I8",
    "literal_negative_u8": "integer literal out of range for TYPE_U8",
    "variable_narrowing_requires_cast": "assignment requires explicit cast TYPE_I32 to TYPE_I8",
    "return_float_requires_cast": "return: type: assignment requires explicit cast TYPE_F64 to TYPE_I32",
    "return_variable_requires_cast": "return: type: assignment requires explicit cast TYPE_I32 to TYPE_I8",
    "return_wrong_type": "return: type: assignment cannot convert TYPE_STRING to TYPE_I32",
    "iff_wrong_arity": "UXB_IFF_ARGUMENT_COUNT",
}
TEST_ENGINES = {"callee_saved_callback": ["x64"],
                "static_routine_scopes": ["AST", "MIR", "x64"],
                "static_tasks": ["AST", "MIR", "x64"],
                "continue_collections": ["AST", "MIR", "x64"],
                "mid_assignment_byref": ["AST", "MIR", "x64"],
                "continue_loops": ["AST", "MIR", "x64", "AST-x64", "JS", "WASM"],
                "continue_lock": ["AST", "MIR", "x64"],
                "literal_small_web": ["AST", "MIR", "x64", "AST-x64", "JS", "WASM"],
                "iff_lazy_web": ["AST", "MIR", "x64", "AST-x64", "JS", "WASM"],
                "stable_cells_growth": ["AST", "MIR"],
                "stable_cells_byref_pointer": ["AST", "MIR", "x64"],
                # Legacy rejects every BYREF routine explicitly (S-167-L).
                "forward_declarations": ["AST", "MIR", "x64"],
                "callee_saved_numeric_callback": ["x64", "AST-x64"],
                "large_local_frame": ["x64", "AST-x64"]}


def norm(text):
    return "\n".join(line.rstrip() for line in text.replace("\r", "").splitlines()
                     if line.strip() and not line.startswith(("INFO:", "WARN:")))


def invoke(argv, cwd, seconds=120):
    started = time.monotonic()
    try:
        p = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=seconds)
        return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                "seconds": round(time.monotonic() - started, 3)}
    except subprocess.TimeoutExpired as exc:
        return {"exit": -999, "stdout": str(exc.stdout or ""), "stderr": "TIMEOUT",
                "seconds": round(time.monotonic() - started, 3)}


def build_probe(directory):
    directory.mkdir(parents=True, exist_ok=True)
    dll = directory / "callee_probe.dll"
    gcc = Path("C:/msys64/ucrt64/bin/gcc.exe")
    if not gcc.exists():
        gcc = Path(shutil.which("gcc") or "gcc")
    environment = os.environ.copy()
    environment["PATH"] = str(gcc.parent) + os.pathsep + environment.get("PATH", "")
    built = subprocess.run([str(gcc), "-shared", str(TESTS / "callee_probe.S"),
                            str(TESTS / "callee_probe.def"), "-o", str(dll)],
                           cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60)
    if built.returncode != 0 or not dll.exists():
        raise RuntimeError("Native callback probe build failed: " + built.stderr)
    return dll.resolve()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", default=str(ROOT / "bin" / "uxb.exe"))
    ap.add_argument("--report", required=True)
    ap.add_argument("--runtime-dir")
    artifacts = ap.add_mutually_exclusive_group()
    artifacts.add_argument("--temp-builds", dest="temp_builds", action="store_true", default=True,
                           help="Default: remove compiler/program artifacts after preserving JSON evidence and hashes.")
    artifacts.add_argument("--keep-builds", dest="temp_builds", action="store_false",
                           help="Keep diagnostic binaries under build/test_outputs, never in reports.")
    ap.add_argument("--only", nargs="*", default=list(EXPECTED) + list(EXPECTED_ERROR))
    ap.add_argument("--engines", nargs="*")
    args = ap.parse_args()
    compiler = Path(args.compiler).resolve()
    compiler_hash = hashlib.sha256(compiler.read_bytes()).hexdigest()
    report = Path(args.report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    runs = report.parent / (report.stem + "_runs")
    runs.mkdir(parents=True, exist_ok=True)
    run_key = hashlib.sha256(str(report).encode("utf-8")).hexdigest()[:16]
    kept_root = ROOT / "build" / "test_outputs" / "compiler_consolidation" / run_key
    generated_tests = TESTS / "generated" / run_key
    probe_scratch = tempfile.TemporaryDirectory(prefix="uxb_consolidation_probe_") if args.temp_builds else None
    results = []
    probe = None
    for name in args.only:
        for engine in args.engines or TEST_ENGINES.get(name, ["AST", "MIR", "x64", "AST-x64"]):
            persistent_case = kept_root / (name + "_" + engine)
            context = tempfile.TemporaryDirectory(prefix="uxb_consolidation_") if args.temp_builds else nullcontext(str(persistent_case))
            with context as case_location:
                case_dir = Path(case_location)
                case_dir.mkdir(parents=True, exist_ok=True)
                source = TESTS / (name + ".uxb")
                if name.startswith("callee_saved_"):
                    if probe is None:
                        probe_root = Path(probe_scratch.name) if probe_scratch else kept_root / "probe_support"
                        probe = build_probe(probe_root)
                    generated_tests.mkdir(parents=True, exist_ok=True)
                    rendered = generated_tests / (name + "_" + engine + ".uxb")
                    rendered.write_text(source.read_text(encoding="utf-8").replace(
                        '"callee_probe.dll"', '"' + probe.as_posix() + '"'), encoding="utf-8")
                    source = rendered
                if engine in ("AST", "MIR"):
                    extra = ["--interpreter-backend", "MIR"] if engine == "MIR" else []
                    result = invoke([compiler, "run", source, *extra, "--out-root", case_dir], case_dir)
                elif engine in ("JS", "WASM"):
                    node = shutil.which("node") or "node"
                    if engine == "JS":
                        generated = case_dir / "program.js"
                        build = invoke([compiler, "jsw", source, "--js-out", generated,
                                        "--out-root", case_dir], ROOT)
                    else:
                        wasm = case_dir / "program.wasm"
                        generated = case_dir / "run_wasm.js"
                        wat2wasm = ROOT / "tools" / "wabt" / "bin" / "wat2wasm.exe"
                        build = invoke([compiler, "wat", source, "--emit-wasm", "--wasm-out", wasm,
                                        "--wat-out", case_dir / "program.wat", "--out-root", case_dir,
                                        "--wat2wasm=" + str(wat2wasm)], ROOT)
                    result = invoke([node, generated], case_dir, 30) if build["exit"] == 0 and generated.exists() else build.copy()
                    result["build"] = build
                else:
                    exe = case_dir / "program.exe"
                    extra = ["--x64-mode", "AST"] if engine == "AST-x64" else []
                    build = invoke([compiler, "bld", source, *extra, "--out-root", case_dir, "-o", exe], ROOT,
                               420 if name in ("large_local_frame", "stable_cells_byref_pointer") else 120)
                    match = re.search(r"build tamamlandi: (.+)", build["stdout"])
                    produced = Path(match[1].strip()) if match else exe
                    if args.runtime_dir and produced.exists():
                        for dll in Path(args.runtime_dir).glob("*.dll"):
                            shutil.copy2(dll, produced.parent / dll.name)
                    result = invoke([produced], case_dir, 30) if build["exit"] == 0 and produced.exists() else build.copy()
                    result["build"] = build
                actual_text = result["stdout"] + result["stderr"]
                if name in EXPECTED_ERROR:
                    result.update(test=name, engine=engine, expected_error=EXPECTED_ERROR[name])
                    result["pass"] = result["exit"] not in (0, -999) and EXPECTED_ERROR[name] in actual_text
                else:
                    result.update(test=name, engine=engine, expected=EXPECTED[name])
                    result["pass"] = result["exit"] == 0 and norm(actual_text) == EXPECTED[name]
                result["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
                result["source_path"] = str(source)
                result["artifact_root"] = str(case_dir)
                result["evidence_root"] = str(runs)
                result["runner_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                if probe is not None:
                    result["probe_sha256"] = hashlib.sha256(probe.read_bytes()).hexdigest()
                result["temporary_build_artifacts"] = args.temp_builds
                artifacts = [path for path in case_dir.rglob("*") if path.is_file() and path.suffix in (".exe", ".dll", ".wasm", ".js")]
                result["artifact_sha256"] = {str(path.relative_to(case_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts}
                if args.temp_builds and not result["pass"]:
                    result["failure_files"] = {str(path.relative_to(case_dir)): path.read_text(encoding="utf-8", errors="replace")[:24000]
                                               for path in case_dir.rglob("*.asm")}
                results.append(result)
                # A full disk must not truncate the last valid evidence file.
                pending = report.with_suffix(report.suffix + ".pending")
                pending.write_text(json.dumps({"compiler": str(compiler), "compiler_sha256": compiler_hash, "temporary_build_artifacts": args.temp_builds, "results": results}, indent=2), encoding="utf-8")
                os.replace(pending, report)
                print(f"{'PASS' if result['pass'] else 'FAIL'} {engine}/{name} exit={result['exit']}", flush=True)
    passed = sum(x["pass"] for x in results)
    if probe_scratch:
        probe_scratch.cleanup()
    print(f"Toplam: {len(results)} PASS: {passed} FAIL: {len(results)-passed}")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
