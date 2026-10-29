"""S-028: real execution and output ownership from unrelated empty working directories."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def norm(text):
    return '\n'.join(s.strip() for s in text.replace('\r', '').splitlines()
                     if s.strip() and not s.startswith(('INFO:', 'WARN:')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in HERE.iterdir() if p.suffix in ['.uxb', '.uxbh']}

    def execute_case(spec):
        name, engine, source_name, explicit = spec
        report = output / name
        report.mkdir()
        with tempfile.TemporaryDirectory(prefix='uxb_out_isolation_') as temp:
            temp = Path(temp)
            cwd = temp / ('nested work dir/space folder' if name.endswith('_cwd1') else 'empty work dir')
            cwd.mkdir(parents=True)
            out_root = temp / 'separate output root'
            out_root.mkdir()
            # A broken local default must not be consumed as the compiler policy.
            if engine == 'FFI':
                poison = cwd / 'build/manual/config/ffi_allowlist.txt'
                poison.parent.mkdir(parents=True)
                poison.write_text('NOT_A_POLICY\n')
            before = {str(p.relative_to(cwd)): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'DIR'
                      for p in cwd.rglob('*')}
            source = HERE / source_name
            command = [str(compiler)]
            if engine in ['AST', 'MIR', 'FFI']:
                command += ['run', str(source)]
                if engine == 'MIR':
                    command += ['--interpreter-backend', 'MIR']
            elif engine in ['x64', 'AST-x64']:
                command += ['bld', str(source)]
                if engine == 'AST-x64':
                    command += ['--x64-mode', 'AST']
            elif engine == 'JS':
                command += ['jsw', str(source), '--js-out', str(out_root / 'program.js')]
            else:
                command += ['wat', str(source), '--emit-wasm', '--wat-out', str(out_root / 'program.wat'),
                            '--wasm-out', str(out_root / 'program.wasm'),
                            '--wat2wasm=' + str(ROOT / 'tools/wabt/bin/wat2wasm.exe')]
            command += ['--out-root', str(out_root), '--run-id', 'isolation_run']
            explicit_path = temp / 'explicit frontend/preprocessed.uxb'
            if explicit:
                explicit_path.parent.mkdir()
                command += ['--preprocessed-out', str(explicit_path)]
            steps = []

            def run(label, argv):
                proc = subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True, timeout=120)
                (report / (label + '.stdout')).write_bytes(proc.stdout)
                (report / (label + '.stderr')).write_bytes(proc.stderr)
                steps.append(dict(label=label, command=list(map(str, argv)), cwd=str(cwd), exit=proc.returncode))
                return proc

            emit = run('compiler', command)
            actual = emit
            if emit.returncode == 0 and engine in ['x64', 'AST-x64']:
                match = re.search(r'build tamamlandi: (.+)', emit.stdout.decode(errors='replace'))
                if match:
                    actual = run('program', [match.group(1).strip()])
            elif emit.returncode == 0 and engine in ['JS', 'WASM']:
                actual = run('program', ['node', out_root / ('program.js' if engine == 'JS' else 'run_wasm.js')])
            stdout = actual.stdout.decode('utf-8', errors='replace')
            expected = 'FFI_OK' if engine == 'FFI' else 'etiket=42'
            checks = dict(exit_zero=emit.returncode == 0 and actual.returncode == 0, actual_output=norm(stdout) == expected)
            after = {str(p.relative_to(cwd)): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'DIR'
                     for p in cwd.rglob('*')}
            checks['cwd_unchanged'] = before == after
            changed_cwd = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
            preprocessing = list(out_root.rglob('preprocess_result.json'))
            matrices = list(out_root.rglob('runtime_route_matrix.json'))
            checks['one_preprocess_report'] = len(preprocessing) == 1
            checks['one_runtime_matrix'] = len(matrices) == 1
            expanded = explicit_path if explicit else next(iter(out_root.rglob('preprocessed.uxb')), None)
            checks['expanded_source'] = bool(expanded and expanded.is_file() and
                ('FFI_OK' if engine == 'FFI' else '42') in expanded.read_text(encoding='utf-8-sig'))
            if engine == 'FFI':
                text = (emit.stdout + emit.stderr).decode('utf-8', errors='replace')
                checks['no_cwd_policy'] = 'build/manual/config/ffi_allowlist.txt' not in text.replace('\\', '/')
                checks['compiler_policy_path'] = str(compiler.parent).replace('\\', '/') + '/config/ffi_allowlist.txt' in text.replace('\\', '/')
            artifacts = {}
            for p in out_root.rglob('*'):
                if p.is_file():
                    artifacts[str(p.relative_to(out_root))] = hashlib.sha256(p.read_bytes()).hexdigest()
                    if p.name in ['preprocess_result.json', 'runtime_route_matrix.json', 'run_manifest.json', 'preprocessed.uxb']:
                        dest = report / 'evidence' / p.relative_to(out_root)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(p.read_bytes())
            return dict(name=name, engine=engine, passed=all(checks.values()), checks=checks,
                        actual=norm(stdout), cwd_changes=changed_cwd, steps=steps, artifact_sha256=artifacts)

    specs = []
    for cwd in range(2):
        for source in (['simple.uxb'] if args.quick else ['program.uxb', 'program_b.uxb', 'forward.uxb', 'nested.uxb']):
            for engine in (['AST', 'x64'] if args.quick else ['AST', 'MIR', 'x64', 'AST-x64', 'JS', 'WASM']):
                specs.append((source[:-4] + '_' + engine + '_cwd' + str(cwd), engine, source, False))
        specs.append(('ffi_cwd' + str(cwd), 'FFI', 'ffi.uxb', False))
        if not args.quick:
            specs.append(('explicit_cwd' + str(cwd), 'AST', 'program.uxb', True))
    # Independent roots run concurrently, including the native build cases.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(execute_case, specs):
            results.append(row)
            print(('PASS ' if row['passed'] else 'FAIL ') + row['name'] +
                  (' ' + str(row['checks']) if not row['passed'] else ''), flush=True)
            (output / 'summary.json').write_text(json.dumps(dict(compiler=str(compiler),
                compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(), source_sha256=source_hashes,
                total=len(results), passed=sum(r['passed'] for r in results), results=results), indent=2), encoding='utf-8')
    count = sum(r['passed'] for r in results)
    print(f'Toplam: {len(results)} PASS: {count} FAIL: {len(results)-count}')
    return 0 if count == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
