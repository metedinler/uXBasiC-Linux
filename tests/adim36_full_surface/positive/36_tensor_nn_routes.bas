INCLUDE "tests/adim36_full_surface/includes/science_routes.uxbh"
CALL(DLL, "uxtensor.dll", "ux_tensor_create", 0, 0)
CALL(DLL, "uxnn.dll", "ux_nn_forward", 0, 0, 0)
PRINT "TENSOR_NN_ROUTE"
