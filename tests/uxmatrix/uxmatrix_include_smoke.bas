INCLUDE "include/modules/uxmatrix.uxmh"

DIM A AS U64
DIM B AS U64
DIM C AS U64

A = uxmatrix.Create(2, 2)
B = uxmatrix.Create(2, 2)

uxmatrix.Set(A, 0, 0, 1.0)
uxmatrix.Set(A, 0, 1, 2.0)
uxmatrix.Set(A, 1, 0, 3.0)
uxmatrix.Set(A, 1, 1, 4.0)

uxmatrix.Set(B, 0, 0, 5.0)
uxmatrix.Set(B, 0, 1, 6.0)
uxmatrix.Set(B, 1, 0, 7.0)
uxmatrix.Set(B, 1, 1, 8.0)

C = uxmatrix.Mul(A, B)
PRINT uxmatrix.Get(C, 0, 0)
PRINT uxmatrix.Get(C, 1, 1)
PRINT uxmatrix.Trace(A)

uxmatrix.Free(A)
uxmatrix.Free(B)
uxmatrix.Free(C)
