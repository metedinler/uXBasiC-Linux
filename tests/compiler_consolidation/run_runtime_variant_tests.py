"""Run each runtime variant in its own process, including real task callbacks."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def child(runtime):
    library = ctypes.CDLL(str(runtime))
    assert library.uxb_rt_init() == 1
    output = ctypes.create_string_buffer(128)
    library.uxb_rt_backend.argtypes = [ctypes.c_char_p, ctypes.c_int]
    assert library.uxb_rt_backend(output, len(output)) == 1
    callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.POINTER(ctypes.c_int), ctypes.c_void_p)

    @callback_type
    def callback(slot, value, result, context):
        result[0] = value * 3 + slot
        return 1

    library.uxb_task_register.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    library.uxb_task_set_callback.argtypes = [ctypes.c_int, callback_type, ctypes.c_void_p]
    library.uxb_parallel_run.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    assert library.uxb_task_register(3, 4, b"VARIANT_CALLBACK") == 1
    assert library.uxb_task_set_callback(3, callback, None) == 1
    result = ctypes.c_int()
    assert library.uxb_parallel_run(3, 4, ctypes.byref(result)) == 1
    assert result.value == 15
    library.__uxb_rt_val_f64.argtypes = [ctypes.c_char_p]
    library.__uxb_rt_val_f64.restype = ctypes.c_double
    parsed = library.__uxb_rt_val_f64(b"2.75")
    assert parsed == 2.75
    assert library.uxb_rt_shutdown() == 1
    print(json.dumps({"backend": output.value.decode(), "callback": result.value, "val_f64": parsed}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--full")
    parser.add_argument("--report")
    parser.add_argument("--child")
    args = parser.parse_args()
    if args.child:
        child(Path(args.child).resolve())
        return
    variants = [(name, Path(args.root).resolve() / name / "uxb_runtime.dll")
                for name in ("std", "libuv", "tbb", "auto")]
    variants.append(("full", Path(args.full).resolve()))
    expected = {"std": "std", "libuv": "libuv", "tbb": "tbb+std",
                "auto": "auto(libuv+tbb)", "full": "auto(libuv+tbb)"}
    results = []
    for name, runtime in variants:
        environment = os.environ.copy()
        environment["UXB_RT_BACKEND"] = "auto" if name == "full" else name
        process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", str(runtime)],
                                 cwd=runtime.parent, env=environment, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=30)
        row = {"test": name + "/callback_and_abi", "exit": process.returncode,
               "stdout": process.stdout, "stderr": process.stderr, "dll": str(runtime),
               "sha256": hashlib.sha256(runtime.read_bytes()).hexdigest(), "pass": False}
        try:
            row["values"] = json.loads(process.stdout)
            row["pass"] = process.returncode == 0 and row["values"]["backend"] == expected[name]
        except ValueError:
            pass
        results.append(row)
        code = ("import ctypes; dll=ctypes.CDLL(" + repr(str(runtime)) + "); "
                "fn=dll.__uxb_rt_host_call; fn.argtypes=[ctypes.c_char_p]; fn.restype=ctypes.c_int64; "
                "fn(b'UXB_TEST_MISSING_HOST'); print('UNREACHABLE')")
        process = subprocess.run([sys.executable, "-c", code], cwd=runtime.parent,
                                 env=environment, capture_output=True, text=True, timeout=30)
        results.append({"test": name + "/unbound_host", "exit": process.returncode,
                        "stdout": process.stdout, "stderr": process.stderr,
                        "pass": process.returncode == 1 and "UXB_RUNTIME_HOST_UNBOUND" in process.stderr
                        and "UNREACHABLE" not in process.stdout})
    report = Path(args.report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    for row in results:
        print(f"{'PASS' if row['pass'] else 'FAIL'} {row['test']}")
    passed = sum(row["pass"] for row in results)
    print(f"Toplam: {len(results)} PASS: {passed} FAIL: {len(results) - passed}")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
