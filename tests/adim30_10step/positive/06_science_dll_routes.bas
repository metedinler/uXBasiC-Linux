DECLARE FUNCTION ux_mean_f64 LIB "uxstats.dll" ALIAS "ux_mean_f64" ( _
    BYVAL data AS PTR, _
    BYVAL n AS I32 _
) AS F64

DECLARE FUNCTION ux_matmul_f64 LIB "uxmatrix.dll" ALIAS "ux_matmul_f64" ( _
    BYVAL a AS PTR, _
    BYVAL b AS PTR, _
    BYVAL c AS PTR, _
    BYVAL n AS I32 _
) AS I32

DECLARE FUNCTION ux_nn_forward LIB "uxnn.dll" ALIAS "ux_nn_forward" ( _
    BYVAL model AS PTR, _
    BYVAL input AS PTR, _
    BYVAL output AS PTR _
) AS I32

PRINT "SCIENCE DLL ROUTES"

CALL(DLL, "uxstats.dll", "ux_mean_f64", 0, 0)
CALL(DLL, "uxmatrix.dll", "ux_matmul_f64", 0, 0, 0, 0)
CALL(DLL, "uxnn.dll", "ux_nn_forward", 0, 0, 0)
