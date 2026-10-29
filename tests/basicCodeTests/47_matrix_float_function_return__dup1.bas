#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"
#include once "../../src/codegen/x64/code_generator.fbs"

Private Function ParseText(ByRef src As String, ByRef ps As ParseState, ByRef errText As String) As Integer
    Dim st As LexerState
    LexerInit st, src

    ParserInit ps, st
    If ParseProgram(ps) = 0 Then
        errText = ps.lastError
        Return 0
    End If

    Return 1
End Function

Private Function AssertTrue(ByVal condValue As Integer, ByRef msg As String) As Integer
    If condValue = 0 Then
        Print "FAIL 47 | "; msg
        Return 0
    End If
    Return 1
End Function

Private Function HasToken(ByRef textIn As String, ByRef tokenText As String) As Integer
    Return InStr(1, textIn, tokenText) > 0
End Function

Private Sub Main()
    Dim src As String
    src = _
        "FUNCTION F1() AS F32" & Chr(10) & _
        "    RETURN 3.25" & Chr(10) & _
        "END FUNCTION" & Chr(10) & _
        "FUNCTION F2() AS F64" & Chr(10) & _
        "    RETURN F1() + 1.0" & Chr(10) & _
        "END FUNCTION" & Chr(10) & _
        "SUB Probe()" & Chr(10) & _
        "    DIM x AS F32" & Chr(10) & _
        "    DIM y AS F64" & Chr(10) & _
        "    x = F1()" & Chr(10) & _
        "    y = F2()" & Chr(10) & _
        "    PRINT x" & Chr(10) & _
        "    PRINT y" & Chr(10) & _
        "END SUB" & Chr(10) & _
        "CALL Probe()"

    Dim ps As ParseState
    Dim errText As String
    Dim asmText As String
    Dim ok As Integer
    ok = 1

    ok And= AssertTrue(ParseText(src, ps, errText), "parse source: " & errText)
    ok And= AssertTrue(X64CodegenEmitNasm(ps, asmText, errText), "x64 codegen emit: " & errText)

    ok And= AssertTrue(HasToken(asmText, "call f1"), "F1 call must be emitted")
    ok And= AssertTrue(HasToken(asmText, "call f2"), "F2 call must be emitted")
    ok And= AssertTrue(HasToken(asmText, "cvtss2sd xmm0, xmm0"), "F32 call result must be widenable to F64")
    ok And= AssertTrue(HasToken(asmText, "movss [rbp -"), "F32 variable store should use movss")
    ok And= AssertTrue(HasToken(asmText, "movsd [rbp -"), "F64 variable store should use movsd")

    If ok = 0 Then End 1

    Print "PASS 47 matrix float function return"
    End 0
End Sub

Main
