import ctypes
import math
import os
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
DLL = ROOT / "dist" / "runtime_ext" / "uxmatrix.dll"
_dll_directory_handles = []
if os.name == "nt":
    for directory in (DLL.parent, ROOT / "dist" / "libraries" / "deps", ROOT / "bin"):
        if directory.is_dir():
            _dll_directory_handles.append(os.add_dll_directory(str(directory)))
lib = ctypes.CDLL(str(DLL))

Handle = ctypes.c_void_p
HandlePtr = ctypes.POINTER(Handle)

lib.uxmatrix_create.argtypes = [ctypes.c_int, ctypes.c_int]
lib.uxmatrix_create.restype = Handle
lib.uxmatrix_free.argtypes = [Handle]
lib.uxmatrix_rows.argtypes = [Handle]
lib.uxmatrix_rows.restype = ctypes.c_int
lib.uxmatrix_cols.argtypes = [Handle]
lib.uxmatrix_cols.restype = ctypes.c_int
lib.uxmatrix_set.argtypes = [Handle, ctypes.c_int, ctypes.c_int, ctypes.c_double]
lib.uxmatrix_set.restype = ctypes.c_int
lib.uxmatrix_get.argtypes = [Handle, ctypes.c_int, ctypes.c_int]
lib.uxmatrix_get.restype = ctypes.c_double
lib.uxmatrix_det.argtypes = [Handle]
lib.uxmatrix_det.restype = ctypes.c_double
lib.uxmatrix_solve.argtypes = [Handle, Handle, HandlePtr]
lib.uxmatrix_solve.restype = ctypes.c_int
lib.uxmatrix_inverse.argtypes = [Handle, HandlePtr]
lib.uxmatrix_inverse.restype = ctypes.c_int
lib.uxmatrix_cholesky.argtypes = [Handle, HandlePtr]
lib.uxmatrix_cholesky.restype = ctypes.c_int
lib.uxmatrix_qr.argtypes = [Handle, HandlePtr, HandlePtr]
lib.uxmatrix_qr.restype = ctypes.c_int
lib.uxmatrix_svd.argtypes = [Handle, HandlePtr, HandlePtr, HandlePtr]
lib.uxmatrix_svd.restype = ctypes.c_int
lib.uxmatrix_eigen_symmetric.argtypes = [Handle, HandlePtr, HandlePtr]
lib.uxmatrix_eigen_symmetric.restype = ctypes.c_int
lib.uxmatrix_rank_svd.argtypes = [Handle, ctypes.c_double]
lib.uxmatrix_rank_svd.restype = ctypes.c_int
lib.uxmatrix_cond2.argtypes = [Handle]
lib.uxmatrix_cond2.restype = ctypes.c_double
for name in ("uxmatrix_solve_new", "uxmatrix_inverse_new", "uxmatrix_cholesky_new"):
    getattr(lib, name).restype = Handle
lib.uxmatrix_solve_new.argtypes = [Handle, Handle]
lib.uxmatrix_inverse_new.argtypes = [Handle]
lib.uxmatrix_cholesky_new.argtypes = [Handle]


allocated = []


def matrix(values):
    rows = len(values)
    cols = len(values[0])
    handle = lib.uxmatrix_create(rows, cols)
    assert handle
    allocated.append(handle)
    for row in range(rows):
        assert len(values[row]) == cols
        for col in range(cols):
            assert lib.uxmatrix_set(handle, row, col, float(values[row][col])) == 1
    return handle


def remember(handle):
    assert handle
    allocated.append(handle)
    return handle


def values(handle):
    return [
        [lib.uxmatrix_get(handle, row, col) for col in range(lib.uxmatrix_cols(handle))]
        for row in range(lib.uxmatrix_rows(handle))
    ]


def multiply(left, right):
    assert len(left[0]) == len(right)
    return [
        [sum(left[row][k] * right[k][col] for k in range(len(right))) for col in range(len(right[0]))]
        for row in range(len(left))
    ]


def transpose(source):
    return [list(row) for row in zip(*source)]


def assert_close(actual, expected, tolerance=1.0e-7):
    assert math.isfinite(actual), actual
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_matrix_close(actual, expected, tolerance=1.0e-7):
    assert len(actual) == len(expected)
    assert len(actual[0]) == len(expected[0])
    for row in range(len(actual)):
        for col in range(len(actual[0])):
            assert_close(actual[row][col], expected[row][col], tolerance)


try:
    a_values = [[4.0, 7.0], [2.0, 6.0]]
    a = matrix(a_values)
    b = matrix([[1.0], [0.0]])
    assert_close(lib.uxmatrix_det(a), 10.0)

    solution = Handle()
    assert lib.uxmatrix_solve(a, b, ctypes.byref(solution)) == 1
    remember(solution.value)
    assert_matrix_close(values(solution), [[0.6], [-0.2]])

    inverse = Handle()
    assert lib.uxmatrix_inverse(a, ctypes.byref(inverse)) == 1
    remember(inverse.value)
    assert_matrix_close(multiply(a_values, values(inverse)), [[1.0, 0.0], [0.0, 1.0]])
    remember(lib.uxmatrix_solve_new(a, b))
    remember(lib.uxmatrix_inverse_new(a))

    spd_values = [[4.0, 2.0], [2.0, 3.0]]
    spd = matrix(spd_values)
    lower = Handle()
    assert lib.uxmatrix_cholesky(spd, ctypes.byref(lower)) == 1
    remember(lower.value)
    lower_values = values(lower)
    assert_matrix_close(multiply(lower_values, transpose(lower_values)), spd_values)
    remember(lib.uxmatrix_cholesky_new(spd))

    tall_values = [[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]]
    tall = matrix(tall_values)
    q, r = Handle(), Handle()
    assert lib.uxmatrix_qr(tall, ctypes.byref(q), ctypes.byref(r)) == 1
    remember(q.value); remember(r.value)
    assert_matrix_close(multiply(values(q), values(r)), tall_values, 1.0e-6)

    u, singular, vt = Handle(), Handle(), Handle()
    assert lib.uxmatrix_svd(tall, ctypes.byref(u), ctypes.byref(singular), ctypes.byref(vt)) == 1
    remember(u.value); remember(singular.value); remember(vt.value)
    u_values, s_values, vt_values = values(u), values(singular), values(vt)
    sigma = [[s_values[0][0], 0.0], [0.0, s_values[1][0]], [0.0, 0.0]]
    assert_matrix_close(multiply(multiply(u_values, sigma), vt_values), tall_values, 1.0e-5)
    assert lib.uxmatrix_rank_svd(tall, 1.0e-9) == 2
    condition = lib.uxmatrix_cond2(tall)
    assert math.isfinite(condition) and condition > 1.0

    eigenvalues, eigenvectors = Handle(), Handle()
    assert lib.uxmatrix_eigen_symmetric(spd, ctypes.byref(eigenvalues), ctypes.byref(eigenvectors)) == 1
    remember(eigenvalues.value); remember(eigenvectors.value)
    lambdas, vectors = values(eigenvalues), values(eigenvectors)
    for col in range(2):
        vector = [[vectors[row][col]] for row in range(2)]
        lhs = multiply(spd_values, vector)
        rhs = [[lambdas[col][0] * vector[row][0]] for row in range(2)]
        assert_matrix_close(lhs, rhs, 1.0e-6)

    print("PASS_UXMATRIX_COMPLETE")
finally:
    for handle in reversed(allocated):
        if handle:
            lib.uxmatrix_free(handle)

sys.exit(0)
