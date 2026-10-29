#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 83: F64 print parity (STR/PRINT path)

Private Sub Main()
    Dim src As String
    src = _
        "Dim x As F64" & Chr(10) & _
        "x = 12345.6789" & Chr(10) & _
        "PRINT x" & Chr(10) & _
        "PRINT STR(x)"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 83 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 83 exec | "; errText
        End 1
    End If

    Print "DONE_83_AST"
    End 0
End Sub

Main
