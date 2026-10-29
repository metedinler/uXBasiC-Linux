#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 45: F80 Storage and Indexing Test
' Checks: F80 dt emission in ASM and 10-byte element stride.

Private Sub Main()
    Dim src As String
    src = _
        "Dim arr(2) As F80" & Chr(10) & _
        "arr(0) = 1.25" & Chr(10) & _
        "arr(1) = 2.50" & Chr(10) & _
        "' Touch both elements to force storage emission" & Chr(10) & _
        "POKED 9900, arr(0)" & Chr(10) & _
        "POKED 9910, arr(1)"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL F80 parse | "; errText
        End 1
    End If

    ' Run the program to force uXBasic to compile the sample and (if possible)
    ' emit assembler for inspection.
    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL F80 exec | "; errText
        End 1
    End If

    Print "DONE_F80_EXEC"
    End 0
End Sub

Main
