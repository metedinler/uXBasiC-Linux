[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s480_' + [Guid]::NewGuid().ToString('N'))
$cases = @(
    @{ Name = 'multidim'; Source = (Join-Path $root 'tests\diagnostics\s480_multidim_ast.uxb'); Expected = '42' },
    @{ Name = 'i32_cast'; Source = (Join-Path $root 'tests\diagnostics\s480_i32_cast_truncation.uxb'); Expected = "-3`n3" }
)
$total = 0
$passed = 0
$failed = 0
New-Item -ItemType Directory -Force $temp | Out-Null

function Norm([string]$text) {
    (($text -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

function Check([string]$name, [string]$actual, [int]$exitCode, [string]$expected) {
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
    foreach ($case in $cases) {
        $lines = @(& $compiler run $case.Source 2>&1)
        Check ($case.Name + '/AST') (($lines | Out-String)) $LASTEXITCODE $case.Expected

        $lines = @(& $compiler run $case.Source --interpreter-backend MIR 2>&1)
        Check ($case.Name + '/MIR') (($lines | Out-String)) $LASTEXITCODE $case.Expected

        $x64Root = Join-Path $temp ($case.Name + '_x64')
        $lines = @(& $compiler bld $case.Source --build-x64 --out-root $x64Root 2>&1)
        $x64Exit = $LASTEXITCODE
        $match = [regex]::Match(($lines | Out-String), 'build tamamlandi: (.+)')
        if ($match.Success) {
            $runLines = @(& $match.Groups[1].Value.Trim() 2>&1)
            Check ($case.Name + '/MIR-x64') (($runLines | Out-String)) $LASTEXITCODE $case.Expected
        } else {
            Check ($case.Name + '/MIR-x64') (($lines | Out-String)) $x64Exit $case.Expected
        }

        $jsPath = Join-Path (Join-Path $temp ($case.Name + '_js')) 'program.js'
        New-Item -ItemType Directory -Force (Split-Path -Parent $jsPath) | Out-Null
        $lines = @(& $compiler jsw $case.Source --js-out $jsPath 2>&1)
        $jsExit = $LASTEXITCODE
        if ($jsExit -eq 0 -and (Test-Path -LiteralPath $jsPath)) {
            $runLines = @(& node $jsPath 2>&1)
            Check ($case.Name + '/JS') (($runLines | Out-String)) $LASTEXITCODE $case.Expected
        } else {
            Check ($case.Name + '/JS') (($lines | Out-String)) $jsExit $case.Expected
        }
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
