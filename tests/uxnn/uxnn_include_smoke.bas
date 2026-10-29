INCLUDE "include/modules/uxnn.uxmh"

DIM net AS U64
DIM l1 AS U64
DIM l2 AS U64

uxnn.Seed(1234)
net = uxnn.NetworkCreate()
l1 = uxnn.DenseLayerCreate(2, 4, uxnn.ACT_RELU)
l2 = uxnn.DenseLayerCreate(4, 1, uxnn.ACT_SIGMOID)
uxnn.LayerInit(l1, uxnn.INIT_XAVIER, 0.0)
uxnn.LayerInit(l2, uxnn.INIT_XAVIER, 0.0)
uxnn.NetworkAddLayer(net, l1)
uxnn.NetworkAddLayer(net, l2)
PRINT uxnn.NetworkLayerCount(net)
uxnn.NetworkFree(net)
