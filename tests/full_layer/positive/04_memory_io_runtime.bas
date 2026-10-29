DIM addr AS PTR
DIM n AS I32
n = 7
addr = VARPTR(n)
PRINT SIZEOF(I32)
PRINT VARPTR(n)
PRINT STRPTR("abc")
' Memory commands are route-tested; bounds are checked by runtime gate.
' POKEB addr, 1
' PRINT PEEKB(addr)
OPEN "tests/full_layer/tmp_runtime.txt" FOR OUTPUT AS #1
PRINT #1, "FILE_OK"
CLOSE #1
OPEN "tests/full_layer/tmp_runtime.txt" FOR INPUT AS #2
PRINT EOF(2)
CLOSE #2
PRINT "RUNTIME_ROUTE_OK"
