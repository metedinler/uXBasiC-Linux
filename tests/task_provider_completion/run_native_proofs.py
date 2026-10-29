"""Prove OS-worker execution and bounded two-worker overlap, not just JOIN output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def normalized(text):
    return '\n'.join(line.strip() for line in text.splitlines()
                     if line.strip() and not line.startswith(('INFO:', 'WARN:')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repeat', type=int, default=2)
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows = []

    def run(command, cwd, env=None):
        try:
            result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                                    capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', timeout=90)
            return dict(command=[str(x) for x in command], exit=result.returncode,
                        stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as exc:
            return dict(command=[str(x) for x in command], exit=None, timeout=True,
                        stdout=str(exc.stdout or ''), stderr=str(exc.stderr or ''))

    # Only this invocation's system-temp tree is removed by TemporaryDirectory.
    with tempfile.TemporaryDirectory(prefix='uxb_task_proof_') as scratch:
        for engine in ('x64', 'AST-x64'):
            for name in ('worker_thread', 'overlap', 'running_cancel'):
                work = Path(scratch) / engine / name
                work.mkdir(parents=True)
                source = Path(__file__).resolve().parent / 'proofs' / (name + '.uxb')
                command = [compiler, 'bld', source, '--task-workers', '2', '--out-root', work, '-o', work / 'program.exe']
                if engine == 'AST-x64':
                    command += ['--x64-mode', 'AST']
                build = run(command, work)
                found = re.search(r'build tamamlandi: (.+)', build['stdout'])
                executable = Path(found.group(1).strip()) if found else None
                if build['exit'] != 0 or not executable or not executable.is_file():
                    failure_files = {str(p.relative_to(work)): dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), excerpt=p.read_text(encoding='utf-8', errors='replace')[:24000])
                                     for p in work.rglob('*') if p.is_file() and p.suffix in ('.txt', '.asm') and p.stat().st_size <= 262144}
                    rows.append(dict(engine=engine, case=name, ok=False, build=build, build_failure_files=failure_files))
                    continue
                binary_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
                runtime_hash = hashlib.sha256((executable.parent / 'uxb_runtime.dll').read_bytes()).hexdigest()
                for workers in ('1', '2', 'AUTO'):
                    env = os.environ.copy()
                    if workers == 'AUTO':
                        env.pop('UXB_TASK_WORKERS', None)
                    else:
                        env['UXB_TASK_WORKERS'] = workers
                    expected = ('0\n-1\n' + ('1' if workers == '1' else '2')) if name == 'worker_thread' else ('0\n0\n258\n0' if workers == '1' else '0\n0\n0\n0')
                    if name == 'running_cancel':
                        expected = '0\nCANCELLED'
                    for repeat in range(args.repeat):
                        result = run([executable], executable.parent, env)
                        ok = result['exit'] == 0 and normalized(result['stdout']) == expected and not result['stderr'].strip()
                        rows.append(dict(engine=engine, case=name, workers=workers,
                                         repeat=repeat + 1, expected=expected, ok=ok,
                                         binary_sha256=binary_hash, runtime_sha256=runtime_hash,
                                         build=build, execution=result))
                        print(('PASS' if ok else 'FAIL'), engine, name, workers, repeat + 1, flush=True)
    summary = dict(compiler=str(compiler), compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
                   total=len(rows), passed=sum(r['ok'] for r in rows), rows=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Total {summary['total']} PASS {summary['passed']}")
    return int(summary['passed'] != summary['total'])


if __name__ == '__main__':
    raise SystemExit(main())
