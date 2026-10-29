[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$passed = 0
$failed = 0

function Check([string]$name, [bool]$ok) {
    if ($ok) { $script:passed++; Write-Host ('PASS ' + $name) }
    else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

$runtimeSource = Join-Path $root 'tests\library_type_contract\rational_libtype_missing_provider_runtime.uxb'
$runtimeOut = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s500_runtime_' + [Guid]::NewGuid().ToString('N'))
$runtimeDiag = Join-Path $runtimeOut 'diagnostics.json'
New-Item -ItemType Directory -Force $runtimeOut | Out-Null
try {
    & $compiler run $runtimeSource --interpreter-backend MIR --all-diagnostics-json-out $runtimeDiag --out-root $runtimeOut *> $null
    $runtimeExit = $LASTEXITCODE
    $d = $null
    if (Test-Path -LiteralPath $runtimeDiag) {
        $payload = Get-Content -LiteralPath $runtimeDiag -Raw | ConvertFrom-Json
        $d = @($payload.diagnostics) | Where-Object { $_.code -eq 'UXB_LIBTYPE_PROVIDER_MISSING' } | Select-Object -First 1
    }
    Check 'runtime provider missing normalized' ($runtimeExit -eq 13 -and $null -ne $d -and
        $d.layer -eq 'library_type' -and $d.phase -eq 'provider_call' -and
        $d.message_en -eq 'Library type provider is missing: RATIONAL.ADD via RATIONAL_PROVIDER_NOT_INSTALLED' -and
        $d.message_tr -eq 'Kutuphane tipi saglayicisi eksik: RATIONAL.ADD via RATIONAL_PROVIDER_NOT_INSTALLED' -and
        $d.related_surface -eq 'RATIONAL.ADD via RATIONAL_PROVIDER_NOT_INSTALLED' -and
        $d.hint_en -ne '' -and $d.hint_tr -ne '')
} finally {
    if (Test-Path -LiteralPath $runtimeOut) { Remove-Item -LiteralPath $runtimeOut -Recurse -Force }
}

$targetSource = Join-Path $root 'tests\library_type_contract\rational_mir_ops_value.uxb'
$targetOut = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s500_target_' + [Guid]::NewGuid().ToString('N'))
$targetDiag = Join-Path $targetOut 'diagnostics.json'
New-Item -ItemType Directory -Force $targetOut | Out-Null
try {
    & $compiler run $targetSource --interpreter-backend AST --all-diagnostics-json-out $targetDiag --out-root $targetOut *> $null
    $targetExit = $LASTEXITCODE
    $d = $null
    if (Test-Path -LiteralPath $targetDiag) {
        $payload = Get-Content -LiteralPath $targetDiag -Raw | ConvertFrom-Json
        $d = @($payload.diagnostics) | Where-Object { $_.code -eq 'UXB_LIBTYPE_PROVIDER_UNAVAILABLE' } | Select-Object -First 1
    }
    Check 'target provider unavailable normalized' ($targetExit -eq 1 -and $null -ne $d -and
        $d.layer -eq 'library_type' -and $d.phase -eq 'target_validation' -and
        $d.message_en -eq 'Library type provider is unavailable for the execution target: AST: RATIONAL' -and
        $d.message_tr -eq 'Calistirma hedefi icin kutuphane tipi saglayicisi kullanilamiyor: AST: RATIONAL' -and
        $d.related_surface -eq 'AST: RATIONAL' -and $d.hint_en -ne '' -and $d.hint_tr -ne '')
} finally {
    if (Test-Path -LiteralPath $targetOut) { Remove-Item -LiteralPath $targetOut -Recurse -Force }
}

$operationSource = Join-Path $root 'tests\library_type_contract\rational_libtype_unsupported_operation.uxb'
$operationOut = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s500_operation_' + [Guid]::NewGuid().ToString('N'))
$operationDiag = Join-Path $operationOut 'diagnostics.json'
New-Item -ItemType Directory -Force $operationOut | Out-Null
try {
    & $compiler run $operationSource --interpreter-backend MIR --all-diagnostics-json-out $operationDiag --out-root $operationOut *> $null
    $operationExit = $LASTEXITCODE
    $d = $null
    if (Test-Path -LiteralPath $operationDiag) {
        $payload = Get-Content -LiteralPath $operationDiag -Raw | ConvertFrom-Json
        $d = @($payload.diagnostics) | Where-Object { $_.code -eq 'UXB_LIBTYPE_PROVIDER_OPERATION_UNAVAILABLE' } | Select-Object -First 1
    }
    Check 'runtime provider operation normalized' ($operationExit -eq 13 -and $null -ne $d -and
        $d.layer -eq 'library_type' -and $d.phase -eq 'provider_call' -and
        $d.message_en -eq 'Library type provider does not support this operation: RATIONAL.CMP via RATIONAL_REFERENCE' -and
        $d.message_tr -eq 'Kutuphane tipi saglayicisi bu islemi desteklemiyor: RATIONAL.CMP via RATIONAL_REFERENCE' -and
        $d.related_surface -eq 'RATIONAL.CMP via RATIONAL_REFERENCE' -and $d.hint_en -ne '' -and $d.hint_tr -ne '')
} finally {
    if (Test-Path -LiteralPath $operationOut) { Remove-Item -LiteralPath $operationOut -Recurse -Force }
}

Write-Output ('Toplam: ' + ($passed + $failed) + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
