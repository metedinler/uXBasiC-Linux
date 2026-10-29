MAIN
t0 = CALL(DLL, "kernel32.dll", "GetTickCount", I32)
CALL(DLL, "kernel32.dll", "Sleep", I32, STDCALL, 25)
t1 = CALL(DLL, "kernel32.dll", "GetTickCount", I32)
delta = t1 - t0
PRINT "delta:"
PRINT delta
PRINT "tick:"
PRINT t1
END MAIN
