DECLARE FUNCTION ux_stddev_f64 LIB "uxstats2.dll" ALIAS "ux_stddev_f64" (BYVAL data AS PTR, BYVAL n AS I32) AS F64
CALL(DLL, "uxstats2.dll", "ux_stddev_f64", 0, 0)
PRINT "STATS2_ROUTE"
