MAIN
ok = CALL(DLL, "winhttp.dll", "WinHttpCheckPlatform", I32, STDCALL)
PRINT "WinHttpCheckPlatform:"
PRINT ok
END MAIN
