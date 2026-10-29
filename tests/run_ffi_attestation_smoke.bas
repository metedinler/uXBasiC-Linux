#include once "../src/runtime/ffi_signer.fbs"

Dim dllPath As String
Dim dllHash As String
Dim dllSigner As String

Print "SYSTEMROOT=" & Environ("SystemRoot")
Print "WINDIR=" & Environ("WINDIR")
Print "SYSTEMDRIVE=" & Environ("SystemDrive")

If FfiResolveDllPath("kernel32.dll", dllPath) = 0 Then
    Print "FAIL resolve kernel32.dll"
    End 1
End If
Print "DLL_PATH=" & dllPath

Dim captureText As String
If FfiRunPowerShellCapture("Write-Output UXB_CAPTURE_OK", captureText) = 0 Then
    Print "FAIL powershell capture"
    End 2
End If
Print "CAPTURE=" & captureText

If FfiExtractHashFromDllPath(dllPath, dllHash) = 0 Then
    Print "FAIL hash kernel32.dll"
    End 4
End If
Print "HASH_ONLY=" & dllHash

If FfiExtractSignerFromDllPath(dllPath, dllSigner) = 0 Then
    Print "FAIL signer kernel32.dll"
    End 4
End If
Print "SIGNER_ONLY=" & dllSigner

If FfiBuildTrustedWindowsDllAttestation("kernel32.dll", dllHash, dllSigner) = 0 Then
    Print "FAIL attest kernel32.dll"
    End 5
End If

Print "DLL_HASH=" & dllHash
Print "DLL_SIGNER=" & dllSigner
Print "UXB_FFI_ATTESTATION_SMOKE_PASS"
