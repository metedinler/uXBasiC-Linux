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
testLocation = UXBSourceLocationMake("negative.bas", 1, 1, 1, "X")
Dim As String diagCode = "", diagLayer = "test", diagPhase = "negative"
Dim As String diagMessage = "bos diagnostic code yakalanmali", diagSurface = "X", diagHint = ""
UXBDiagnosticPush diags, diagCode, UXB_DIAG_ERROR, diagLayer, diagPhase, diagMessage, testLocation, diagSurface, diagHint
Dim As String mapSurface = "X", mapSource = "token", mapTarget = "ast", mapKind = "expr"
Dim As String mapName = "IDENT", mapId = "ast#1", mapStatus = "OK"
UXBSourceMapAdd smap, mapSurface, mapSource, mapTarget, mapKind, mapName, testLocation, mapId, mapStatus
Dim gate As UXBAdim16GateResult
UXBAdim16RunDiagnosticsGate diags, smap, gate
If gate.ok <> 0 Then
    Print "FAIL: empty code accepted"
    End 1
End If
Print "ADIM16_NEGATIVE_EMPTY_CODE_PASS"
