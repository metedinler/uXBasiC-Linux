#include once "../../src/parser/token_kinds.fbs"
#include once "../../src/parser/lexer.fbs"
#include once "../../src/parser/parser.fbs"

Private Function LoadTextFile(ByRef filePath As String, ByRef textOut As String) As Integer
    Dim f As Integer
    f = FreeFile
    Open filePath For Input As #f
    If Err <> 0 Then Return 0

    textOut = ""
    Do While Not Eof(f)
        Dim lineText As String
        Line Input #f, lineText
        textOut &= lineText & Chr(13) & Chr(10)
    Loop

    Close #f
    Return 1
End Function

Private Sub Main()
    Dim filePath As String
    filePath = Command(1)
    If filePath = "" Then
        Print "USAGE: parse_uxb_file_probe <path>"
        End 2
    End If

    Dim sourceText As String
    If LoadTextFile(filePath, sourceText) = 0 Then
        Print "LOAD_FAIL " & filePath
        End 2
    End If

    Dim st As LexerState
    LexerInit st, sourceText, filePath

    Dim ps As ParseState
    ParserInit ps, st

    If ParseProgram(ps) = 0 Then
        Print "PARSE_FAIL " & ps.lastError
        End 1
    End If

    Print "PARSE_OK nodes=" & Str(ps.ast.count)
    End 0
End Sub

Main
