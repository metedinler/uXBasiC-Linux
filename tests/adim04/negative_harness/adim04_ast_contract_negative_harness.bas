#include once "../../../src/parser/ast.fbs"
#include once "../../../src/parser/ast_contract.fbs"

Private Function ExpectFail(ByRef p As ASTPool, ByVal rootIdx As Integer, ByRef labelText As String) As Integer
    Dim errText As String
    If UXBAstAdim04ValidateTree(p, rootIdx, errText) = 0 Then
        Print "PASS expected fail: "; labelText; " => "; errText
        Return 1
    End If
    Print "FAIL expected contract failure but got PASS: "; labelText
    Return 0
End Function

Dim passCount As Integer
passCount = 0

' Negative 1: BINARY without right operand.
Dim p1 As ASTPool
ASTPoolInit p1
Dim root1 As Integer
root1 = ASTNewNode(p1, ASTK_PROGRAM, "", "", 1, 1)
Dim b1 As Integer
b1 = ASTNewNode(p1, ASTK_BINARY, "", "+", 1, 3)
Dim n1 As Integer
n1 = ASTNewNode(p1, ASTK_IDENTIFIER, "A", "", 1, 1)
ASTSetLeft p1, b1, n1
ASTAddChild p1, root1, b1
If ExpectFail(p1, root1, "binary missing right") <> 0 Then passCount += 1

' Negative 2: BLOCK using left/right.
Dim p2 As ASTPool
ASTPoolInit p2
Dim root2 As Integer
root2 = ASTNewNode(p2, ASTK_PROGRAM, "", "", 1, 1)
Dim block2 As Integer
block2 = ASTNewNode(p2, ASTK_BLOCK, "", "", 1, 1)
Dim n2 As Integer
n2 = ASTNewNode(p2, ASTK_IDENTIFIER, "X", "", 1, 1)
ASTSetLeft p2, block2, n2
ASTAddChild p2, root2, block2
If ExpectFail(p2, root2, "block with left") <> 0 Then passCount += 1

' Negative 3: UNARY using right operand.
Dim p3 As ASTPool
ASTPoolInit p3
Dim root3 As Integer
root3 = ASTNewNode(p3, ASTK_PROGRAM, "", "", 1, 1)
Dim u3 As Integer
u3 = ASTNewNode(p3, ASTK_UNARY, "", "-", 1, 1)
Dim l3 As Integer
l3 = ASTNewNode(p3, ASTK_IDENTIFIER, "A", "", 1, 2)
Dim r3 As Integer
r3 = ASTNewNode(p3, ASTK_IDENTIFIER, "B", "", 1, 3)
ASTSetLeft p3, u3, l3
ASTSetRight p3, u3, r3
ASTAddChild p3, root3, u3
If ExpectFail(p3, root3, "unary with right") <> 0 Then passCount += 1

Dim gateJsonErr As String
UXBAstAdim04WriteGateJson p3, "reports/control/current/adim04_gate.json", gateJsonErr
UXBAstAdim04WriteGateMd p3, "reports/control/current/adim04_gate.md", gateJsonErr
UXBAstAdim04WriteChildModelMatrixCsv p3, "reports/control/current/ast_child_model_matrix.csv", gateJsonErr

If passCount = 3 Then
    Print "ADIM04_NEGATIVE_HARNESS_PASS"
    End 0
End If

Print "ADIM04_NEGATIVE_HARNESS_FAIL passCount="; passCount
End 1
