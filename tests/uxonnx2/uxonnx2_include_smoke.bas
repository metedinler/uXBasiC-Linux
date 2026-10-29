INCLUDE "include/modules/uxonnx2.uxmh"

ok = uxonnx2.Init("uxb\\dist\\runtime_ext\\deps\\uxonnx2")
PRINT ok
PRINT uxonnx2.Version()

t = uxonnx2.TensorCreate2D(uxonnx2.DTYPE_F32, 1, 4)
uxonnx2.TensorSetF64(t, 0, 1.25)
uxonnx2.TensorSetF64(t, 3, 9.5)
PRINT uxonnx2.TensorRank(t)
PRINT uxonnx2.TensorCount(t)
PRINT uxonnx2.TensorGetF64(t, 0)
PRINT uxonnx2.TensorGetF64(t, 3)
uxonnx2.TensorFree(t)
