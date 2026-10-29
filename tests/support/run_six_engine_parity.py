"""Real executions, exact oracle, exit codes and hashes for six compiler engines.

Each compiler invocation gets a fresh directory. No rejected feature, missing
artifact or stale output is counted as a successful positive-language probe.
Outputs are kept as evidence; the runner deletes no workspace files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINES = ('AST', 'MIR', 'MIR-x64', 'AST-x64', 'JS', 'WASM')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def normalized(text):
    return '\n'.join(line.strip() for line in text.replace('\r', '').splitlines()
                     if line.strip() and not re.match(r'^(?:INFO:|WARN:)', line))

def run(args, cwd, timeout):
    start = time.monotonic()
    p = subprocess.Popen([str(a) for a in args], cwd=cwd, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    timed_out = False
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        else:
            p.kill()
        stdout, stderr = p.communicate()
    return {'args': [str(a) for a in args], 'exitCode': p.returncode, 'timedOut': timed_out,
            'seconds': round(time.monotonic() - start, 3),
            'stdout': stdout.decode('utf8', 'replace'), 'stderr': stderr.decode('utf8', 'replace')}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', required=True, type=Path)
    parser.add_argument('--suite', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=90)
    parser.add_argument('--engines', nargs='+', choices=ENGINES, default=ENGINES)
    parser.add_argument('--only', nargs='*')
    opts = parser.parse_args()
    compiler, suite, out = opts.compiler.resolve(), opts.suite.resolve(), opts.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    node = shutil.which('node')
    w2w = ROOT / 'tools/wabt/bin/wat2wasm.exe'
    if ('JS' in opts.engines or 'WASM' in opts.engines) and not node:
        raise RuntimeError('Node is required for real web-target execution')
    if 'WASM' in opts.engines and not w2w.is_file():
        raise RuntimeError('wat2wasm is required for real WASM execution')
    report = {'compiler': str(compiler), 'compilerSha256': digest(compiler),
              'suite': str(suite), 'engines': opts.engines, 'positiveExecutionOnly': True,
              'cases': [], 'passed': 0, 'failed': 0}
    for source in sorted(suite.glob('*.uxb')):
        if opts.only and source.stem not in opts.only:
            continue
        expected_file = suite / 'expected' / (source.stem + '.txt')
        if not expected_file.is_file():
            raise RuntimeError(f'Positive oracle missing: {expected_file}')
        expected = normalized(expected_file.read_text(encoding='utf-8-sig'))
        for engine in opts.engines:
            folder = out / source.stem / engine
            folder.mkdir(parents=True)
            common = [compiler, 'run', source, '--out-root', folder]
            stages = []
            if engine in ('AST', 'MIR'):
                if engine == 'MIR':
                    common += ['--interpreter-backend', 'MIR']
                stages.append(run(common, folder, opts.timeout))
            else:
                if engine in ('MIR-x64', 'AST-x64'):
                    artifact = folder / 'program.exe'
                    build = [compiler, 'bld', source, '--out-root', folder, '-o', artifact]
                    if engine == 'AST-x64':
                        build += ['--x64-mode', 'AST']
                    execute = [artifact]
                elif engine == 'JS':
                    artifact = folder / 'program.js'
                    build = [compiler, 'jsw', source, '--out-root', folder, '--js-out', artifact]
                    execute = [node, artifact]
                else:
                    artifact = folder / 'program.wasm'
                    build = [compiler, 'wat', source, '--out-root', folder, '--emit-wasm',
                             '--wat-out', folder / 'program.wat', '--wasm-out', artifact,
                             f'--wat2wasm={w2w}']
                    execute = [node, folder / 'run_wasm.js']
                stages.append(run(build, folder, opts.timeout))
                if engine in ('MIR-x64', 'AST-x64'):
                    match = re.search(r'build tamamlandi:\s*([^\r\n]+)', stages[-1]['stdout'])
                    if match:
                        produced = Path(match.group(1).strip()).resolve()
                        if not produced.is_relative_to(folder.resolve()):
                            raise RuntimeError(f'Build artifact escaped isolated output directory: {produced}')
                        artifact, execute = produced, [produced]
                if stages[-1]['exitCode'] == 0 and not stages[-1]['timedOut'] and artifact.is_file():
                    stages.append(run(execute, folder, opts.timeout))
            final = stages[-1]
            actual = normalized(final['stdout'] + '\n' + final['stderr'])
            passed = (all(s['exitCode'] == 0 and not s['timedOut'] for s in stages)
                      and (engine in ('AST', 'MIR') or len(stages) == 2) and actual == expected)
            case = {'source': str(source), 'sourceSha256': digest(source), 'engine': engine,
                    'expected': expected, 'actual': actual, 'passed': passed, 'stages': stages}
            report['cases'].append(case)
            report['passed' if passed else 'failed'] += 1
            (out / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
            print(f"{'PASS' if passed else 'FAIL'} {source.stem}/{engine}", flush=True)
            if not passed:
                print(f'  wanted={expected!r} actual={actual[:1800]!r}', flush=True)
    print(f"Total {len(report['cases'])}; PASS {report['passed']}; FAIL {report['failed']}", flush=True)
    return int(report['failed'] != 0 or not report['cases'])

if __name__ == '__main__':
    raise SystemExit(main())
