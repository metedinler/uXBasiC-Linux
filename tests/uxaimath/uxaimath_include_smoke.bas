INCLUDE "include/modules/uxtensor.uxmh"
INCLUDE "include/modules/uxaimath.uxmh"

uxaimath.Seed(12345)

DIM x AS U64
DIM y AS U64

x = uxtensor.Create1D(4)
y = uxtensor.Create1D(4)

uxtensor.SetFlat(x, 0, -1.0)
uxtensor.SetFlat(x, 1, 0.0)
uxtensor.SetFlat(x, 2, 1.0)
uxtensor.SetFlat(x, 3, 2.0)

uxaimath.TensorSoftmax(x, y)
PRINT uxtensor.Sum(y)

uxaimath.TensorReLU(x)
PRINT uxtensor.GetFlat(x, 0)
PRINT uxaimath.Sigmoid(0.0)

uxtensor.Free(x)
uxtensor.Free(y)
