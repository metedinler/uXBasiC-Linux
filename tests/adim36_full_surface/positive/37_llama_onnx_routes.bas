INCLUDE "tests/adim36_full_surface/includes/science_routes.uxbh"
CALL(DLL, "uxonnx.dll", "ux_onnx_run", 0, 0, 0)
CALL(DLL, "uxllama.dll", "ux_llama_eval", 0, "hello")
PRINT "LLAMA_ONNX_ROUTE"
