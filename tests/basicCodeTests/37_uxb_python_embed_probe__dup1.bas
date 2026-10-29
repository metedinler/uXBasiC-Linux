MAIN
CALL(DLL, "python313.dll", "Py_Initialize", BYVAL, CDECL)
ok = CALL(DLL, "python313.dll", "Py_IsInitialized", I32, CDECL)
PRINT "Py_IsInitialized:"
PRINT ok
CALL(DLL, "python313.dll", "Py_FinalizeEx", I32, CDECL)
END MAIN

