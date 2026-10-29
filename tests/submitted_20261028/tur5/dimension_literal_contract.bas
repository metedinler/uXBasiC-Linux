#include once "../../../src/common/number_literal.fbs"
Declare Sub ContractExit CDecl Alias "exit" (ByVal exitCode As Long)
Dim Shared caseCount As Integer, passedCount As Integer
Sub Check(ByVal sourceText As String, ByVal expected As Integer)
    Dim actual As Integer = -1
    Dim accepted As Integer = UXBArrayDimensionLiteral(sourceText, actual)
    caseCount += 1
    If (expected > 0 And accepted <> 0 And actual = expected) Or (expected = 0 And accepted = 0 And actual = 0) Then
        passedCount += 1
    Else
        Print "FAIL "; sourceText; " accepted="; accepted; " value="; actual; " expected="; expected
    End If
End Sub
Check "1", 1
Check "2", 2
Check "2147483647", 2147483647
Check "&H1", 1
Check "&H7FFFFFFF", 2147483647
Check "&O17", 15
Check "&B1010", 10
Check "0xFE", 254
Check "0o17", 15
Check "0b10", 2
Check "%B11", 3
Check "1_000", 1000
Check " 2 ", 2
Check "", 0
Check "0", 0
Check "-1", 0
Check "+1", 0
Check "1.5", 0
Check "1e0", 0
Check "2147483648", 0
Check "999999999999999999999999", 0
Check "&H80000000", 0
Check "&H", 0
Check "&HFG", 0
Check "&B2", 0
Check "&O8", 0
Check "0b2", 0
Check "_", 0
Check "1x", 0
Check "-&H1", 0
Check "&H0", 0
Print "PASS "; LTrim(Str(passedCount)); "/"; LTrim(Str(caseCount))
ContractExit IIf(passedCount = caseCount, 0, 1)
