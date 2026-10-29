' CALL_DLL_AST_STRICT
DECLARE FUNCTION ux_mean_f64 LIB "uxstats.dll" ALIAS "ux_mean_f64" (BYVAL data AS PTR, BYVAL n AS I32) AS F64
CALL(DLL, "uxstats.dll", "ux_mean_f64", 0, 0)
PRINT "DLL-CALL"
