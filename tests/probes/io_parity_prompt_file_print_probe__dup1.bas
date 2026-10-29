INPUT "A?"; a
INPUT b

PRINT 1,
PRINT "12345678901234",
PRINT 1;
PRINT 12, 3;

OPEN "tests\tmp_io_parity_probe.bin" FOR BINARY AS #1
v = 287454020
PUT #1, 1, 4, v
SEEK #1, 1
v = 0
GET #1, 1, 4, v
CLOSE #1

OPEN "tests\tmp_io_parity_probe.bin" FOR BINARY AS #1
INPUT #1, c
CLOSE #1

PRINT a, b;
PRINT c
PRINT v, c
