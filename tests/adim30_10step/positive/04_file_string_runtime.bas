' ADIM30 POSITIVE 04 — file IO / runtime calls / string/math surface
DIM S AS STRING
S = "abc"
PRINT "STRING-LEN"
PRINT LEN(S)
RANDOMIZE 1
PRINT RND()
PRINT TIMER()
OPEN "reports/control/current/adim30_10step_chain/FILE_STRING_RUNTIME/tmp_file_io.txt" FOR OUTPUT AS #1
CLOSE #1
OPEN "reports/control/current/adim30_10step_chain/FILE_STRING_RUNTIME/tmp_file_io.txt" FOR INPUT AS #1
CLOSE #1
PRINT "FILE-OK"
