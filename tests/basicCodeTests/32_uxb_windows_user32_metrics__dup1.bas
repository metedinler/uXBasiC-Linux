MAIN
screenW = CALL(DLL, "user32.dll", "GetSystemMetrics", I32, STDCALL, 0)
screenH = CALL(DLL, "user32.dll", "GetSystemMetrics", I32, STDCALL, 1)
CALL(DLL, "user32.dll", "MessageBeep", I32, STDCALL, 0)
PRINT "user32 screen width:"
PRINT screenW
PRINT "user32 screen height:"
PRINT screenH
END MAIN

