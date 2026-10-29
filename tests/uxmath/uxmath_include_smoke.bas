INCLUDE "include/modules/uxmath.uxmh"

DIM p AS U64

ASSERT UXMATH_Version() = 1001

p = UXMATH_VecCreate(4)
ASSERT UXMATH_VecPush(p, 1.0) = 1
ASSERT UXMATH_VecPush(p, 2.0) = 1
ASSERT UXMATH_VecPush(p, 3.0) = 1

ASSERT UXMATH_VecCount(p) = 3
ASSERT ABS(UXMATH_PolyEval(p, 2.0) - 17.0) < 0.000001
ASSERT ABS(UXMATH_PolyDerivativeEval(p, 2.0) - 14.0) < 0.000001
ASSERT ABS(UXMATH_PolyIntegralEval(p, 0.0, 1.0) - 3.0) < 0.000001
ASSERT ABS(UXMATH_Sigmoid(0.0) - 0.5) < 0.000001
ASSERT UXMATH_ODE_RK4_Logistic(1.0, 0.5, 100.0, 0.0, 10.0, 100) > 1.0

ASSERT UXMATH_VecFree(p) = 1
