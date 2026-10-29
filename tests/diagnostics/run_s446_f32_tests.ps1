[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$source = Join-Path $root 'tests\diagnostics\s446_f32_parity.uxb'
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s446_' + [Guid]::NewGuid().ToString('N'))
$expected = "1.677722e+07`n1`n0.1`n1.25"
$total = 0
$passed = 0
$failed = 0
New-Item -ItemType Directory -Force $temp | Out-Null

function Norm([string]$text) {
    (($text -replace "`r", "") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

function Check([string]$name, [string]$actual, [int]$exitCode) {
    $script:total++
    $normalized = Norm $actual
    if ($exitCode -eq 0 -and $normalized.Trim() -eq $expected) {
        $script:passed++
        Write-Host ('PASS ' + $name)
    } else {
        $script:failed++
        Write-Host ('FAIL ' + $name)
        Write-Host ('  beklenen: ' + ($expected -replace "`n", ' | '))
        Write-Host ('  gelen   : ' + ($normalized -replace "`n", ' | '))
        Write-Host ('  cikis   : ' + $exitCode)
    }
}

try {
    $lines = @(& $compiler run $source 2>&1); Check 'AST' (($lines | Out-String)) $LASTEXITCODE
    $lines = @(& $compiler run $source --interpreter-backend MIR 2>&1); Check 'MIR' (($lines | Out-String)) $LASTEXITCODE

    $x64Root = Join-Path $temp 'x64'
    $lines = @(& $compiler bld $source --build-x64 --out-root $x64Root 2>&1)
    $x64Exit = $LASTEXITCODE
    $match = [regex]::Match(($lines | Out-String), 'build tamamlandi: (.+)')
    if ($match.Success) {
        $exe = $match.Groups[1].Value.Trim()
        $runLines = @(& $exe 2>&1)
        Check 'MIR-x64' (($runLines | Out-String)) $LASTEXITCODE
    } else {
        Check 'MIR-x64' (($lines | Out-String)) $x64Exit
    }

    $jsRoot = Join-Path $temp 'js'
    New-Item -ItemType Directory -Force $jsRoot | Out-Null
    $jsPath = Join-Path $jsRoot 'program.js'
    $lines = @(& $compiler jsw $source --js-out $jsPath 2>&1)
    $jsEmitExit = $LASTEXITCODE
    if ($jsEmitExit -eq 0 -and (Test-Path -LiteralPath $jsPath)) {
        $runLines = @(& node $jsPath 2>&1)
        Check 'JS' (($runLines | Out-String)) $LASTEXITCODE
    } else {
        Check 'JS' (($lines | Out-String)) $jsEmitExit
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
