"""Run real programs on six engines; retain commands, exits and raw results."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENGINES = ['AST', 'MIR', 'x64', 'AST-x64', 'JS', 'WASM']

def norm(text):
    return '\n'.join(s.strip() for s in text.replace('\r', '').splitlines()
                     if s.strip() and not s.startswith(('INFO:', 'WARN:')))

def raw_stdout(text):
    # Interpreter diagnostics share stdout, including after a final semicolon.
    # Remove only its exact completion suffix; retain all language whitespace.
    text = text.replace('\r\n', '\n')
    suffix = 'INFO: Execution completed successfully\n'
    if text.endswith(suffix):
        text = text[:-len(suffix)]
    return ''.join(line for line in text.replace('\r\n', '\n').splitlines(keepends=True)
                   if not line.startswith(('INFO:', 'WARN:')))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output')
    parser.add_argument('--test-root', default=str(HERE))
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--engines', nargs='*', choices=ENGINES)
    parser.add_argument('--jobs', type=int, default=1, choices=range(1, 9))
    parser.add_argument('--timeout', type=int, default=90, help='Per-process time limit in seconds; use a larger budget for loaded interpreter runs')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--native-runtime-dir', help='Stage an isolated candidate DLL next to each generated native executable')
    artifacts = parser.add_mutually_exclusive_group()
    artifacts.add_argument('--temp-builds', dest='temp_builds', action='store_true', default=True,
                           help='Default: remove all compiler/program artifacts after recording raw results and hashes')
    artifacts.add_argument('--keep-builds', dest='temp_builds', action='store_false',
                           help='Retain diagnostic artifacts under build/test_outputs; never deploy binaries into reports')
    parser.add_argument('--resume-sha256', help='Recorded compiler hash for recovering a run predating identity files')
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error('--timeout must be positive')
    compiler = Path(args.uxb).resolve()
    output = Path(args.output or ROOT / 'reports' / ('turkce_ad_' + datetime.now().strftime('%Y%m%d_%H%M%S'))).resolve()
    output.mkdir(parents=True, exist_ok=args.resume)
    test_root = Path(args.test_root).resolve()
    manifest = test_root / 'cases.json'
    if manifest.is_file():
        manifest_bytes = manifest.read_bytes()
        cases = json.loads(manifest_bytes.decode('utf-8-sig'))
    else:
        # Also verify the established expected/*.txt suites with exit codes
        # and per-step evidence; a printed diagnostic alone is insufficient.
        cases = {}
        for source in sorted(test_root.glob('*.uxb')):
            expected = test_root / 'expected' / source.stem
            output_file = expected.with_suffix('.txt')
            case = {'output': output_file.read_text(encoding='utf-8-sig').strip().replace('\r', '') if output_file.exists() else ''}
            engines_file = expected.with_suffix('.engines.txt')
            if engines_file.exists():
                engine_lines = [line.strip() for line in engines_file.read_text(encoding='utf-8-sig').splitlines()
                                if line.strip() and not line.lstrip().startswith('#')]
                if all('=' in line for line in engine_lines):
                    # Model suites use partial ENGINE=run/reject overrides;
                    # a one-line legacy override does not remove other engines.
                    modes = dict.fromkeys(ENGINES[:4], 'run')
                    modes.update(line.split('=', 1) for line in engine_lines)
                    case['engines'] = list(modes)
                    case['errors'] = {engine: mode.partition(':')[2] or 'ERROR:'
                                      for engine, mode in modes.items() if mode.startswith('reject')}
                else:
                    case['engines'] = ' '.join(engine_lines).split()
            else:
                case['engines'] = ENGINES[:4]
            contains_file = expected.with_suffix('.contains.txt')
            if contains_file.exists():
                case.setdefault('errors', {}).update(line.split('=', 1) for line in contains_file.read_text(encoding='utf-8-sig').splitlines() if '=' in line)
            directories_file = expected.with_suffix('.directories.txt')
            if directories_file.exists():
                case['directories'] = [line.strip() for line in directories_file.read_text(encoding='utf-8-sig').splitlines()
                                       if line.strip() and not line.lstrip().startswith('#')]
            stdin_file = expected.with_suffix('.stdin.txt')
            if stdin_file.exists():
                case['stdin'] = stdin_file.read_text(encoding='utf-8-sig')
            files_file = expected.with_suffix('.files.json')
            if files_file.exists():
                case['files'] = json.loads(files_file.read_text(encoding='utf-8-sig'))
            cases[source.stem] = case
        manifest_bytes = json.dumps(cases, ensure_ascii=False, sort_keys=True).encode('utf-8')
    compiler_hash = hashlib.sha256(compiler.read_bytes()).hexdigest()
    identity = dict(compiler_sha256=compiler_hash, cases_sha256=hashlib.sha256(manifest_bytes).hexdigest())
    native_runtime_dir = args.native_runtime_dir or os.environ.get('UXB_NATIVE_RUNTIME_DIR')
    native_runtime = Path(native_runtime_dir).resolve() if native_runtime_dir else None
    if native_runtime:
        identity['native_runtime_sha256'] = hashlib.sha256((native_runtime / 'uxb_runtime.dll').read_bytes()).hexdigest()
    identity_path = output / 'run_identity.json'
    if args.resume and identity_path.exists():
        if json.loads(identity_path.read_text(encoding='utf-8')) != identity:
            parser.error('Resume compiler or expectations differ from the original run')
    elif args.resume:
        if (args.resume_sha256 or '').casefold() != compiler_hash:
            parser.error('Recovering an older run requires its recorded --resume-sha256')
        identity_path.write_text(json.dumps(identity, indent=2), encoding='utf-8')
    else:
        identity_path.write_text(json.dumps(identity, indent=2), encoding='utf-8')

    def run(command, work, case_environment=None, input_text=None, new_console=False):
        command = [str(x) for x in command]
        try:
            environment = os.environ.copy()
            for key, value in (case_environment or {}).items():
                if key != 'UXB_TASK_WORKERS' or not re.fullmatch(r'[0-9]+|AUTO', str(value), re.I):
                    raise ValueError('Only an explicit UXB_TASK_WORKERS test override is supported')
                environment[key] = str(value)
            if native_runtime:
                environment['UXB_NATIVE_RUNTIME_DIR'] = str(native_runtime)
            console_options = {}
            if new_console:
                if os.name != 'nt':
                    raise ValueError('A real Windows console fixture requires Windows')
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = 0  # SW_HIDE; tests never open a visible window.
                console_options = dict(startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
            # Keep lone CR, TAB, BS and NUL in raw console evidence. Text mode
            # silently changes CR to LF before raw_stdout can inspect it.
            input_bytes = input_text.encode('utf-8') if input_text is not None else None
            p = subprocess.run(command, cwd=work, env=environment, input=input_bytes, capture_output=True, timeout=args.timeout, **console_options)
            return dict(command=command, exit=p.returncode,
                        stdout=p.stdout.decode('utf-8', errors='replace'),
                        stderr=p.stderr.decode('utf-8', errors='replace'))
        except subprocess.TimeoutExpired as exc:
            def partial(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
            return dict(command=command, exit=-999, stdout=partial(exc.stdout),
                        stderr=partial(exc.stderr) + f'\nTIMEOUT ({args.timeout} seconds)')

    def run_case(task):
        name, case, engine = task
        evidence = output / name / engine
        evidence.mkdir(parents=True, exist_ok=True)
        source = test_root / (name + '.uxb')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        result_path = evidence / 'result.json'
        if args.resume and result_path.exists():
            try:
                cached = json.loads(result_path.read_text(encoding='utf-8'))
                last = cached['steps'][-1]
                actual = norm(last['stdout'] + '\n' + last['stderr'])
                needle = case.get('errors', {}).get(engine, case.get('errors', {}).get('ALL', case.get('error')))
                matches = raw_stdout(last['stdout']) == case['raw_stdout'] if 'raw_stdout' in case else actual == case.get('output', '')
                ok = (last['exit'] not in (0, -999, -998) and needle.casefold() in actual.casefold()) if needle else (all(s['exit'] == 0 for s in cached['steps']) and matches)
                if (ok and cached.get('passed') and cached.get('case') == name and cached.get('engine') == engine
                        and cached.get('source_sha256') == source_hash
                        and cached['steps'][0]['command'][0] == str(compiler)
                        and cached.get('compiler_sha256', compiler_hash) == compiler_hash):
                    cached['reused_from_previous_attempt'] = True
                    print(f'REUSE {engine}/{name}', flush=True)
                    return cached
            except (ValueError, KeyError, IndexError):
                pass
            # Preserve failed/incomplete evidence before retrying it.
            import time
            shutil.copyfile(result_path, evidence / ('result_attempt_' + str(time.time_ns()) + '.json'))
        temporary_build = Path(tempfile.mkdtemp(prefix='uxb_accept_')).resolve() if args.temp_builds else None
        retained_key = output.name + '_' + hashlib.sha256(str(output).encode()).hexdigest()[:10]
        work = temporary_build or ROOT / 'build/test_outputs' / retained_key / name / engine
        work.mkdir(parents=True, exist_ok=True)
        for relative_directory in case.get('directories', []):
            directory = (work / relative_directory).resolve()
            if directory != work and work not in directory.parents:
                raise ValueError('Test directory must stay inside its isolated work area')
            directory.mkdir(parents=True, exist_ok=True)
        if engine in ('AST', 'MIR'):
            command = [compiler, 'run', source] + (['--interpreter-backend', 'MIR'] if engine == 'MIR' else [])
        elif engine in ('x64', 'AST-x64'):
            command = [compiler, 'bld', source, '-o', 'program.exe'] + (['--x64-mode', 'AST'] if engine == 'AST-x64' else [])
        elif engine == 'JS':
            command = [compiler, 'jsw', source, '--js-out', work / 'program.js']
        else:
            command = [compiler, 'wat', source, '--emit-wasm', '--wat-out', work / 'program.wat', '--wasm-out', work / 'program.wasm', '--wat2wasm=' + str(ROOT / 'tools/wabt/bin/wat2wasm.exe')]
        build_root = work / 'build'
        artifact_hashes = {}
        steps = [run(command + ['--out-root', build_root], work, case.get('environment'), case.get('stdin'))]
        built = steps[-1]
        if built['exit'] == 0 and engine not in ('AST', 'MIR'):
            if engine in ('x64', 'AST-x64'):
                match = re.search(r'build tamamlandi: (.+)', built['stdout'])
                executable = Path(match[1].strip()) if match else work / 'program.exe'
                command = [executable if executable.is_absolute() else work / executable]
            else:
                command = [shutil.which('node') or 'node', work / ('program.js' if engine == 'JS' else 'run_wasm.js')]
            if Path(command[-1]).is_file():
                if native_runtime and engine in ('x64', 'AST-x64'):
                    for dependency in native_runtime.glob('*.dll'):
                        shutil.copyfile(dependency, Path(command[-1]).parent / dependency.name)
                    artifact_hashes['uxb_runtime.dll'] = hashlib.sha256((Path(command[-1]).parent / 'uxb_runtime.dll').read_bytes()).hexdigest()
                artifact_hashes[str(command[-1])] = hashlib.sha256(Path(command[-1]).read_bytes()).hexdigest()
                steps.append(run(command, work, case.get('environment'), case.get('stdin'), bool(case.get('new_console'))))
            else:
                steps.append(dict(exit=-998, stdout='', stderr='Missing executable artifact', command=[str(x) for x in command]))
        last = steps[-1]
        if engine == 'WASM' and built['exit'] == 0:
            for artifact in ('program.wasm', 'program.wat', 'run_wasm.js', 'ux_wasm_runtime.js'):
                artifact_path = work / artifact
                if artifact_path.is_file():
                    artifact_hashes[str(artifact_path)] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        actual = norm(last['stdout'] + '\n' + last['stderr'])
        needle = case.get('errors', {}).get(engine, case.get('errors', {}).get('ALL', case.get('error')))
        matches = raw_stdout(last['stdout']) == case['raw_stdout'] if 'raw_stdout' in case else actual == case.get('output', '')
        ok = (last['exit'] not in (0, -999, -998) and needle.casefold() in actual.casefold()) if needle else (all(s['exit'] == 0 for s in steps) and matches)
        file_checks = {}
        for relative, expected_file in case.get('files', {}).get(engine, case.get('files', {}).get('ALL', {})).items():
            path = (work / relative).resolve()
            if work not in path.parents:
                raise ValueError('Expected file must stay inside its isolated work area')
            try:
                exists = path.is_file()
                check = {'exists': exists, 'matched': False}
                if expected_file.get('absent'):
                    check['matched'] = not exists
                elif exists:
                    data = path.read_bytes()
                    expected_bytes = (bytes.fromhex(expected_file['hex']) if 'hex' in expected_file
                                      else expected_file['text'].encode('utf-8'))
                    check.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                 matched=data == expected_bytes)
            except OSError as error:
                check = {'matched': False, 'error': str(error)}
            file_checks[relative] = check
            if not check['matched']:
                ok = False
                actual += '\nFILE_CHECK_FAILED: ' + relative
        record = dict(case=name, engine=engine, passed=ok, actual=actual, steps=steps, environment=case.get('environment', {}),
                      file_checks=file_checks,
                      new_console=bool(case.get('new_console')),
                      source_sha256=source_hash, compiler_sha256=compiler_hash,
                      artifact_sha256=artifact_hashes, temporary_build_artifacts=bool(temporary_build))
        record['artifact_root'] = str(work)
        record['evidence_root'] = str(evidence)
        record['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if not ok and engine in ('x64', 'AST-x64'):
            record['build_failure_files'] = {
                str(p.relative_to(build_root)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                                'excerpt': p.read_text(encoding='utf-8', errors='replace')[:16000]}
                for p in [*build_root.rglob('*.txt'), *build_root.rglob('program.asm')] if p.stat().st_size <= 262144
            }
        result_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        if temporary_build:
            # Only this invocation's system-temp directory may be removed.
            # Workspace evidence and source files are never cleanup targets.
            if temporary_build.parent != Path(tempfile.gettempdir()).resolve() or not temporary_build.name.startswith('uxb_accept_'):
                raise RuntimeError('Unexpected temporary build directory')
            if ROOT == temporary_build or ROOT in temporary_build.parents:
                raise RuntimeError('Refusing workspace cleanup')
            shutil.rmtree(temporary_build)
        print(('PASS' if ok else 'FAIL') + f' {engine}/{name}' + ('' if ok else ': ' + actual.replace('\n', ' | ')), flush=True)
        return record

    tasks = [(name, case, engine) for name, case in cases.items()
             if not args.only or name in args.only
             for engine in case.get('engines', ENGINES)
             if not args.engines or engine in args.engines]
    # Every task has its own working directory and output root. Limit process
    # concurrency explicitly; one worker retains the original default behavior.
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(run_case, tasks))
    passed = sum(r['passed'] for r in results)
    summary = dict(schema='uxb.turkce_ad.v1', compiler=str(compiler), sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
                   cases_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                   total=len(results), passed=passed, failed=len(results)-passed, results=results)
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Toplam: {len(results)}   PASS: {passed}   FAIL: {len(results)-passed}')
    return 0 if results and passed == len(results) else 1

if __name__ == '__main__':
    sys.exit(main())
