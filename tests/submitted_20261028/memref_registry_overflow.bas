#include once "memory_ref.fbs"
UXBMemRefReset()
Dim ownerName As String = "overflow region"
If UXBMemRefRegister(UXB_MEMREF_KIND_ARRAY, (Not CULngInt(0)) - 1, 4, ownerName) >= 0 Then
    Print "FAIL overflow region accepted"
    End 1
End If
If UXBMemRefCheck(1200, 4) <> 0 Then
    Print "FAIL unregistered access after registration failure"
    End 1
End If
Print "TOTAL 2/2 PASS"
