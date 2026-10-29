DIM tickValue AS I32
DIM processId AS I32
tickValue = CALL(DLL, "kernel32.dll", "GetTickCount", I32, CDECL)
processId = CALL(API, "kernel32.dll", "GetCurrentProcessId", I32, CDECL)
ASSERT tickValue >= 0
ASSERT processId > 0
