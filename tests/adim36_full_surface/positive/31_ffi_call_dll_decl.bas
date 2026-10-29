DECLARE FUNCTION ux_add_i32 LIB "uxmath.dll" ALIAS "ux_add_i32" (BYVAL a AS I32, BYVAL b AS I32) AS I32
CALL(DLL, "uxmath.dll", "ux_add_i32", 1, 2)
PRINT "DLL_DECL_ROUTE"
