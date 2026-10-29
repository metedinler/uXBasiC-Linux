OPEN "adim36_input_roundtrip.txt" FOR OUTPUT AS #1
PRINT #1, "HELLO_INPUT"
CLOSE #1

OPEN "adim36_input_roundtrip.txt" FOR INPUT AS #2
DIM S AS STRING
INPUT #2, S
CLOSE #2

PRINT S
