"""Exercise native FFI return types, ten arguments and STRPTR after task adapter changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    fixture = root / 'tests/libraries/ffi_contract'
    gcc = Path('C:/msys64/ucrt64/bin/gcc.exe')
    with tempfile.TemporaryDirectory(prefix='uxb_task_ffi_') as temp:
        work = Path(temp)
        dll = work / 'uxb_ffi_contract_test.dll'
        command = [str(gcc), '-shared', '-O2', '-static-libgcc',
                   str(fixture / 'uxb_ffi_contract_test.c'), '-o', str(dll)]
        env = os.environ.copy()
        env['PATH'] = str(gcc.parent) + os.pathsep + env.get('PATH', '')
        try:
            build = subprocess.run(command, capture_output=True, text=True, timeout=90, env=env)
        except subprocess.TimeoutExpired as exc:
            output.mkdir(parents=True, exist_ok=False)
            (output / 'fixture_build_failure.json').write_text(json.dumps(dict(
                command=command, exit=None, timeout=True,
                stdout=str(exc.stdout or ''), stderr=str(exc.stderr or '')), indent=2))
            return 1
        if build.returncode:
            output.mkdir(parents=True, exist_ok=False)
            (output / 'fixture_build_failure.json').write_text(json.dumps(dict(
                command=command, exit=build.returncode, stdout=build.stdout, stderr=build.stderr), indent=2))
            return 1
        source = (fixture / 'ffi_contract_positive.uxb').read_text(encoding='utf-8-sig')
        (work / 'ffi_contract.uxb').write_text(source.replace('uxb_ffi_contract_test.dll', dll.as_posix()), encoding='utf-8')
        (work / 'cases.json').write_text(json.dumps({'ffi_contract': dict(
            output='UXB_FFI_CONTRACT_PASS', engines=['x64', 'AST-x64'])}), encoding='utf-8')
        result = subprocess.run([sys.executable, str(root / 'tests/turkce_ad/run_tests.py'),
                                 '--uxb', str(compiler), '--test-root', str(work),
                                 '--output', str(output), '--jobs', '2', '--temp-builds'], cwd=root)
        (output / 'fixture.json').write_text(json.dumps(dict(
            command=command, exit=build.returncode,
            source_sha256=hashlib.sha256((fixture / 'uxb_ffi_contract_test.c').read_bytes()).hexdigest(),
            dll_sha256=hashlib.sha256(dll.read_bytes()).hexdigest()), indent=2))
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
