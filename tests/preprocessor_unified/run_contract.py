"""Actual preprocessing effects, removed selectors, and inactive block isolation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--orphan-all', action='store_true', help='Verify every standalone block terminator is rejected')
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    specs = []

    def add(name, source, **expect):
        specs.append((name, source, expect))

    add('shared_manifest_macro', '%%BUNDLE_NAME "ortak"\n%%DEFINE VALUE 42\nPRINT VALUE\n',
        expanded='PRINT 42', manifest=True)
    add('inactive_control', '%%IF FALSE\n%%BUNDLE_NAME "kapali"\n%%ELSE\nPRINT 42\n%%ENDIF\n',
        expanded='PRINT 42', manifest=False)
    # Payload includes a fake conditional terminator and unsafe path; neither is
    # interpreted or validated in an inactive block, nor does it write artifacts.
    add('inactive_raw_block', '%%IF FALSE\n%%JS_BEGIN "../blocked.js"\n%%ENDIF\ninvalid raw payload\n%%JS_END\n%%ELSE\nPRINT 42\n%%ENDIF\n',
        expanded='PRINT 42', block_count=0)
    blocks = [('HTML', 'HTML', ''), ('CSS', 'CSS', ''),
              ('JS', 'JS', '%%ALLOW_RAW_JS ON\n'),
              ('WAT', 'WAT', '%%ALLOW_RAW_WAT ON\n'),
              ('WAT_FUNC', 'WAT_FUNC', '%%ALLOW_RAW_WAT ON\n'),
              ('WASM_HOST_JS', 'WASM_HOST_JS', '%%ALLOW_RAW_JS ON\n'),
              ('JSON', 'JSON', ''), ('JSON_ARRAY', 'JSON_ARRAY', ''),
              ('MD', 'MD', ''), ('GEN_BLOCK', 'GEN', '')]
    for begin, target, prefix in blocks:
        head = 'GEN_BLOCK' if begin == 'GEN_BLOCK' else begin + '_BEGIN'
        end = 'GEN_END' if begin == 'GEN_BLOCK' else begin + '_END'
        add('block_' + target, prefix + f'%%{head}\npayload_{target}\n%%{end}\nPRINT 42\n',
            expanded='PRINT 42', block_count=1, target=target, payload='payload_' + target)
    # S-672: a template body is stored by name (no block); %%SECTION only sets the default section of the blocks inside it.
    add('block_TEMPLATE', '%%TEMPLATE_BEGIN payload_TEMPLATE\npayload_TEMPLATE\n%%TEMPLATE_END\nPRINT 42\n', expanded='PRINT 42', block_count=0)
    add('block_SECTION', '%%SECTION HEAD\n%%HTML_BEGIN\npayload_SECTION\n%%HTML_END\n%%ENDSECTION\nPRINT 42\n',
        expanded='PRINT 42', block_count=1, target='HTML', section='HEAD', payload='payload_SECTION')
    add('runtime_js_policy', '%%TARGET JS\n%%JS_BEGIN RUNTIME\nconst runtimeMarker=42;\n%%JS_END\nPRINT 42\n',
        expanded='PRINT 42', block_count=1, target='JS', section='RUNTIME')
    add('raw_js_without_permission', '%%JS_BEGIN\nconst marker=42;\n%%JS_END\n',
        error='RAW_JS_PAYLOAD_NOT_ALLOWED_FOR_TARGET')
    add('missing_block_end', '%%HTML_BEGIN\n<p>unterminated</p>\n', error='META_BLOCK_END_MISSING')
    add('unmatched_end', '%%HTML_END\n', error='META_UNMATCHED_END')
    if args.orphan_all:
        for end in ['CSS_END', 'JS_END', 'WAT_END', 'WAT_FUNC_END', 'WASM_HOST_JS_END',
                    'JSON_END', 'JSON_ARRAY_END', 'MD_END', 'TEMPLATE_END', 'ENDSECTION', 'GEN_END']:
            add('orphan_' + end.lower(), '%%' + end + '\n', error='META_UNMATCHED_END')
    add('unknown_is_error', '%%DOES_NOT_EXIST\n', error='META_UNKNOWN_DIRECTIVE')
    add('embed_base64_real_bytes', '%%EMBEDBASE64 "payload.bin" AS EMBEDDED\nPRINT EMBEDDED\n',
        expanded='PRINT YWJj', binary_input=True)
    for mode in ('A', 'B'):
        # S-671: %%PP is not a directive any more (no tombstone); it is rejected like every unknown directive.
        add('removed_source_' + mode, '%%PP ' + mode + '\nPRINT 42\n', error='META_UNKNOWN_DIRECTIVE')
    for option in ('--pp', '--preprocessor', '-b28', '-b30'):
        add('removed_cli_' + option.lstrip('-'), 'PRINT 42\n', args=[option, 'B'], rejected=True)
    for option in ('--pp=B', '--preprocessor=A'):
        add('removed_cli_equals_' + option.split('=')[0].lstrip('-'), 'PRINT 42\n', args=[option], rejected=True)

    rows = []
    for name, source_text, expected in specs:
        work = output / name
        work.mkdir()
        source = work / 'program.uxb'
        source.write_text(source_text, encoding='utf-8')
        expanded = work / 'expanded.uxb'
        report = work / 'preprocess.json'
        with tempfile.TemporaryDirectory(prefix='uxb_unified_pp_') as scratch:
            if expected.get('binary_input'):
                (Path(scratch) / 'payload.bin').write_bytes(b'abc')
            command = [str(compiler), 'lex', str(source), '--out-root', str(Path(scratch) / 'out'),
                       '--preprocessed-out', str(expanded), '--preprocess-result-json-out', str(report)]
            command += expected.get('args', [])
            p = subprocess.run(command, cwd=scratch, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=90)
            (work / 'stdout.txt').write_text(p.stdout, encoding='utf-8')
            (work / 'stderr.txt').write_text(p.stderr, encoding='utf-8')
            checks = {}
            if expected.get('error') or expected.get('rejected'):
                checks['rejected'] = p.returncode > 0
                if expected.get('error'):
                    checks['diagnostic'] = expected['error'] in p.stdout + p.stderr
            else:
                checks['exit_zero'] = p.returncode == 0
                checks['expanded_source'] = expanded.exists() and expanded.read_text(encoding='utf-8-sig').strip() == expected['expanded']
                data = json.loads(report.read_text(encoding='utf-8-sig')) if report.exists() else {}
                if 'block_count' in expected:
                    checks['block_count'] = data.get('blockCount') == expected['block_count']
                if 'target' in expected:
                    block = next(iter(data.get('blocks', [])), {})
                    checks['target'] = block.get('target') == expected['target']
                    # The CLI JSON intentionally omits raw payload. Check the
                    # collected source range here; web execution tests cover
                    # consumption of actual JS/WASM payloads separately.
                    checks['source_range'] = block.get('startLine', 0) > 0 and block.get('endLine', 0) > block.get('startLine', 0)
                    if 'section' in expected:
                        checks['section'] = block.get('section') == expected['section']
                    if expected['target'] == 'GEN':
                        generated = list((Path(scratch) / 'out').rglob('generated.txt'))
                        checks['generated_payload'] = len(generated) == 1 and generated[0].read_text().strip() == expected['payload']
                        if generated:
                            (work / 'generated_payload.txt').write_bytes(generated[0].read_bytes())
                if 'manifest' in expected:
                    # Engine and artifact identity (2), plus bundle and its
                    # security snapshot (7) only in the active case.
                    checks['manifest_effect'] = data.get('manifestCount') == (9 if expected['manifest'] else 2)
            # Explicit frontend outputs go to work; implicit outputs belong to out.
            allowed = {'out', 'payload.bin'} if expected.get('binary_input') else {'out'}
            cwd_entries = sorted(p.name for p in Path(scratch).iterdir())
            checks['no_cwd_artifacts'] = set(cwd_entries) <= allowed
            rows.append(dict(name=name, passed=all(checks.values()), checks=checks,
                             expected_rejection=bool(expected.get('error') or expected.get('rejected')),
                             exit=p.returncode, command=command, cwd_entries=cwd_entries,
                             source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
            print(('PASS ' if rows[-1]['passed'] else 'FAIL ') + name, flush=True)
        result = dict(compiler=str(compiler), compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
                      total=len(rows), passed=sum(r['passed'] for r in rows), results=rows)
        (output / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    passed = sum(r['passed'] for r in rows)
    print(f'Toplam: {len(rows)} PASS: {passed} FAIL: {len(rows) - passed}', flush=True)
    return int(passed != len(rows))


if __name__ == '__main__':
    raise SystemExit(main())
