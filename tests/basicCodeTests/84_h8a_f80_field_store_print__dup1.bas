#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 84: F80 field storage and print via x87->qword conversion

Private Sub Main()
    Dim src As String
    src = _
        "Type T" & Chr(10) & _
        "  v As F80" & Chr(10) & _
        "End Type" & Chr(10) & _
        "Dim t As T" & Chr(10) & _
        "t.v = 9.87654321" & Chr(10) & _
        "PRINT t.v"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 84 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 84 exec | "; errText
        End 1
    End If

    Print "DONE_84_AST"
    End 0
End Sub

Main
