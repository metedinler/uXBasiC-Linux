#include once "../../../src/common/number_literal.fbs"
Declare Sub ExitProcess Lib "kernel32" Alias "ExitProcess" (ByVal exitCode As UInteger)

Dim Shared checks As Integer
Sub CheckValue(ByVal textValue As String, ByVal expectedOk As Integer, ByVal expectedValue As LongInt = 0)
    Dim actual As Integer
    Dim ok As Integer = UXBDecimalI32Literal(textValue, actual)
    If ok <> expectedOk OrElse (ok <> 0 AndAlso actual <> expectedValue) Then
        Print "FAIL: "; textValue
        ExitProcess(1)
    End If
    checks += 1
End Sub

CheckValue("0", 1, 0)
CheckValue("+0", 1, 0)
CheckValue("-0", 1, 0)
CheckValue("0000000001", 1, 1)
CheckValue("2147483647", 1, 2147483647LL)
CheckValue("+2147483647", 1, 2147483647LL)
CheckValue("-2147483648", 1, -2147483648LL)
CheckValue("-0002147483648", 1, -2147483648LL)
CheckValue("2147483648", 0)
CheckValue("4294967296", 0)
CheckValue("-2147483649", 0)
CheckValue("-4294967296", 0)
CheckValue("99999999999999999999999999999999999999999", 0)
CheckValue("+", 0)
CheckValue("-", 0)
CheckValue("", 0)
CheckValue("1.0", 0)
CheckValue("1e0", 0)
CheckValue("&h1", 0)
CheckValue("1 0", 0)
CheckValue("  -1  ", 1, -1)
CheckValue(String(1000, "0") + "2147483647", 1, 2147483647LL)
Print "PASS "; checks; "/"; checks
ExitProcess(0)
