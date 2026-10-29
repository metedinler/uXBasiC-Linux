INCLUDE "include/modules/uxstats2.uxmh"

x = UXSTATS2_VecCreate(16)
y = UXSTATS2_VecCreate(16)
g = UXSTATS2_VecCreate(16)

UXSTATS2_VecPush(x, 1.0)
UXSTATS2_VecPush(x, 2.0)
UXSTATS2_VecPush(x, 3.0)
UXSTATS2_VecPush(x, 4.0)

UXSTATS2_VecPush(y, 2.0)
UXSTATS2_VecPush(y, 4.0)
UXSTATS2_VecPush(y, 6.0)
UXSTATS2_VecPush(y, 8.0)

UXSTATS2_VecPush(g, 1.0)
UXSTATS2_VecPush(g, 1.0)
UXSTATS2_VecPush(g, 2.0)
UXSTATS2_VecPush(g, 2.0)

PRINT UXSTATS2_OneSampleTP(x, 2.5)
PRINT UXSTATS2_WelchTP(x, y)
PRINT UXSTATS2_Correlation(x, y)
PRINT UXSTATS2_AnovaOneWayP(x, g)

UXSTATS2_VecFree(x)
UXSTATS2_VecFree(y)
UXSTATS2_VecFree(g)
