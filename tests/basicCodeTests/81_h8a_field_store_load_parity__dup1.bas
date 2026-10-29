#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 81: Field store/load parity for floats

Private Sub Main()
    Dim src As String
    src = _
        "Type T" & Chr(10) & _
        "  f As F64" & Chr(10) & _
        "End Type" & Chr(10) & _
        "Dim r As T" & Chr(10) & _
        "r.f = 3.1415" & Chr(10) & _
        "PRINT r.f"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 81 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 81 exec | "; errText
        End 1
    End If

    Print "DONE_81_AST"
    End 0
End Sub

Main