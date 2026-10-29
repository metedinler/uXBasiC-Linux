"""Serial alternating baseline/candidate measurements with raw timing evidence."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--no-trace', action='store_true')
    parser.add_argument('--only', choices=['straight_240', 'loop_100', 'loop_10000'])
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    compilers = {name: Path(getattr(args, name)).resolve() for name in ('baseline', 'candidate')}
    sources = {'straight_240': ('DIM total AS I64 = 0\n' + 'total = total + 1\n' * 240 + 'PRINT total\n', '240'),
               'loop_100': ('DIM total AS I64 = 0\nDIM i AS I32\nFOR i = 1 TO 100\ntotal = total + i\nNEXT\nPRINT total\n', '5050'),
               'loop_10000': ('DIM total AS I64 = 0\nDIM i AS I32\nFOR i = 1 TO 10000\ntotal = total + i\nNEXT\nPRINT total\n', '50005000')}
    ctypes.windll.kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    rows = []
    for name, (text, expected) in sources.items():
        if args.only and name != args.only:
            continue
        source = output / (name + '.uxb')
        source.write_text(text, encoding='utf-8')
        for repeat in range(args.repeat):
            order = list(compilers) if repeat % 2 == 0 else list(reversed(compilers))
            for variant in order:
                work = output / f'{name}_{repeat}_{variant}'
                work.mkdir()
                with tempfile.TemporaryDirectory(prefix='uxb_mir_measure_') as scratch:
                    timing = work / 'timing.json'
                    command = [str(compilers[variant]), 'run', str(source), '--interpreter-backend', 'MIR',
                               '--out-root', str(Path(scratch) / 'out')]
                    if not args.no_trace:
                        command += ['--layer-timing-json-out', str(timing)]
                    started = time.perf_counter()
                    proc = subprocess.Popen(command, cwd=scratch, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate(timeout=180)
                    elapsed = time.perf_counter() - started
                    creation, exit_time, kernel, user = (wintypes.FILETIME() for _ in range(4))
                    ok = ctypes.windll.kernel32.GetProcessTimes(int(proc._handle), ctypes.byref(creation),
                         ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user))
                    cpu = sum((v.dwHighDateTime << 32) + v.dwLowDateTime for v in (kernel, user)) / 1e7 if ok else None
                    actual = '\n'.join(s.strip() for s in stdout.decode('utf-8', errors='replace').splitlines()
                                       if s.strip() and not s.startswith(('INFO:', 'WARN:')))
                    (work / 'stdout.txt').write_bytes(stdout)
                    (work / 'stderr.txt').write_bytes(stderr)
                    layers = json.loads(timing.read_text(encoding='utf-8-sig')).get('layers', []) if timing.exists() else []
                    rows.append(dict(case=name, variant=variant, repeat=repeat, wall_seconds=elapsed,
                                     cpu_seconds=cpu, exit=proc.returncode, passed=proc.returncode == 0 and actual == expected,
                                     actual=actual, expected=expected, layers=layers, command=command))
                    print(f'{variant}/{name}/{repeat}: exit={proc.returncode} wall={elapsed:.3f}s cpu={cpu}', flush=True)
                (output / 'runs.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    medians = {name: {variant: statistics.median(r['wall_seconds'] for r in rows if r['case'] == name and r['variant'] == variant)
                       for variant in compilers} for name in sources if not args.only or name == args.only}
    result = dict(compiler_sha256={k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in compilers.items()},
                  source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.uxb')},
                  passed=all(r['passed'] for r in rows), runs=len(rows), trace_enabled=not args.no_trace, median_wall_seconds=medians,
                  timing_limit='Whole CLI run, including parsing, verification and artifacts; no isolated instruction dispatch speedup claim.',
                  results=rows)
    (output / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
