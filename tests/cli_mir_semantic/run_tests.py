"""S-024: typed MIR verification must include the semantic gate on every CLI alias."""
import argparse
import hashlib
import json
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
    results = []
    for mode in ['verb', 'flag', 'verify_json', 'full_json']:
        for stem in ['invalid_assignment', 'valid', 'function_parameter']:
            valid = stem != 'invalid_assignment'
            name = mode + '_' + stem
            work = output / name
            work.mkdir()
            source = HERE / (stem + '.uxb')
            command = [str(compiler)]
            if mode == 'verb':
                command += ['mir', str(source)]
            else:
                command += ['--source', str(source)]
                if mode == 'flag':
                    command += ['--mir-verify']
                elif mode == 'verify_json':
                    command += ['--mir-verify-json-out', str(work / 'verify.json')]
                else:
                    command += ['--mir-full-json-out', str(work / 'full.json')]
            command += ['--out-root', str(work / 'out')]
            proc = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
            (work / 'stdout.txt').write_bytes(proc.stdout)
            (work / 'stderr.txt').write_bytes(proc.stderr)
            text = (proc.stdout + proc.stderr).decode('utf-8', errors='replace')
            manifests = list(work.rglob('run_manifest.json'))
            manifests_json = [json.loads(p.read_text(encoding='utf-8-sig')) for p in manifests]
            checks = {}
            if valid:
                checks['exit_zero'] = proc.returncode == 0
                checks['semantic_stage'] = len(manifests_json) == 1 and manifests_json[0].get('stages', {}).get('semantic') is True
                checks['mir_stage'] = len(manifests_json) == 1 and manifests_json[0].get('stages', {}).get('mir_build_opt') is True
                checks['canonical_emitted'] = bool(list(work.rglob('canonical_mir.json')))
                if mode in ['verify_json', 'full_json']:
                    checks['explicit_json'] = (work / ('verify.json' if mode == 'verify_json' else 'full.json')).is_file()
            else:
                checks['exit_nonzero'] = proc.returncode > 0
                checks['semantic_diagnostic'] = 'Semantic gate basarisiz' in text and 'STRING' in text and 'I32' in text
                checks['no_canonical_mir'] = not list(work.rglob('canonical_mir.json'))
                checks['no_explicit_success'] = not (work / 'verify.json').exists() and not (work / 'full.json').exists()
                checks['no_pass_manifest'] = all(m.get('status') != 'PASS' for m in manifests_json)
            row = dict(name=name, command=command, exit=proc.returncode, checks=checks, passed=all(checks.values()), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            results.append(row)
            print(('PASS ' if row['passed'] else 'FAIL ') + name, flush=True)
            (output / 'summary.json').write_text(json.dumps(dict(compiler=str(compiler), compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(), total=len(results), passed=sum(r['passed'] for r in results), results=results), indent=2), encoding='utf-8')
    count = sum(r['passed'] for r in results)
    print(f'Toplam: {len(results)} PASS: {count} FAIL: {len(results)-count}')
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
