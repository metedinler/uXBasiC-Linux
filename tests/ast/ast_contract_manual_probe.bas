' Manual probe for Stage 2 AST contract layer.
' Run from uxb root after copying patch files:
'
'   fbc tests\ast\ast_contract_manual_probe.bas -x build\ast_contract_manual_probe.exe
'   build\ast_contract_manual_probe.exe
'
#include once "../../src/parser/ast.fbs"
#include once "../../src/parser/ast_contract.fbs"

Dim p As ASTPool
ASTPoolInit p

Dim rootIdx As Integer
Dim lhsIdx As Integer
Dim rhsIdx As Integer
Dim binIdx As Integer

rootIdx = ASTNewNode(p, "PROGRAM", "", "", 1, 1)
lhsIdx = ASTNewNode(p, "NUMBER", "1", "", 1, 1)
rhsIdx = ASTNewNode(p, "NUMBER", "2", "", 1, 5)
binIdx = ASTMakeBinary(p, "+", lhsIdx, rhsIdx, 1, 3)
ASTAddRoleChild p, rootIdx, binIdx, "BODY"

Dim errText As String
If UXBAstValidateContract(p, rootIdx, errText) = 0 Then
    Print "AST contract FAIL: "; errText
    End 1
End If

Shell "cmd /c if not exist dist mkdir dist"
Dim writeErr As String
If UXBAstWriteContractReportJson(p, rootIdx, "dist\ast_contract_manual_probe.json", writeErr) = 0 Then
    Print "AST contract JSON write FAIL: "; writeErr
    End 2
End If

UXBAstPrintContractSummary p, rootIdx
Print "AST contract manual probe PASS"
Print "Report: dist\ast_contract_manual_probe.json"
End 0
