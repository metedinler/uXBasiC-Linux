#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REQUIRED = [
    'uxb_rt_init', 'uxb_rt_shutdown', 'uxb_rt_backend',
    'uxb_task_register', 'uxb_slot_bind', 'uxb_task_set_callback',
    'uxb_slot_control', 'uxb_task_on', 'uxb_task_off',
    'uxb_slot_on', 'uxb_slot_off', 'uxb_task_trigger',
    'uxb_shell_run', 'uxb_thread_start', 'uxb_pipe_run',
    'uxb_parallel_run', 'uxb_shell_start', 'uxb_text_file_write',
    'uxb_last_error',
]

CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_void_p,
)


def configure(dll: ctypes.CDLL) -> None:
    dll.uxb_rt_init.argtypes = []
    dll.uxb_rt_init.restype = ctypes.c_int
    dll.uxb_rt_shutdown.argtypes = []
    dll.uxb_rt_shutdown.restype = ctypes.c_int
    dll.uxb_rt_backend.argtypes = [ctypes.c_char_p, ctypes.c_int]
    dll.uxb_rt_backend.restype = ctypes.c_int
    dll.uxb_task_register.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    dll.uxb_task_register.restype = ctypes.c_int
    dll.uxb_slot_bind.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    dll.uxb_slot_bind.restype = ctypes.c_int
    dll.uxb_task_set_callback.argtypes = [ctypes.c_int, CALLBACK, ctypes.c_void_p]
    dll.uxb_task_set_callback.restype = ctypes.c_int
    dll.uxb_slot_control.argtypes = [ctypes.c_int, ctypes.c_int]
    dll.uxb_slot_control.restype = ctypes.c_int
    for name in ('uxb_task_trigger', 'uxb_thread_start', 'uxb_pipe_run', 'uxb_parallel_run'):
        fn = getattr(dll, name)
        fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        fn.restype = ctypes.c_int
    dll.uxb_shell_run.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
    ]
    dll.uxb_shell_run.restype = ctypes.c_int
    dll.uxb_shell_start.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.c_char_p, ctypes.POINTER(ctypes.c_int),
    ]
    dll.uxb_shell_start.restype = ctypes.c_int
    dll.uxb_text_file_write.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    dll.uxb_text_file_write.restype = ctypes.c_int
    dll.uxb_last_error.argtypes = []
    dll.uxb_last_error.restype = ctypes.c_char_p


def last_error(dll: ctypes.CDLL) -> str:
    value = dll.uxb_last_error()
    return value.decode('utf-8', errors='replace') if value else ''


def run_behavior_smoke(dll_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {'status': 'FAIL', 'checks': {}}
    dll_dir = str(dll_path.parent)
    old_path = os.environ.get('PATH', '')
    os.environ['PATH'] = dll_dir + os.pathsep + old_path
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(dll_dir)
    dll = ctypes.CDLL(str(dll_path))
    configure(dll)

    callbacks: list[Any] = []

    @CALLBACK
    def pipe_callback(slot_id: int, input_value: int, output_ptr: Any, _user_data: Any) -> int:
        if not output_ptr:
            return 0
        output_ptr[0] = input_value * 2
        return 1

    callbacks.append(pipe_callback)

    def check(name: str, condition: bool, detail: Any = '') -> None:
        result['checks'][name] = {'pass': bool(condition), 'detail': detail}

    try:
        check('init', dll.uxb_rt_init() == 1, last_error(dll))
        backend = ctypes.create_string_buffer(128)
        backend_ok = dll.uxb_rt_backend(backend, len(backend)) == 1
        check('backend', backend_ok and bool(backend.value), backend.value.decode(errors='replace'))

        check('register_slot_3', dll.uxb_task_register(3, 2, b'VeriHatti') == 1, last_error(dll))
        check('bind_callback', dll.uxb_task_set_callback(3, pipe_callback, None) == 1, last_error(dll))
        output = ctypes.c_int(0)
        check('pipe_output_42', dll.uxb_pipe_run(3, 21, ctypes.byref(output)) == 1 and output.value == 42, output.value)

        check('slot_off', dll.uxb_slot_control(3, 0) == 1, last_error(dll))
        output.value = -1
        off_rc = dll.uxb_pipe_run(3, 21, ctypes.byref(output))
        check('off_fail_closed', off_rc == 0, last_error(dll))
        check('slot_on', dll.uxb_slot_control(3, 1) == 1, last_error(dll))

        check('slot_255_valid', dll.uxb_task_register(255, 3, b'Boundary') == 1, last_error(dll))
        check('slot_256_rejected', dll.uxb_task_register(256, 3, b'Invalid') == 0, last_error(dll))

        stdout_buf = ctypes.create_string_buffer(65536)
        stderr_buf = ctypes.create_string_buffer(65536)
        exit_code = ctypes.c_int(-999)
        shell_cmd = b'cmd /c echo UXB_SHELL_OK' if os.name == 'nt' else b'printf UXB_SHELL_OK'
        shell_rc = dll.uxb_shell_run(
            shell_cmd, b'', 10000,
            stdout_buf, len(stdout_buf),
            stderr_buf, len(stderr_buf),
            ctypes.byref(exit_code),
        )
        shell_out = stdout_buf.value.decode('utf-8', errors='replace')
        shell_err = stderr_buf.value.decode('utf-8', errors='replace')
        check('shell_capture', shell_rc == 1 and exit_code.value == 0 and 'UXB_SHELL_OK' in shell_out,
              {'rc': shell_rc, 'exit': exit_code.value, 'stdout': shell_out, 'stderr': shell_err})

        write_path = dll_path.parent / 'uxb_runtime_write_test.txt'
        try:
            write_path.unlink(missing_ok=True)
            write_rc = dll.uxb_text_file_write(
                os.fsencode(write_path), b'UXB_WRITE_OK\n')
            write_text = write_path.read_text(encoding='utf-8') if write_path.is_file() else ''
            check('text_file_write', write_rc == 1 and write_text == 'UXB_WRITE_OK\n',
                  {'rc': write_rc, 'text': write_text})
        finally:
            write_path.unlink(missing_ok=True)

        nowait_path = dll_path.parent / 'uxb_runtime_nowait_test.txt'
        try:
            nowait_path.unlink(missing_ok=True)
            nowait_exit = ctypes.c_int(-999)
            nowait_rc = dll.uxb_shell_start(
                b'cmd /c echo UXB_NOWAIT_OK', b'', os.fsencode(nowait_path), b'',
                ctypes.byref(nowait_exit))
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                if nowait_path.is_file() and 'UXB_NOWAIT_OK' in nowait_path.read_text(
                        encoding='utf-8', errors='replace'):
                    break
                time.sleep(0.05)
            nowait_text = nowait_path.read_text(
                encoding='utf-8', errors='replace') if nowait_path.is_file() else ''
            check('shell_nowait', nowait_rc == 1 and nowait_exit.value == 0
                  and 'UXB_NOWAIT_OK' in nowait_text,
                  {'rc': nowait_rc, 'exit': nowait_exit.value, 'stdout': nowait_text})
        finally:
            nowait_path.unlink(missing_ok=True)
    finally:
        shutdown_rc = dll.uxb_rt_shutdown()
        check('shutdown', shutdown_rc == 1, shutdown_rc)

    result['status'] = 'PASS' if all(item['pass'] for item in result['checks'].values()) else 'FAIL'
    return result


def find_root(value: str) -> Path:
    start = Path(value).resolve()
    for p in (start, *start.parents):
        if (p / 'src').is_dir() and (p / 'native' / 'uxb_runtime').is_dir():
            return p
        if (p / 'uxb' / 'src').is_dir():
            return p / 'uxb'
    for p in Path(__file__).resolve().parents:
        if (p / 'src').is_dir() and (p / 'native' / 'uxb_runtime').is_dir():
            return p
    raise SystemExit(f'uXBasic root bulunamadi: {start}')

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--expect-backend', default='')
    args = parser.parse_args()
    root = find_root(args.root)
    dll_path = root / 'bin' / 'uxb_runtime.dll'
    report: dict[str, Any] = {
        'schema': 'uxb.yama6.runtime.v2',
        'dll': str(dll_path),
        'status': 'FAIL',
        'exports': {},
        'behavior': {},
    }
    report_dir = root / 'reports' / 'yama6_runtime'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / 'runtime_dll_check.json'

    if not dll_path.is_file():
        report['error'] = f'missing {dll_path}'
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print('ERROR: ' + report['error'])
        return 2

    objdump_candidates = [
        Path(r'C:\msys64\ucrt64\bin\objdump.exe'),
        Path(r'C:\msys64\ucrt64\bin\x86_64-w64-mingw32-objdump.exe'),
    ]
    objdump = next((path for path in objdump_candidates if path.is_file()), None)
    if objdump is None:
        report['error'] = 'objdump missing'
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print('ERROR: objdump missing')
        return 3

    text = subprocess.check_output([str(objdump), '-p', str(dll_path)], text=True, errors='replace')
    for name in REQUIRED:
        report['exports'][name] = name in text
    if not all(report['exports'].values()):
        report['error'] = 'required export missing'
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print('YAMA6_RUNTIME status=FAIL export check')
        return 4

    try:
        report['behavior'] = run_behavior_smoke(dll_path)
    except Exception as exc:  # noqa: BLE001 - report exact loader/runtime failure
        report['behavior'] = {'status': 'FAIL', 'error': repr(exc)}

    if args.expect_backend:
        backend_detail = report.get('behavior', {}).get('checks', {}).get('backend', {}).get('detail', '')
        report['expected_backend'] = args.expect_backend
        report['backend_match'] = args.expect_backend.lower() in str(backend_detail).lower()
    else:
        report['backend_match'] = True
    report['status'] = 'PASS' if report['behavior'].get('status') == 'PASS' and report['backend_match'] else 'FAIL'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('YAMA6_RUNTIME status=' + report['status'])
    return 0 if report['status'] == 'PASS' else 5


if __name__ == '__main__':
    raise SystemExit(main())
