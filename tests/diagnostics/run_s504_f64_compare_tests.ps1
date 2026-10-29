[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s504_f64_compare.uxb'
$expected = "-1`n-1`n-1"
$total = 0
$passed = 0
$failed = 0

function Norm([string]$text) {
    (($text -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

function Check([string]$name, [string]$actual, [int]$exitCode) {
    $script:total++
    $ok = $exitCode -eq 0 -and (Norm $actual).Trim() -eq $expected
    if ($ok) {
        $script:passed++
        Write-Host ('PASS ' + $name)
    } else {
        $script:failed++
        Write-Host ('FAIL ' + $name)
        Write-Host ('  beklenen: ' + ($expected -replace "`n", ' | '))
        Write-Host ('  gelen   : ' + ((Norm $actual) -replace "`n", ' | '))
        Write-Host ('  cikis   : ' + $exitCode)
    }
}

$lines = @(& $compiler run $source 2>&1)
Check 'AST' ($lines -join "`n") $LASTEXITCODE
$lines = @(& $compiler run $source --interpreter-backend MIR 2>&1)
Check 'MIR' ($lines -join "`n") $LASTEXITCODE

$lines = @(& $compiler jsw $source --js-out (Join-Path $env:TEMP 'uxb_s504_compare.js') 2>&1)
$emitExit = $LASTEXITCODE
$jsPath = Join-Path $env:TEMP 'uxb_s504_compare.js'
if ($emitExit -eq 0 -and (Test-Path -LiteralPath $jsPath)) {
    $runLines = @(& node $jsPath 2>&1)
    Check 'JS' ($runLines -join "`n") $LASTEXITCODE
} else {
    Check 'JS' ($lines -join "`n") $emitExit
}

$lines = @(& $compiler bld $source 2>&1)
$buildExit = $LASTEXITCODE
$match = [regex]::Match(($lines -join "`n"), 'build tamamlandi: (.+)')
if ($buildExit -eq 0 -and $match.Success) {
    $exe = $match.Groups[1].Value.Trim()
    $runLines = @(& $exe 2>&1)
    Check 'MIR-x64' ($runLines -join "`n") $LASTEXITCODE
} else {
    Check 'MIR-x64' ($lines -join "`n") $buildExit
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
