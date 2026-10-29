"""Real package execution and fault injection; never modify installed DLLs."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SYMBOL = b'_ZSt15__get_once_callv\0'
DLLS = ('uxb_runtime.dll', 'libstdc++-6.dll', 'libgcc_s_seh-1.dll',
        'libwinpthread-1.dll', 'libuv-1.dll', 'libtbb12.dll')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, env):
    result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
    return dict(command=[str(x) for x in command], exit=result.returncode, stdout=result.stdout, stderr=result.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--baseline')
    parser.add_argument('--runtime-dir', help='Native runtime package; defaults to UXB_NATIVE_RUNTIME_DIR, then the compiler directory')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    runtime_dir = Path(args.runtime_dir or os.environ.get('UXB_NATIVE_RUNTIME_DIR') or compiler.parent).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.SetErrorMode(0x8003)  # Children inherit; negative loader cases cannot show a dialog.
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    rows, baseline_rows = [], []
    with tempfile.TemporaryDirectory(prefix='uxb_loader_contract_') as scratch:
        scratch = Path(scratch)
        valid, broken = scratch / 'valid', scratch / 'broken'
        for directory in (valid, broken):
            directory.mkdir()
            for name in DLLS + ('libuxb_runtime.dll.a',):
                shutil.copy2(runtime_dir / name, directory / name)
        bad = broken / 'libstdc++-6.dll'
        original = bad.read_bytes()
        assert original.count(SYMBOL) == 1, 'Expected exactly one real export to corrupt.'
        bad.write_bytes(original.replace(SYMBOL, b'_ZSt15__get_once_calLv\0', 1))
        fixture = Path(__file__).resolve().parent / 'proofs' / 'loader_output.uxb'
        for engine in ('x64', 'AST-x64'):
            valid_env = os.environ.copy()
            valid_env['UXB_NATIVE_RUNTIME_DIR'] = str(valid)
            def build(binary, label, environment):
                directory = scratch / label
                directory.mkdir()
                command = [binary, 'bld', fixture, '--out-root', directory]
                if engine == 'AST-x64':
                    command += ['--x64-mode', 'AST']
                return run(command, ROOT, environment)
            good = build(compiler, engine + '_valid with spaces', valid_env)
            match = re.search(r'build tamamlandi: (.+)', good['stdout'])
            if good['exit'] != 0 or not match:
                files = {str(path.relative_to(scratch)): path.read_text(encoding='utf-8', errors='replace')[:16000]
                         for path in scratch.rglob('*.txt') if path.stat().st_size < 262144}
                (output / 'early_failure.json').write_text(json.dumps(dict(build=good, files=files), indent=2))
                raise AssertionError(good)
            exe = Path(match[1].strip())
            isolated = valid_env.copy()
            isolated['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
            execution = run([exe], exe.parent, isolated)
            rows.append(dict(case='valid_package_system_only_PATH', engine=engine,
                             ok=execution['exit'] == 0 and execution['stdout'].strip() == '42',
                             build=good, execution=execution, binary_sha256=digest(exe),
                             dll_sha256={name: digest(exe.parent / name) for name in DLLS},
                             probe_sha256=digest(exe.parent / 'uxb_loader_probe.exe')))
            locked = exe.parent / 'libstdc++-6.dll'
            handle = kernel.CreateFileW(str(locked), 0x80000000, 1, None, 3, 0, None)
            assert handle not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
            try:
                relink = run(['cmd.exe', '/d', '/c', exe.parent / 'link_program.bat'], ROOT, valid_env)
            finally:
                kernel.CloseHandle(handle)
            rows.append(dict(case='failed_copy_is_build_failure', engine=engine,
                             ok=relink['exit'] != 0 and 'cannot copy native dependency: libstdc++-6.dll' in relink['stdout'], result=relink))
            broken_env = valid_env.copy()
            broken_env['UXB_NATIVE_RUNTIME_DIR'] = str(broken)
            failed = build(compiler, engine + '_missing_export', broken_env)
            rows.append(dict(case='missing_once_export_is_build_failure', engine=engine,
                             ok=failed['exit'] != 0 and 'native DLL package validation failed' in (failed['stdout'] + failed['stderr'])
                             and 'win32=127' in (failed['stdout'] + failed['stderr']),
                             build=failed, corrupted_dependency_sha256=digest(bad)))
            if args.baseline:
                old = build(Path(args.baseline).resolve(), engine + '_baseline', broken_env)
                match = re.search(r'build tamamlandi: (.+)', old['stdout'])
                execution = run([Path(match[1].strip())], ROOT, broken_env) if match else None
                baseline_rows.append(dict(engine=engine, build=old, execution=execution,
                                          reproduced=old['exit'] == 0 and execution is not None
                                          and execution['exit'] in (-1073741511, 3221225785)))
        for row in rows:
            print('PASS' if row['ok'] else 'FAIL', row['engine'], row['case'], flush=True)
    summary = dict(compiler=str(compiler), compiler_sha256=digest(compiler),
                   runtime_dir=str(runtime_dir), runtime_sha256={name: digest(runtime_dir / name) for name in DLLS},
                   total=len(rows), passed=sum(row['ok'] for row in rows), rows=rows, baseline=baseline_rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Total {summary['total']} PASS {summary['passed']}")
    return int(summary['passed'] != summary['total'] or any(not row['reproduced'] for row in baseline_rows))


if __name__ == '__main__':
    raise SystemExit(main())
