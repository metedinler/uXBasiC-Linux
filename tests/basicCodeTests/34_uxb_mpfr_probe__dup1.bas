MAIN
tls = CALL(DLL, "libmpfr-6.dll", "mpfr_buildopt_tls_p", I32, CDECL)
PRINT "mpfr_buildopt_tls_p:"
PRINT tls
CALL(DLL, "libmpfr-6.dll", "mpfr_free_cache", BYVAL, CDECL)
END MAIN

