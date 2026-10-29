INCLUDE "include/modules/uxdataframe.uxmh"

MAIN
    DIM frame AS U64
    DIM selected AS U64
    DIM matrix AS U64

    ASSERT uxdataframe.RuntimeVersion() = 1
    ASSERT uxdataframe.DuckDBAvailable() = 1
    ASSERT LEN(uxdataframe.DuckDBVersion()) > 0

    frame = uxdataframe.LoadCSV("dist/runtime_ext/uxdf_probe.csv", 1)
    ASSERT frame <> 0
    ASSERT uxdataframe.RowCount(frame) = 3
    ASSERT uxdataframe.ColCount(frame) = 4
    ASSERT uxdataframe.ColName(frame, 0) = "id"
    ASSERT ABS(uxdataframe.GetF64(frame, 1, 2) - 4.0) < 0.000001
    ASSERT uxdataframe.GetText(frame, 0, 3) = "A"

    selected = uxdataframe.SelectCols(frame, "x,y")
    ASSERT selected <> 0
    matrix = uxdataframe.ToF64Matrix(selected)
    ASSERT matrix <> 0
    ASSERT uxdataframe.MatrixRows(matrix) = 3
    ASSERT uxdataframe.MatrixCols(matrix) = 2
    ASSERT ABS(uxdataframe.MatrixGet(matrix, 0, 0) - 1.0) < 0.000001

    uxdataframe.MatrixFree(matrix)
    uxdataframe.Free(selected)
    uxdataframe.Free(frame)
    PRINT "PASS_UXDATAFRAME"
END MAIN
