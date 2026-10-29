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
Dim As String diagCode = "UXB_TEST", diagLayer = "test", diagPhase = "negative"
Dim As String diagMessage = "normal diagnostic", diagSurface = "X", diagHint = ""
UXBDiagnosticPush diags, diagCode, UXB_DIAG_WARNING, diagLayer, diagPhase, diagMessage, testLocation, diagSurface, diagHint
Dim emptyLoc As SourceLocation
emptyLoc = UXBSourceLocationMake("", 0, 0, 0, "")
Dim As String mapSurface = "X", mapSource = "ast", mapTarget = "mir", mapKind = "instruction"
Dim As String mapName = "LOAD", mapId = "mir#1", mapStatus = "MISSING_LOCATION"
UXBSourceMapAdd smap, mapSurface, mapSource, mapTarget, mapKind, mapName, emptyLoc, mapId, mapStatus
Dim gate As UXBAdim16GateResult
UXBAdim16RunDiagnosticsGate diags, smap, gate
If gate.ok <> 0 Then
    Print "FAIL: missing source location accepted"
    End 1
End If
Print "ADIM16_NEGATIVE_MISSING_LOCATION_PASS"
