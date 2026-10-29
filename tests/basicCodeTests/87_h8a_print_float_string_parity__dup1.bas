#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 87: PRINT and STR string parity for floats

Private Sub Main()
    Dim src As String
    src = _
        "Dim v As F64" & Chr(10) & _
        "v = 0.00012345" & Chr(10) & _
        "PRINT ""val=""; v" & Chr(10) & _
        "PRINT STR(v)"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 87 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 87 exec | "; errText
        End 1
    End If

    Print "DONE_87_AST"
    End 0
End Sub

Main
