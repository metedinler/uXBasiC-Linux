INCLUDE "include/modules/uxtensor.uxmh"

A = uxtensor.Create2D(2, 3)
B = uxtensor.Create2D(3, 2)

uxtensor.Set2D(A, 0, 0, 1.0)
uxtensor.Set2D(A, 0, 1, 2.0)
uxtensor.Set2D(A, 0, 2, 3.0)
uxtensor.Set2D(A, 1, 0, 4.0)
uxtensor.Set2D(A, 1, 1, 5.0)
uxtensor.Set2D(A, 1, 2, 6.0)

uxtensor.Set2D(B, 0, 0, 1.0)
uxtensor.Set2D(B, 0, 1, 2.0)
uxtensor.Set2D(B, 1, 0, 3.0)
uxtensor.Set2D(B, 1, 1, 4.0)
uxtensor.Set2D(B, 2, 0, 5.0)
uxtensor.Set2D(B, 2, 1, 6.0)

C = uxtensor.MatMul(A, B)
PRINT uxtensor.Get2D(C, 0, 0)
PRINT uxtensor.Get2D(C, 1, 1)

uxtensor.Free(A)
uxtensor.Free(B)
uxtensor.Free(C)
