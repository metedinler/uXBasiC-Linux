"""Record GCC's required clock symbols and verify a locally isolated C build.

Read-only outside the report directory and disposable scratch. No DLL replacement
or package update. pefile is used only for inspection, not by the compiler.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def inspect_pe(path):
    import pefile
    pe = pefile.PE(str(path), fast_load=True)
    pe.parse_data_directories(directories=[1, 0])
    imports = {}
    for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        names = [s.name.decode() for s in entry.imports
                 if s.name and b'clock_gettime' in s.name]
        if names:
            imports[entry.dll.decode()] = names
    exports = [s.name.decode() for s in
               getattr(getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None), 'symbols', [])
               if s.name and b'clock_gettime' in s.name]
    pe.close()
    return dict(path=str(path), size=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                clock_imports=imports, clock_exports=exports)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--msys-bin', default='C:/msys64/ucrt64/bin')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    msys = Path(args.msys_bin).resolve()
    bundled = root / 'tools/FreeBASIC-1.10.1-win64/bin/win64'
    gcc = msys / 'gcc.exe'
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join([str(msys), str(bundled), env.get('PATH', '')])
    # Failed toolchain probes must not display a loader dialog to the user.
    previous_error_mode = ctypes.windll.kernel32.SetErrorMode(0x8003)
    try:
        cc1 = subprocess.run([str(gcc), '-print-prog-name=cc1'], env=env,
                             capture_output=True, text=True, timeout=15, check=True)
        records = [inspect_pe(Path(cc1.stdout.strip())),
                   inspect_pe(msys / 'libwinpthread-1.dll'),
                   inspect_pe(bundled / 'libwinpthread-1.dll')]
        steps = []
        with tempfile.TemporaryDirectory(prefix='uxb_gcc_probe_') as scratch:
            scratch = Path(scratch)
            source = scratch / 'clock_dependency_probe.c'
            source.write_text('#include <stdio.h>\nint main(void){puts("GCC_CLOCK_OK");return 0;}\n')
            exe = scratch / 'probe.exe'
            for label, command in [('compile', [str(gcc), str(source), '-o', str(exe)]),
                                   ('execute', [str(exe)])]:
                proc = subprocess.run(command, cwd=scratch, env=env,
                                      capture_output=True, text=True, timeout=30)
                steps.append(dict(label=label, command=command, exit=proc.returncode,
                                  stdout=proc.stdout, stderr=proc.stderr))
                if proc.returncode:
                    break
        passed = (len(steps) == 2 and all(s['exit'] == 0 for s in steps)
                  and steps[-1]['stdout'].strip() == 'GCC_CLOCK_OK'
                  and 'clock_gettime64' in records[1]['clock_exports'])
        result = dict(schema='uxb.toolchain.clock_probe.v1', passed=passed,
                      dll_evidence=records, child_path_prefix=[str(msys), str(bundled)],
                      steps=steps, external_files_modified=False)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(('PASS' if passed else 'FAIL') + ': isolated GCC C build and execution')
        return 0 if passed else 1
    finally:
        ctypes.windll.kernel32.SetErrorMode(previous_error_mode)


if __name__ == '__main__':
    raise SystemExit(main())
