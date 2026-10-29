[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s505_unary_comparison.uxb'
$expected = "1`n1`n1`n1"
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s505_' + [Guid]::NewGuid().ToString('N'))
$total = 0
$passed = 0
$failed = 0
New-Item -ItemType Directory -Force $temp | Out-Null

function Norm([string]$text) {
    (($text -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

function Check([string]$name, [bool]$ok, [string]$detail = '') {
    $script:total++
    if ($ok) {
        $script:passed++
        Write-Host ('PASS ' + $name)
    } else {
        $script:failed++
        Write-Host ('FAIL ' + $name)
        if ($detail) { Write-Host ('  ' + $detail) }
    }
}

try {
    foreach ($backend in @(@('AST', @()), @('MIR', @('--interpreter-backend', 'MIR')))) {
        $lines = @(& $compiler run $source @($backend[1]) 2>&1)
        $actual = Norm ($lines -join "`n")
        Check $backend[0] ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")
    }

    foreach ($mode in @(@('MIR-x64', @()), @('AST-x64', @('--x64-mode', 'AST')))) {
        $buildLines = @(& $compiler bld $source --build-x64 @($mode[1]) --out-root (Join-Path $temp $mode[0]) 2>&1)
        $buildExit = $LASTEXITCODE
        $buildText = $buildLines -join "`n"
        $match = [regex]::Match($buildText, 'build tamamlandi: (.+)')
        if ($buildExit -eq 0 -and $match.Success) {
            $exe = $match.Groups[1].Value.Trim()
            $runLines = @(& $exe 2>&1)
            $actual = Norm ($runLines -join "`n")
            Check $mode[0] ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")
        } else {
            Check $mode[0] $false ("build=$buildExit $buildText")
        }
    }

    $js = Join-Path $temp 's505.js'
    $emitLines = @(& $compiler jsw $source --js-out $js 2>&1)
    $emitExit = $LASTEXITCODE
    if ($emitExit -eq 0 -and (Test-Path -LiteralPath $js)) {
        $runLines = @(& node $js 2>&1)
        $actual = Norm ($runLines -join "`n")
        Check 'JS' ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")
    } else {
        Check 'JS' $false ("emit=$emitExit $($emitLines -join ' ')")
    }

    $wat = Join-Path $temp 's505.wat'
    $wasmFloat = Join-Path $temp 's505.wasm'
    $wat2wasm = Join-Path $root 'tools\wabt\bin\wat2wasm.exe'
    $watLines = @(& $compiler wat $source --emit-wasm --wat-out $wat --wasm-out $wasmFloat "--wat2wasm=$wat2wasm" 2>&1)
    $watExit = $LASTEXITCODE
    $watFloatOk = $false
    $watText = $watLines -join ' '
    if ($watExit -eq 0 -and (Test-Path -LiteralPath $wasmFloat)) {
        $floatLines = @(& node (Join-Path $temp 'run_wasm.js') 2>&1)
        $floatActual = Norm ($floatLines -join "`n")
        $watFloatOk = $LASTEXITCODE -eq 0 -and $floatActual.Trim() -eq $expected
        $watText = $floatActual
    }
    Check 'WAT/WASM F64 execution' $watFloatOk ("exit=$watExit $watText")

    $watIntegerSource = Join-Path $root 'tests\diagnostics\s505_unary_comparison_i32.uxb'
    $watInteger = Join-Path $temp 's505_i32.wat'
    $watIntegerLines = @(& $compiler wat $watIntegerSource --wat-out $watInteger 2>&1)
    $watIntegerExit = $LASTEXITCODE
    $watIntegerOk = $watIntegerExit -eq 0 -and (Test-Path -LiteralPath $watInteger) -and (Get-Item -LiteralPath $watInteger).Length -gt 0
    if ($watIntegerOk) {
        $wat2wasm = Join-Path $root 'tools\wabt\bin\wat2wasm.exe'
        if (Test-Path -LiteralPath $wat2wasm) {
            $wasm = Join-Path $temp 's505_i32.wasm'
            & $wat2wasm $watInteger -o $wasm *> $null
            $watIntegerOk = $LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $wasm) -and (Get-Item -LiteralPath $wasm).Length -gt 0
        }
    }
    Check 'WAT/WASM integer artifact' $watIntegerOk ("exit=$watIntegerExit $($watIntegerLines -join ' ')")
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
