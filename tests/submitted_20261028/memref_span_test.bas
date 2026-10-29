' S-056/S-094 span guard regression, to be run in the uXBasic FreeBASIC toolchain.
' Example from repo root:
'   fbc -i src/common -x memref_span_test test_taslaklari/memref_span_test.bas
' It tests a private internal helper directly; it does NOT run the six uXBasic engines.
#include once "memory_ref.fbs"

Private Sub ExpectCheck(ByVal addr As ULongInt, ByVal n As ULongInt, ByVal expected As Integer, ByRef labelText As String)
    Dim result As Integer
    result = UXBMemRefCheck(addr, n)
    If result <> expected Then
        Print "FAIL "; labelText; " expected="; expected; " actual="; result; " "; UXBMemRefReason()
        End 1
    End If
    Print "PASS "; labelText
End Sub

UXBMemRefReset()
Dim ownerName As String
ownerName = "array a"
If UXBMemRefRegister(UXB_MEMREF_KIND_ARRAY, 1000, 16, ownerName) < 0 Then
    Print "FAIL region registration"
    End 1
End If

ExpectCheck(1000, 4, 1, "first in-bounds DWord")
ExpectCheck(1012, 4, 1, "last in-bounds DWord")
ExpectCheck(1016, 1, 0, "one-past-end")
ExpectCheck(1015, 4, 0, "cross past end")
ExpectCheck(999, 4, 0, "cross from before start")
ExpectCheck(996, 4, 1, "touch without overlap: external")
ExpectCheck(1200, 4, 1, "disjoint external")
ExpectCheck((Not CULngInt(0)) - 1, 4, 0, "U64 access-span overflow")

UXBMemRefRelease(1000)
ExpectCheck(1000, 1, 0, "stale pointer")
ExpectCheck(999, 4, 0, "cross into released region")
Print "TOTAL 10/10 PASS"
