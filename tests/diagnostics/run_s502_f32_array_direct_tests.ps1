[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s502_f32_array_direct.uxb'
$expected = "2.5`n2.5`n2.5`n1.25"
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s502_' + [Guid]::NewGuid().ToString('N'))
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

    foreach ($mode in @(@('MIR-x64', @('--x64-mode', 'MIR')), @('AST-x64', @('--x64-mode', 'AST')))) {
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

    $js = Join-Path $temp 's502.js'
    $emitLines = @(& $compiler jsw $source --js-out $js 2>&1)
    $emitExit = $LASTEXITCODE
    if ($emitExit -eq 0 -and (Test-Path -LiteralPath $js)) {
        $runLines = @(& node $js 2>&1)
        $actual = Norm ($runLines -join "`n")
        Check 'JS' ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")
    } else {
        Check 'JS' $false ("emit=$emitExit $($emitLines -join ' ')")
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
