INCLUDE "include/modules/uxmathcore.uxmh"

v1 = UXMC_BufferCreate(UXMC_TYPE_F64(), 0)
v2 = UXMC_BufferCreate(UXMC_TYPE_F64(), 0)
outv = UXMC_BufferCreate(UXMC_TYPE_F64(), 0)

UXMC_PushF64(v1, 1.0)
UXMC_PushF64(v1, 2.0)
UXMC_PushF64(v1, 3.0)

UXMC_PushF64(v2, 10.0)
UXMC_PushF64(v2, 20.0)
UXMC_PushF64(v2, 30.0)

UXMC_VecAddF64(v1, v2, outv)
PRINT UXMC_GetF64(outv, 2)
PRINT UXMC_VecDotF64(v1, v2)
PRINT UXMC_VecL2NormF64(v1)

UXMC_BufferFree(v1)
UXMC_BufferFree(v2)
UXMC_BufferFree(outv)
