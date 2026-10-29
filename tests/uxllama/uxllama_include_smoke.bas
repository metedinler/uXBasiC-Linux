INCLUDE "include/modules/uxllama.uxmh"

h = uxllama.Create()
uxllama.LowMemoryProfile(h, uxllama.PROFILE_TINY)
PRINT uxllama.ModelExists(h)
uxllama.Free(h)
