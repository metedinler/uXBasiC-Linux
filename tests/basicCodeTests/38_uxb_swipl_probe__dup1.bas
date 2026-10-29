MAIN
ok0 = CALL(DLL, "libswipl.dll", "PL_is_initialised", PTR, CDECL, 0, 0)
PRINT "PL_is_initialised before:"
PRINT ok0
ok1 = CALL(DLL, "libswipl.dll", "PL_initialise", PTR, CDECL, 0, 0)
PRINT "PL_initialise:"
PRINT ok1
CALL(DLL, "libswipl.dll", "PL_cleanup", PTR, CDECL, 0)
END MAIN

