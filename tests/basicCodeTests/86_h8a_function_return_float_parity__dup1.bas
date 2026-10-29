#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 86: Function returning F64 and calling code

Private Sub Main()
    Dim src As String
    src = _
        "Function foo() As F64" & Chr(10) & _
        "  Return 3.14159" & Chr(10) & _
        "End Function" & Chr(10) & _
        "PRINT foo()"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 86 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 86 exec | "; errText
        End 1
    End If

    Print "DONE_86_AST"
    End 0
End Sub

Main
