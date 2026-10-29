INCLUDE "include/modules/uxstats.uxmh"

DIM x AS U64
DIM y AS U64
x = UXSTATS_VecCreate(8)
y = UXSTATS_VecCreate(8)

UXSTATS_VecPush(x, 1.0)
UXSTATS_VecPush(y, 2.0)
UXSTATS_VecPush(x, 2.0)
UXSTATS_VecPush(y, 4.0)
UXSTATS_VecPush(x, 3.0)
UXSTATS_VecPush(y, 6.0)
UXSTATS_VecPush(x, 4.0)
UXSTATS_VecPush(y, 8.0)

PRINT UXSTATS_Correlation(x, y)
PRINT UXSTATS_RegressionSlope(x, y)
PRINT UXSTATS_RegressionIntercept(x, y)
PRINT UXSTATS_RegressionR2(x, y)

ASSERT ABS(UXSTATS_Correlation(x, y) - 1.0) < 0.000001
ASSERT ABS(UXSTATS_RegressionSlope(x, y) - 2.0) < 0.000001
ASSERT ABS(UXSTATS_RegressionIntercept(x, y)) < 0.000001
ASSERT ABS(UXSTATS_RegressionR2(x, y) - 1.0) < 0.000001

UXSTATS_VecFree(x)
UXSTATS_VecFree(y)
PRINT "PASS_UXSTATS_REGRESSION"
