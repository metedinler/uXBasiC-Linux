OPEN "tests/adim36_full_surface/tmp/out21.bin" FOR BINARY AS #2
DIM A AS STRING
PUT #2, 1, "A"
SEEK #2, 1
GET #2, 1, A
CLOSE #2
PRINT "FILE_BINARY_SURFACE"
