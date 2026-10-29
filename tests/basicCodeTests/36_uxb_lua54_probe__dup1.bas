MAIN
L = CALL(DLL, "lua54.dll", "luaL_newstate", PTR, CDECL)
PRINT "luaL_newstate handle:"
PRINT L
CALL(DLL, "lua54.dll", "luaL_openlibs", PTR, CDECL, L)
CALL(DLL, "lua54.dll", "lua_close", PTR, CDECL, L)
END MAIN

