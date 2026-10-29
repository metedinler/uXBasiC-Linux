"""Validate the real length-bearing memory/C ABI and persistent text ownership."""
import argparse
import ctypes as C
import hashlib
import json
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--dll', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--null-slot-probe', action='store_true', help='Internal child: a null destination must raise a runtime error')
args = parser.parse_args()
path = Path(args.dll).resolve()
dll = C.CDLL(str(path))

def api(name, result, *parameters):
    fn = getattr(dll, '__uxb_rt_' + name)
    fn.restype, fn.argtypes = result, list(parameters)
    return fn

read = api('mem_read_sequence', C.c_void_p, C.c_void_p, C.c_int64)
write = api('mem_write_sequence', C.c_int64, C.c_void_p, C.c_void_p, C.c_int64)
length = api('strlen', C.c_int64, C.c_void_p)
store = api('str_store', C.c_int64, C.POINTER(C.c_void_p), C.c_void_p)
release = api('str_release', C.c_int64, C.POINTER(C.c_void_p))
compare = api('str_compare', C.c_int64, C.c_void_p, C.c_void_p)
repeat = api('string_text', C.c_void_p, C.c_int64, C.c_void_p)
chr_byte = api('chr', C.c_void_p, C.c_int64)
if args.null_slot_probe:
    store(None, None)
    raise SystemExit(0)
records = []

def check(name, condition):
    records.append({'case': name, 'passed': bool(condition)})

payload = C.create_string_buffer(b'A\0B\0C')
span = read(payload, 5)
check('explicit_span_length', length(span) == 5)
left, right = C.c_void_p(), C.c_void_p()
check('persistent_copy', store(C.byref(left), span) == 1 and length(left) == 5)
owned_address = left.value
check('self_store_is_success', store(C.byref(left), left) == 1 and left.value == owned_address and length(left) == 5)
check('copy_alias', store(C.byref(right), left) == 1 and length(right) == 5)
check('compare_beyond_nul', compare(left, C.cast(C.create_string_buffer(b'A'), C.c_void_p)) > 0)
for i in range(96):
    chr_byte(i)
check('ring_wrap_preserves_owned_length', length(left) == 5 and length(right) == 5)
check('release_original', release(C.byref(left)) == 1 and not left.value and length(right) == 5)
out = C.create_string_buffer(5)
check('span_write', write(out, right, 5) == 5 and out.raw == b'A\0B\0C')
check('nul_character_is_nonempty', length(repeat(4, chr_byte(0))) == 4)
check('foreign_zstring_boundary', length(C.cast(payload, C.c_void_p)) == 1)
check('release_alias', release(C.byref(right)) == 1 and not right.value)
resize = api('array_resize', C.c_int64, C.POINTER(C.c_int64), C.c_int64, C.c_int64, C.c_uint64)
descriptor = (C.c_int64 * 3)(0, 0, -1)
identity = C.addressof(descriptor)
check('resize_allocate', resize(descriptor, -1, 1, 8) == 3)
cells = C.cast(descriptor[0], C.POINTER(C.c_int64))
cells[0], cells[1], cells[2] = 10, 20, 30
check('resize_grow', resize(descriptor, -2, 2, 8 | (1 << 32)) == 5)
cells = C.cast(descriptor[0], C.POINTER(C.c_int64))
check('preserve_logical_indices', list(cells[:5]) == [0, 10, 20, 30, 0])
check('descriptor_identity', C.addressof(descriptor) == identity and list(descriptor[1:]) == [-2, 2])
check('resize_shrink', resize(descriptor, 0, 0, 8 | (1 << 32)) == 1)
check('shrink_keeps_intersection', C.cast(descriptor[0], C.POINTER(C.c_int64))[0] == 20)
check('resize_clear', resize(descriptor, 0, 0, 8) == 1 and C.cast(descriptor[0], C.POINTER(C.c_int64))[0] == 0)
register = api('register_string_literals', C.c_int64, C.POINTER(C.c_int64), C.c_int64)
literal = C.create_string_buffer(b'L\0T')
pairs = (C.c_int64 * 2)(C.addressof(literal), 3)
check('literal_span_registration', register(pairs, 1) == 1 and length(C.cast(literal, C.c_void_p)) == 3)
child = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--dll', str(path),
                        '--output', args.output, '--null-slot-probe'], capture_output=True, timeout=15)
check('null_slot_is_runtime_error', child.returncode != 0 and b'STRING destination slot is null' in child.stdout + child.stderr)
report = {'dll': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'total': len(records), 'passed': sum(r['passed'] for r in records), 'results': records}
Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(f"Native span ABI: {report['passed']}/{report['total']}")
raise SystemExit(0 if all(r['passed'] for r in records) else 1)
