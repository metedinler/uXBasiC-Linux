INCLUDE "include/modules/uxnn3.uxmh"

ds = uxnn3.DatasetCreate(4, 2, 1)
uxnn3.XSet(ds, 0, 0, 0.0)
uxnn3.XSet(ds, 0, 1, 0.0)
uxnn3.YSet(ds, 0, 0, 0.0)

net = uxnn3.ModelCreate(2)
uxnn3.AddDense(net, 4, uxnn3.ACT_TANH)
uxnn3.AddDense(net, 1, uxnn3.ACT_SIGMOID)
uxnn3.Init(net, 1234, 0.0)
uxnn3.SetOptimizer(net, uxnn3.OPT_MOMENTUM, 0.1, 0.9)

PRINT uxnn3.LayerCount(net)
PRINT uxnn3.ModelOutputDim(net)

uxnn3.ModelFree(net)
uxnn3.DatasetFree(ds)
