OPEN "adim36_bad_input_target.txt" FOR OUTPUT AS #1
PRINT #1, "7"
CLOSE #1

OPEN "adim36_bad_input_target.txt" FOR INPUT AS #1
INPUT #1, 9
CLOSE #1
