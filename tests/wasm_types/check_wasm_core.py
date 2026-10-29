"""Execute emitted WASM with host text operations disabled (console stays bound)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name('cases.json').read_text(encoding='utf-8'))
    records = []
    for name in ('text_values', 'text_arrays', 'text_growth_alias', 'text_nul', 'runtime_name_isolation'):
        work = Path(args.results).resolve() / name / 'WASM'
        runner = (work / 'run_wasm.js').read_text(encoding='utf-8')
        entry = re.search(r'instance\.exports\["([^"]+)"\]', runner).group(1)
        code = (
            "const fs=require('fs');require('./ux_wasm_runtime.js');"
            "globalThis.uxbWasmImports.ux.string_op=()=>{throw Error('core text operation delegated to host')};"
            "WebAssembly.instantiate(fs.readFileSync('program.wasm'),globalThis.uxbWasmImports)"
            ".then(({instance})=>{globalThis.uxbWasmInstance=instance;instance.exports["
            + json.dumps(entry) + "]();}).catch(e=>{console.error(e);process.exitCode=1;});"
        )
        result = subprocess.run(['node', '-e', code], cwd=work, capture_output=True,
                                encoding='utf-8', timeout=30)
        actual = result.stdout.strip().replace('\r', '')
        record = dict(case=name, exit=result.returncode, actual=actual, stderr=result.stderr,
                      passed=result.returncode == 0 and actual == cases[name]['output'],
                      host_string_op='throws if called',
                      wasm_sha256=hashlib.sha256((work / 'program.wasm').read_bytes()).hexdigest())
        records.append(record)
        print(('PASS' if record['passed'] else 'FAIL') + ' ' + name)
    Path(args.output).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(r['passed'] for r in records) else 1


if __name__ == '__main__':
    raise SystemExit(main())
