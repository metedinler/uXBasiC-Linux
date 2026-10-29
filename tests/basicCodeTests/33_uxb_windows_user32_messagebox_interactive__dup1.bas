MAIN
rc = CALL(DLL, "user32.dll", "MessageBoxA", I32, STDCALL, "PTR,STRPTR,STRPTR,I32", 0, "uXBasic GUI smoke", "uXBasic", 0)
PRINT "MessageBoxA return:"
PRINT rc
END MAIN
