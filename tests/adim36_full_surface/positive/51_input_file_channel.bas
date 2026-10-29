OPEN "adim36_input_channel.txt" FOR OUTPUT AS #1
PRINT #1, "41"
PRINT #1, "82"
CLOSE #1

DIM a AS I32
DIM b AS I32

OPEN "adim36_input_channel.txt" FOR INPUT AS #1
INPUT #1, a
INPUT #1, b
CLOSE #1

PRINT a
PRINT b
