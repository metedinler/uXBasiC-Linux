OPEN "native_file_probe.bin" FOR BINARY AS #7
v = 287454020
PUT #7, 1, 4, v
SEEK #7, 1
v = 0
GET #7, 1, 4, v
CLOSE #7
PRINT v
