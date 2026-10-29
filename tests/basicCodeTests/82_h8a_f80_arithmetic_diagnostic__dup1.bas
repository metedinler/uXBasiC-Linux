#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 82: F80 arithmetic should trigger x64 diagnostic (build fail expected)

Private Sub Main()
    Dim src As String
    src = _
        "Dim a As F80" & Chr(10) & _
        "Dim b As F80" & Chr(10) & _
        "a = 1.2345" & Chr(10) & _
        "b = 6.7890" & Chr(10) & _
        "Dim c As F80" & Chr(10) & _
        "c = a + b" & Chr(10) & _
        "PRINT c"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 82 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 82 exec | "; errText
        End 1
    End If

    Print "DONE_82_AST"
    End 0
End Sub

Main
