' FILE_PRINT_STRICT
OPEN "reports/control/current/tmp_file_adim32b.txt" FOR OUTPUT AS #1
PRINT #1, "HELLO"
CLOSE #1
PRINT "DONE"
