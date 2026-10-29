#include once "../../../src/common/source_location.fbs"
#include once "../../../src/common/source_location_adim16_ext.fbs"
#include once "../../../src/common/json_builder.fbs"
#include once "../../../src/common/report_writer.fbs"
#include once "../../../src/common/diagnostic.fbs"
#include once "../../../src/common/source_mapping.fbs"
#include once "../../../src/common/diagnostic_schema_writer.fbs"
#include once "../../../src/common/adim16_diagnostics_gate.fbs"

Dim diags As UXBDiagnosticList
UXBDiagnosticListInit diags

Dim smap As UXBSourceMapList
UXBSourceMapInit smap

Dim testLocation As SourceLocation
testLocation = UXBSourceLocationMake("tests/adim16/harness/adim16_common_harness.bas", 10, 5, 3, "PRINT")

Dim As String diagCode = "UXB_TEST_WARN", diagLayer = "test", diagPhase = "harness"
Dim As String diagMessage = "JSON kacis testi: a" & Chr(34) & "b", diagSurface = "PRINT", diagHint = "ok"
UXBDiagnosticPush diags, diagCode, UXB_DIAG_WARNING, diagLayer, diagPhase, diagMessage, testLocation, diagSurface, diagHint

Dim As String mapSurface = "PRINT", mapSourceStage = "token", mapTargetStage = "ast"
Dim As String mapEntityKind = "stmt", mapEntityName = "PRINT_STMT", mapTargetId = "ast#1", mapStatus = "OK"
UXBSourceMapAdd smap, mapSurface, mapSourceStage, mapTargetStage, mapEntityKind, mapEntityName, testLocation, mapTargetId, mapStatus

Dim gate As UXBAdim16GateResult
UXBAdim16RunDiagnosticsGate diags, smap, gate
If gate.ok = 0 Then
    Print "FAIL: "; gate.errorsText
    End 1
End If

Dim errText As String
UXBWriteDiagnosticSchemaJson "reports/control/current/adim11_diagnostic_schema.json", errText
UXBSourceMapWriteCsv smap, "reports/control/current/adim11_source_mapping_report.csv", errText
UXBWriteJsonSchemaReportCsv "reports/control/current/adim11_json_schema_report.csv", errText
UXBAdim16WriteGateReports gate, "reports/control/current/adim11_gate.json", "reports/control/current/adim11_gate.md", errText
UXBDiagnosticWriteJson diags, "reports/control/current/adim11_positive_diag.json", errText

Print "ADIM16_COMMON_HARNESS_PASS"
