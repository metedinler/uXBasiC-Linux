"""S-027: verify emission evidence separately from actual JS/WASM execution."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for mode in ['JS', 'WASM', 'WAT']:
        for valid in [True, False]:
            work = output / (mode + ('_valid' if valid else '_invalid'))
            work.mkdir()
            steps = []

            def run(label, command):
                command = list(map(str, command))
                proc = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
                (work / (label + '.stdout')).write_bytes(proc.stdout)
                (work / (label + '.stderr')).write_bytes(proc.stderr)
                steps.append(dict(label=label, command=command, exit=proc.returncode))
                return proc

            source = HERE / ('function_parameter.uxb' if valid else 'invalid_assignment.uxb')
            command = [compiler, 'jsw' if mode == 'JS' else 'wat', source,
                       '--out-root', work / 'out', '--js-report-json-out', work / 'backend.json',
                       '--wasm-report-json-out', work / 'backend.json']
            if mode == 'JS':
                command += ['--js-out', work / 'program.js']
            else:
                command += ['--wat-out', work / 'program.wat']
                if mode == 'WASM':
                    command += ['--emit-wasm', '--wasm-out', work / 'program.wasm',
                                '--wat2wasm=' + str(ROOT / 'tools/wabt/bin/wat2wasm.exe')]
            emit = run('emit', command)
            report_path = work / 'backend.json'
            report = json.loads(report_path.read_text(encoding='utf-8-sig')) if report_path.exists() else {}
            checks = {}
            if valid:
                checks['emit_ok'] = emit.returncode == 0 and report.get('status') == 'PASS'
                checks['static_verified'] = report.get('verification', {}).get('mir_static_passed') is True
                checks['no_mir_execution_claim'] = report.get('verification', {}).get('mir_interpreter_passed') is False
                checks['target'] = report.get('target') == mode.lower()
                if mode == 'WAT' and emit.returncode == 0:
                    # WAT-only emission has no loader. Use the same source's generated
                    # WASM host adapter; translate the independent WAT artifact here.
                    translate = run('translate', [ROOT / 'tools/wabt/bin/wat2wasm.exe',
                                                 work / 'program.wat', '-o', work / 'program.wasm'])
                    checks['translate_ok'] = translate.returncode == 0
                    for name in ['ux_wasm_runtime.js', 'run_wasm.js']:
                        shutil.copyfile(output / 'WASM_valid' / name, work / name)
                if mode != 'JS' and (work / 'program.wasm').exists():
                    checks['validate_ok'] = run('validate', [ROOT / 'tools/wabt/bin/wasm-validate.exe', work / 'program.wasm']).returncode == 0
                if emit.returncode == 0:
                    execute = run('execute', ['node', work / ('program.js' if mode == 'JS' else 'run_wasm.js')])
                    actual = execute.stdout.decode('utf-8', errors='replace').replace('\r', '').strip()
                    checks['real_output'] = execute.returncode == 0 and actual == '42\n42'
            else:
                text = (emit.stdout + emit.stderr).decode('utf-8', errors='replace')
                checks['semantic_rejected'] = emit.returncode > 0 and 'Semantic gate basarisiz' in text
                checks['no_success_report'] = report.get('status') != 'PASS'
            rows.append(dict(mode=mode, valid=valid, steps=steps, checks=checks, passed=all(checks.values())))
            print(('PASS ' if rows[-1]['passed'] else 'FAIL ') + work.name, flush=True)
            (output / 'summary.json').write_text(json.dumps(dict(compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
                total=len(rows), passed=sum(r['passed'] for r in rows), results=rows), indent=2), encoding='utf-8')
    passed = sum(r['passed'] for r in rows)
    print(f'Toplam: {len(rows)} PASS: {passed} FAIL: {len(rows)-passed}')
    return 0 if passed == len(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
