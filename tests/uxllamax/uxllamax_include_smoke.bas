INCLUDE "include/modules/uxllamax.uxmh"

DIM h AS U64
h = uxllamax.Create()
uxllamax.LowMemoryProfile(h, uxllamax.PROFILE_TINY)
PRINT uxllamax.Version()
PRINT uxllamax.ModelExists(h)
uxllamax.Free(h)
