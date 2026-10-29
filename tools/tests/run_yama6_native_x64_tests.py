#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


CASES = [
    {
        'name': 'full_stack',
        'source': 'tests/yama6_runtime/full_stack_native_yama6.uxb',
        'required': [
            'PIPE_RUN', '3', 'THREAD_RUN', 'PARALEL_RUN', 'EVENT_INPUT',
            '42', 'SHELL_OK', '0', 'FULL_STACK_DONE',
        ],
        'forbidden': ['SHOULD_NOT_PRINT'],
        'asm': [
            'call uxb_shell_run', 'call uxb_pipe_run',
            'call uxb_thread_start', 'call uxb_parallel_run',
            'call uxb_task_trigger',
        ],
    },
    {
        'name': 'shell_nowait',
        'source': 'tests/yama1_shell_byte/shell_nowait_outpath_yama1.uxb',
        'required': ['SHELL_NOWAIT_SUBMITTED'],
        'forbidden': [],
        'asm': ['call uxb_shell_start'],
        'file': 'reports/uxb_shell_nowait.txt',
        'file_text': 'UXB_SHELL_NOWAIT',
        'async_file': True,
    },
    {
        'name': 'shell_sync_paths',
        'source': 'tests/yama1_shell_byte/shell_sync_paths_yama1.uxb',
        'required': ['0', 'SHELL_SYNC_PATHS_DONE'],
        'forbidden': [],
        'asm': ['call uxb_shell_run', 'call uxb_text_file_write'],
        'file': 'reports/uxb_shell_sync_out.txt',
        'file_text': 'UXB_SHELL_SYNC_OUT',
        'async_file': False,
    },
]


def find_root(value: str) -> Path:
    start = Path(value).resolve()
    for path in (start, *start.parents):
        if (path / 'src').is_dir() and (path / 'xtestx').is_dir():
            return path
        if (path / 'uxb' / 'src').is_dir():
            return path / 'uxb'
    raise SystemExit(f'uXBasic root bulunamadi: {start}')


def run_process(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict:
    started = time.time()
    process = subprocess.run(
        command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    return {
        'command': command,
        'returncode': process.returncode,
        'stdout': process.stdout,
        'stderr': process.stderr,
        'elapsed_seconds': round(time.time() - started, 3),
    }


def wait_for_file(path: Path, started_ns: int, expected: str, async_file: bool) -> tuple[bool, str]:
    deadline = time.monotonic() + (8.0 if async_file else 1.0)
    text = ''
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_mtime_ns >= started_ns:
            text = path.read_text(encoding='utf-8', errors='replace')
            if expected in text:
                return True, text
        time.sleep(0.05)
    return False, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--uxb', default='bin/uxb.exe')
    args = parser.parse_args()

    root = find_root(args.root)
    compiler = (root / args.uxb).resolve()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = root / 'reports' / 'yama6_runtime' / 'native_x64' / stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {
        'schema': 'uxb.yama6.native_x64.v1',
        'generated_at': datetime.now().astimezone().isoformat(),
        'compiler': str(compiler),
        'status': 'FAIL',
        'results': [],
    }
    if not compiler.is_file():
        report['error'] = f'compiler missing: {compiler}'
        print(report['error'])
        return 2

    base_env = os.environ.copy()
    base_env['UXB_RT_BACKEND'] = 'auto'
    base_env['PATH'] = (
        str(root / 'bin') + os.pathsep
        + r'C:\msys64\ucrt64\bin' + os.pathsep
        + base_env.get('PATH', '')
    )

    failed = 0
    for backend in ('AST', 'MIR'):
        for case in CASES:
            name = f"{case['name']}_{backend.lower()}"
            build_dir = report_dir / name
            build_dir.mkdir(parents=True, exist_ok=True)
            source = root / case['source']
            command = [
                str(compiler), '--source', str(source), '--build-x64',
                '--build-x64-out', str(build_dir), '--codegen-source', backend,
            ]
            if backend == 'MIR':
                command += ['--x64-mode', 'MIR', '--mir-verify']
            build = run_process(command, root, base_env, 300)

            exe = build_dir / 'program.exe'
            asm = build_dir / 'program.asm'
            checks = {
                'build_exit_zero': build['returncode'] == 0,
                'exe_exists': exe.is_file(),
                'asm_exists': asm.is_file(),
                'runtime_dll_deployed': (build_dir / 'uxb_runtime.dll').is_file(),
            }
            asm_text = asm.read_text(encoding='utf-8', errors='replace') if asm.is_file() else ''
            for marker in case['asm']:
                checks[f'asm:{marker}'] = marker in asm_text

            run = {'command': [], 'returncode': -1, 'stdout': '', 'stderr': '', 'elapsed_seconds': 0}
            file_result = None
            if all(checks.values()):
                run_env = base_env.copy()
                run_env['PATH'] = str(build_dir) + os.pathsep + run_env['PATH']
                started_ns = time.time_ns()
                run = run_process([str(exe)], root, run_env, 60)
                output = (run['stdout'] or '') + '\n' + (run['stderr'] or '')
                checks['run_exit_zero'] = run['returncode'] == 0
                for marker in case['required']:
                    checks[f'output_required:{marker}'] = marker in output
                for marker in case['forbidden']:
                    checks[f'output_forbidden:{marker}'] = marker not in output
                if case.get('file'):
                    file_path = root / case['file']
                    file_ok, file_text = wait_for_file(
                        file_path, started_ns, case['file_text'],
                        bool(case.get('async_file')))
                    checks['output_file_fresh_and_valid'] = file_ok
                    file_result = {'path': str(file_path), 'text': file_text}

            status = 'PASS' if checks and all(checks.values()) else 'FAIL'
            if status == 'FAIL':
                failed += 1
                print(f"FAIL: {name}")
            else:
                print(f"PASS: {name}")
            report['results'].append({
                'name': name,
                'backend': backend,
                'source': str(source),
                'build_dir': str(build_dir),
                'status': status,
                'checks': checks,
                'build': build,
                'run': run,
                'file_result': file_result,
            })

    report['failed'] = failed
    report['passed'] = len(report['results']) - failed
    report['status'] = 'PASS' if failed == 0 else 'FAIL'
    timestamped = report_dir / 'report.json'
    latest = root / 'reports' / 'yama6_runtime' / 'native_x64_tests.json'
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    timestamped.write_text(payload, encoding='utf-8')
    latest.write_text(payload, encoding='utf-8')
    print(
        f"YAMA6_NATIVE_X64 status={report['status']} "
        f"passed={report['passed']} failed={failed}")
    print(f'REPORT={timestamped}')
    return 0 if failed == 0 else 3


if __name__ == '__main__':
    raise SystemExit(main())
