INCLUDE "include/modules/uxnn2.uxmh"

uxnn2.Seed(1234)
net = uxnn2.NetworkCreate(2)
uxnn2.AddDense(net, 4, uxnn2.ACT_RELU)
uxnn2.AddDense(net, 1, uxnn2.ACT_SIGMOID)
uxnn2.Init(net, uxnn2.INIT_XAVIER, 0.0)
PRINT uxnn2.LayerCount(net)
PRINT uxnn2.OutputDim(net)
uxnn2.NetworkFree(net)
