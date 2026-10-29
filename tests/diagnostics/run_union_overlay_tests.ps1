[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\union_overlay.uxb'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s442_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null
$passed = 0
$total = 0
$failed = 0

function Check([string]$name, [bool]$ok) {
    $script:total++
    if ($ok) { $script:passed++ } else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

try {
    $astOut = Join-Path $temp 'ast.out'
    & $compiler run $source '--program-output-out' $astOut *> $null
    Check 'ast-run' ($LASTEXITCODE -eq 0 -and (Test-Path $astOut) -and (Get-Content $astOut -Raw).Trim() -eq '4')

    $mirOut = Join-Path $temp 'mir.out'
    & $compiler run $source '--interpreter-backend' 'MIR' '--program-output-out' $mirOut *> $null
    Check 'mir-run' ($LASTEXITCODE -eq 0 -and (Test-Path $mirOut) -and (Get-Content $mirOut -Raw).Trim() -eq '4')

    $mirJson = Join-Path $temp 'mir.json'
    & $compiler mir $source '--mir-json-out' $mirJson *> $null
    $mirText = if (Test-Path $mirJson) { Get-Content $mirJson -Raw } else { '' }
    Check 'mir-contract' ($LASTEXITCODE -eq 0 -and $mirText.Contains('MIR_UNION_FIELD_LOAD') -and $mirText.Contains('MIR_UNION_FIELD_STORE') -and -not $mirText.Contains('U.B'))

    $nativeExe = Join-Path $temp 'union_overlay.exe'
    & $compiler bld $source '--build-x64' '--build-x64-out' $nativeExe *> $null
    $nativeOk = $false
    if ($LASTEXITCODE -eq 0 -and (Test-Path $nativeExe)) {
        $nativeOut = Join-Path $temp 'native.out'
        & $nativeExe *> $nativeOut
        $nativeOk = ($LASTEXITCODE -eq 0 -and (Get-Content $nativeOut -Raw).Trim() -eq '4')
    }
    Check 'mir-x64-run' $nativeOk

    $jsOut = Join-Path $temp 'union_overlay.js'
    & $compiler jsw $source '--js-out' $jsOut *> $null
    $jsOk = $false
    if ($LASTEXITCODE -eq 0 -and (Test-Path $jsOut)) {
        $jsLog = Join-Path $temp 'js.out'
        node $jsOut *> $jsLog
        $jsText = Get-Content $jsOut -Raw
        $jsOk = ($LASTEXITCODE -eq 0 -and (Get-Content $jsLog -Raw).Trim() -eq '4' -and $jsText.Contains('unionFieldLoad') -and $jsText.Contains('unionFieldStore'))
    }
    Check 'js-run' $jsOk

    $watOut = Join-Path $temp 'union_overlay.wat'
    & $compiler wat $source '--wat-out' $watOut *> $null
    $watOk = $false
    if ($LASTEXITCODE -eq 0 -and (Test-Path $watOut)) {
        $watText = Get-Content $watOut -Raw
        $wasmOut = Join-Path $temp 'union_overlay.wasm'
        $wat2wasm = Join-Path $root 'tools\wabt\bin\wat2wasm.exe'
        if (Test-Path $wat2wasm) { & $wat2wasm $watOut '-o' $wasmOut *> $null; $watOk = ($LASTEXITCODE -eq 0 -and (Test-Path $wasmOut) -and (Get-Item $wasmOut).Length -gt 0) }
        $watOk = $watOk -and $watText.Contains('global $__G_U') -and -not $watText.Contains('$U_B') -and -not $watText.Contains('$U_I')
    }
    Check 'wat-compile' $watOk
} finally {
    if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
