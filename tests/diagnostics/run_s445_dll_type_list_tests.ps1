[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s445_dll_unknown_type.uxb'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s445_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null
$passed = 0
$total = 0
$failed = 0

function Check([string]$name, [bool]$ok) {
    $script:total++
    if ($ok) { $script:passed++ } else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

function RunReject([string]$name, [string[]]$arguments) {
    $lines = @(& $compiler @arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($lines | Out-String)
    Check $name ($exitCode -ne 0 -and $text.Contains('UXB_FFI_ARGUMENT_TYPE_LIST') -and $text.Contains('BILINMEZ'))
}

try {
    RunReject 'AST' @('run', $source)
    RunReject 'MIR' @('run', $source, '--interpreter-backend', 'MIR')
    RunReject 'MIR-x64' @('bld', $source, '--build-x64', '--build-x64-out', (Join-Path $temp 's445.exe'))
    RunReject 'JS' @('jsw', $source, '--js-out', (Join-Path $temp 's445.js'))
    RunReject 'WAT' @('wat', $source, '--wat-out', (Join-Path $temp 's445.wat'))
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
