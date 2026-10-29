#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 85: Builtin float-returning functions (SQR,SIN,COS,EXP,LOG)

Private Sub Main()
    Dim src As String
    src = _
        "Dim a As F64" & Chr(10) & _
        "a = SQR(9)" & Chr(10) & _
        "PRINT a" & Chr(10) & _
        "a = SIN(0)" & Chr(10) & _
        "PRINT a" & Chr(10) & _
        "a = EXP(1)" & Chr(10) & _
        "PRINT a"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 85 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 85 exec | "; errText
        End 1
    End If

    Print "DONE_85_AST"
    End 0
End Sub

Main
