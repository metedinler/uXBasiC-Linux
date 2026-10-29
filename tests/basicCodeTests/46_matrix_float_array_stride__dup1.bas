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
        Print "FAIL 46 | "; msg
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
        "SUB Probe()" & Chr(10) & _
        "    DIM a(0 TO 3) AS F32" & Chr(10) & _
        "    DIM b(0 TO 3) AS F64" & Chr(10) & _
        "    DIM i AS I32" & Chr(10) & _
        "    i = 1" & Chr(10) & _
        "    a(i) = 1.5" & Chr(10) & _
        "    b(i) = 2.5" & Chr(10) & _
        "    PRINT a(i)" & Chr(10) & _
        "    PRINT b(i)" & Chr(10) & _
        "END SUB" & Chr(10) & _
        "CALL Probe()"

    Dim ps As ParseState
    Dim errText As String
    Dim asmText As String
    Dim ok As Integer
    ok = 1

    ok And= AssertTrue(ParseText(src, ps, errText), "parse source: " & errText)
    ok And= AssertTrue(X64CodegenEmitNasm(ps, asmText, errText), "x64 codegen emit: " & errText)

    ok And= AssertTrue(HasToken(asmText, "imul rbx, 4"), "F32 indexed stride must be 4")
    ok And= AssertTrue(HasToken(asmText, "movss [rcx], xmm0"), "F32 indexed store must use movss")

    ok And= AssertTrue(HasToken(asmText, "imul rbx, 8"), "F64 indexed stride must be 8")
    ok And= AssertTrue(HasToken(asmText, "movsd [rcx], xmm0"), "F64 indexed store must use movsd")

    If ok = 0 Then End 1

    Print "PASS 46 matrix float array stride"
    End 0
End Sub

Main
