#include once "../../src/common/error_system_adim45.fbs"

UXBErrorSystemConfigure45 "", "en", "", 0

Dim unavailableJson As String
unavailableJson = UXBErrorLegacyJson45("error", "UXB_LIBTYPE_PROVIDER_UNAVAILABLE: library type lifecycle provider unavailable for JS: TEXT_REF")
If InStr(unavailableJson, "UXB_LIBTYPE_PROVIDER_UNAVAILABLE") = 0 Then
    Print "FAIL library_type_error_catalog unavailable"
    End 1
End If

Dim missingJson As String
missingJson = UXBErrorLegacyJson45("error", "UXB_LIBTYPE_PROVIDER_MISSING: library type provider missing: RATIONAL.ADD via RATIONAL_PROVIDER_NOT_INSTALLED")
If InStr(missingJson, "UXB_LIBTYPE_PROVIDER_MISSING") = 0 Then
    Print "FAIL library_type_error_catalog missing"
    End 1
End If

Dim mismatchJson As String
mismatchJson = UXBErrorLegacyJson45("error", "UXB_LIBTYPE_PROVIDER_TYPE_MISMATCH: library type provider type mismatch: RATIONAL via TEST_PROVIDER")
If InStr(mismatchJson, "UXB_LIBTYPE_PROVIDER_TYPE_MISMATCH") = 0 Then
    Print "FAIL library_type_error_catalog mismatch"
    End 1
End If

Dim operationJson As String
operationJson = UXBErrorLegacyJson45("error", "UXB_LIBTYPE_PROVIDER_OPERATION_UNAVAILABLE: library type provider operation unavailable: RATIONAL.CMP via RATIONAL_REFERENCE")
If InStr(operationJson, "UXB_LIBTYPE_PROVIDER_OPERATION_UNAVAILABLE") = 0 Then
    Print "FAIL library_type_error_catalog operation"
    End 1
End If

Print "PASS test_library_type_error_catalog"
