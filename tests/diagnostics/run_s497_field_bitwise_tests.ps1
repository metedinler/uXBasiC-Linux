[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s497_field_bitwise_assignment.uxb'
$expected = "4`n12`n8`n-1"
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s497_' + [Guid]::NewGuid().ToString('N'))
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
    $lines = @(& $compiler run $source 2>&1)
    $actual = Norm ($lines -join "`n")
    Check 'AST' ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")

    $lines = @(& $compiler run $source --interpreter-backend MIR 2>&1)
    $actual = Norm ($lines -join "`n")
    Check 'MIR' ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")

    foreach ($mode in @(@('MIR-x64', @()), @('AST-x64', @('--x64-mode', 'AST')))) {
        $buildLines = @(& $compiler bld $source @($mode[1]) 2>&1)
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

    $js = Join-Path $temp 's497.js'
    $emitLines = @(& $compiler jsw $source --js-out $js 2>&1)
    $emitExit = $LASTEXITCODE
    if ($emitExit -eq 0 -and (Test-Path -LiteralPath $js)) {
        $runLines = @(& node $js 2>&1)
        $actual = Norm ($runLines -join "`n")
        Check 'JS' ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) ("beklenen=$expected gelen=$actual")
    } else {
        Check 'JS' $false ("emit=$emitExit $($emitLines -join ' ')")
    }

    $wat = Join-Path $temp 's497.wat'
    $watLines = @(& $compiler wat $source --wat-out $wat 2>&1)
    $watExit = $LASTEXITCODE
    $watOk = $watExit -eq 0 -and (Test-Path -LiteralPath $wat) -and (Get-Item -LiteralPath $wat).Length -gt 0
    if ($watOk) {
        $wat2wasm = Join-Path $root 'tools\wabt\bin\wat2wasm.exe'
        if (Test-Path -LiteralPath $wat2wasm) {
            $wasm = Join-Path $temp 's497.wasm'
            & $wat2wasm $wat -o $wasm *> $null
            $watOk = $LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $wasm) -and (Get-Item -LiteralPath $wasm).Length -gt 0
        }
    }
    Check 'WAT/WASM artifact' $watOk ("exit=$watExit $($watLines -join ' ')")
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
