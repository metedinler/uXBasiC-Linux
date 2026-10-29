OPEN "dist/adim36_input_roundtrip.txt" FOR OUTPUT AS #1
PRINT #1, "HELLO_INPUT"
CLOSE #1
DIM S AS STRING
OPEN "dist/adim36_input_roundtrip.txt" FOR INPUT AS #2
INPUT #2, S
CLOSE #2
PRINT S
