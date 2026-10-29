#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/runtime/memory_vm.fbs"
#include once "../../src/runtime/memory_exec.fbs"
#include once "../helpers/runtime_test_common.fbs"

' Test 80: Operator numeric parity (int, F32, F64)
' Ensures simple arithmetic and mixed-type ops parse/run across backends.

Private Sub Main()
    Dim src As String
    src = _
        "Dim i As Integer" & Chr(10) & _
        "Dim f32v As F32" & Chr(10) & _
        "Dim f64v As F64" & Chr(10) & _
        "i = 3" & Chr(10) & _
        "f32v = 1.5" & Chr(10) & _
        "f64v = 2.25" & Chr(10) & _
        "i = i + 2" & Chr(10) & _
        "f32v = f32v * 2" & Chr(10) & _
        "f64v = f64v + 0.75" & Chr(10) & _
        "PRINT i, f32v, f64v"

    Dim ps As ParseState
    Dim errText As String

    If RTParseProgram(src, ps, errText) = 0 Then
        Print "FAIL 80 parse | "; errText
        End 1
    End If

    If RTExecProgram(ps, errText) = 0 Then
        Print "FAIL 80 exec | "; errText
        End 1
    End If

    Print "DONE_80_AST"
    End 0
End Sub

Main
