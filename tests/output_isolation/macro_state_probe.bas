#include once "../../src/preprocessor/preprocess_engine.fbs"
Dim resultA As PreprocessResult
Dim resultB As PreprocessResult
Dim sourceA As String = "%%DEFINE SENTINEL 77" & Chr(10) & "PRINT SENTINEL" & Chr(10)
Dim sourceB As String = "PRINT SENTINEL" & Chr(10)
Dim sourcePath As String = Command(1)
If PreprocessRun(sourceA, sourcePath, resultA) = 0 Then End 1
If Instr(resultA.expandedSource, "PRINT 77") = 0 Then End 2
If PreprocessRun(sourceB, sourcePath, resultB) = 0 Then End 3
If Instr(resultB.expandedSource, "PRINT SENTINEL") = 0 Then End 4
Print "MACRO_RUN_RESET_PASS"
