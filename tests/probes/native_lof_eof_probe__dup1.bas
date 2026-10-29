OPEN "tests\\tmp_native_lof_probe.bin" FOR BINARY AS #1
PUT #1, 1, 4, 305419896
PRINT LOF(1)
PRINT EOF(1)
CLOSE #1
