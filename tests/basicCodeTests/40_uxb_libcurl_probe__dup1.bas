MAIN
rc = CALL(DLL, "libcurl.dll", "curl_global_init", I32, CDECL, 3)
h = CALL(DLL, "libcurl.dll", "curl_easy_init", PTR, CDECL)
PRINT "curl_global_init:"
PRINT rc
PRINT "curl_easy_init handle:"
PRINT h
CALL(DLL, "libcurl.dll", "curl_easy_cleanup", PTR, CDECL, h)
CALL(DLL, "libcurl.dll", "curl_global_cleanup", BYVAL, CDECL)
END MAIN

