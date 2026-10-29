#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = [
    "tools/uxbdll/uxbdll.py",
    "tools/uxclazz/uxclazz.py",
    "runtime_ext/uxclz/include/uxclz.h",
    "runtime_ext/uxclz/src/uxclz.cpp",
    "runtime_ext/uxclz/tests/uxclz_smoke.cpp",
    "libsx/uxclz/uxclz.bas",
    "include/modules/uxclz.uxmh",
    "include/modules/uxclazz.uxmh",
    "docs/UXCLAZZ_UXBDLL_MIMARI_VE_KULLANIM_KILAVUZU_TR.md",
]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("RUN", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", action="store_true", help="compile and run uxclz C++ smoke test")
    args = parser.parse_args()

    for rel in EXPECTED:
        path = ROOT / rel
        if not path.exists():
            raise RuntimeError(f"missing patch file: {rel}")
        print("PASS file", rel)

    py_compile.compile(str(ROOT / "tools/uxbdll/uxbdll.py"), doraise=True)
    py_compile.compile(str(ROOT / "tools/uxclazz/uxclazz.py"), doraise=True)
    print("PASS Python syntax")

    with tempfile.TemporaryDirectory(prefix="uxclazz_verify_") as temp_raw:
        temp = Path(temp_raw)
        generated = temp / "fish_sample_generated.uxb"
        metadata = temp / "fish_sample.json"
        run([
            sys.executable, str(ROOT / "tools/uxclazz/uxclazz.py"),
            str(ROOT / "examples/uxclazz/fish_sample.uxclz"),
            "-o", str(generated), "--manifest", str(metadata),
        ])
        text = generated.read_text(encoding="utf-8")
        for marker in ["CLASS FishSample", "MAGIC HASH", "MAGIC CLONE", "METHOD ToJson", "CLASS Customer"]:
            if marker not in text:
                raise RuntimeError(f"generated UXClazz source missing marker: {marker}")
        data = json.loads(metadata.read_text(encoding="utf-8"))
        if len(data["classes"]) != 2:
            raise RuntimeError("UXClazz metadata class count mismatch")
        print("PASS UXClazz generation")

        fake_root = temp / "project"
        build_dir = fake_root / "build/test"
        (build_dir / "interop").mkdir(parents=True)
        (build_dir / "program.asm").write_text(
            "bits 64\nsection .text\nglobal UXTEST_ADD\nUXTEST_ADD:\n ret\n",
            encoding="utf-8",
        )
        (build_dir / "program_link_args.rsp").write_text('"obj/program.obj"\n', encoding="utf-8")
        (build_dir / "build_program.bat").write_text("@exit /b 0\n", encoding="utf-8")
        (build_dir / "interop/toolchain.env.bat").write_text("@set UXB_LINK_CMD=gcc\n", encoding="utf-8")
        manifest = fake_root / "test.uxdll.json"
        manifest.write_text(json.dumps({
            "name": "uxtest", "project_root": ".", "build_dir": "build/test",
            "output_dir": "dist", "exports": [{
                "public": "uxtest_add", "internal": "UXTEST_ADD", "return": "I32",
                "args": [{"name": "a", "type": "I32"}, {"name": "b", "type": "I32"}]
            }]
        }), encoding="utf-8")
        run([sys.executable, str(ROOT / "tools/uxbdll/uxbdll.py"), "--manifest", str(manifest), "--force"])
        if "uxtest_add=UXTEST_ADD" not in (build_dir / "uxtest.def").read_text(encoding="utf-8"):
            raise RuntimeError("uxbdll .def alias missing")
        wrapper = (fake_root / "libsx/uxtest/uxtest.bas").read_text(encoding="utf-8")
        if 'CALL(DLL, "uxtest.dll", "uxtest_add", I32' not in wrapper:
            raise RuntimeError("uxbdll wrapper generation failed")
        print("PASS uxbdll generation")

    if args.native:
        script = ROOT / "runtime_ext/uxclz/build_posix.sh"
        if os.name == "nt":
            run(["cmd.exe", "/d", "/c", str(ROOT / "runtime_ext/uxclz/build_uxclz.bat")], ROOT)
        elif shutil.which("g++"):
            run([str(script)], ROOT / "runtime_ext/uxclz")
        else:
            raise RuntimeError("--native requested but no g++ compiler was found")
        print("PASS uxclz native smoke")

    print("UXCLAZZ_UXBDLL_PATCH_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VERIFY_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
