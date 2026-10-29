INCLUDE "include/modules/uxonnx.uxmh"

ok = uxonnx.Init("uxb\\dist\\runtime_ext\\deps\\uxonnx")
PRINT ok
PRINT uxonnx.Version()

t = uxonnx.TensorCreate2D(1, 3)
uxonnx.TensorSet(t, 0, 1.0)
uxonnx.TensorSet(t, 1, 2.0)
uxonnx.TensorSet(t, 2, 3.0)
PRINT uxonnx.TensorCount(t)
PRINT uxonnx.TensorGet(t, 2)
uxonnx.TensorFree(t)
