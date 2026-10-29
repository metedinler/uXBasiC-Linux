INCLUDE "include/modules/uxdataset.uxmh"

ds = uxdataset.Create(4, 2, 1)
uxdataset.SetX(ds, 0, 0, 1.0)
uxdataset.SetX(ds, 0, 1, 2.0)
uxdataset.SetY(ds, 0, 0, 1.0)
PRINT uxdataset.RowCount(ds)
PRINT uxdataset.InputDim(ds)
PRINT uxdataset.GetX(ds, 0, 1)
uxdataset.Free(ds)
