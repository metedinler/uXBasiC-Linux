#include once "../../src/common/diagnostic.fbs"
#include once "../../src/common/diagnostic_schema_writer.fbs"

Dim langText As String = Command(1)
Dim logPath As String = Command(2)
Dim editorPath As String = Command(3)
UXBErrorSystemConfigure45 logPath, langText, "", 0, 1
Dim list As UXBDiagnosticList
UXBDiagnosticListInit list
If Command(4) <> "" Then list.errorLimit = ValInt(Command(4))
Dim sourceLoc As SourceLocation = UXBSourceLocationMake("included_source.uxb", 10, 3, 6)
Dim codeText As String = "UXB_PROBE_TYPE_MISMATCH"
Dim layerText As String = "semantic", phaseText As String = "type_check"
Dim msgEn As String = "Expected an integer", msgTr As String = "Tamsayi bekleniyor"
UXBDiagnosticPushBilingual list, codeText, UXB_DIAG_ERROR, layerText, phaseText, msgEn, msgTr, sourceLoc
UXBDiagnosticPushBilingual list, codeText, UXB_DIAG_ERROR, layerText, phaseText, msgEn, msgTr, sourceLoc
sourceLoc.lineNo = 21
UXBDiagnosticPushBilingual list, codeText, UXB_DIAG_ERROR, layerText, phaseText, msgEn, msgTr, sourceLoc
msgEn = "Expected a string": msgTr = "Metin bekleniyor"
UXBDiagnosticPushBilingual list, codeText, UXB_DIAG_ERROR, layerText, phaseText, msgEn, msgTr, sourceLoc
Dim jsonText As String, errText As String
If Command(5) <> "" Then
    Dim schemaPath As String = Command(5)
    If UXBWriteDiagnosticSchemaJson(schemaPath, errText) = 0 Then Print errText: End 1
End If
UXBDiagnosticListToVSCodeJson list, jsonText
If UXBReportWriteText(editorPath, jsonText, errText) = 0 Then Print errText: End 1
UXBDiagnosticListToJson list, jsonText
Print jsonText
End 0
