[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$total = 0
$passed = 0
$failed = 0

function Norm([string]$text) {
    (($text -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

function CheckCompare([string]$name, [string]$source, [int]$expectedExit, [string]$expectedStatus, [string]$expectedAst, [string]$expectedMir) {
    $script:total++
    $outRoot = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s464_' + [Guid]::NewGuid().ToString('N'))
    $comparePath = Join-Path $outRoot 'compare.json'
    New-Item -ItemType Directory -Force $outRoot | Out-Null
    try {
        $lines = @(& $compiler run $source --interpreter-backend BOTH --interpreter-compare-json-out $comparePath --out-root $outRoot 2>&1)
        $exitCode = $LASTEXITCODE
        $ok = $false
        if (Test-Path -LiteralPath $comparePath) {
            $report = Get-Content -LiteralPath $comparePath -Raw | ConvertFrom-Json
            $ok = ($exitCode -eq $expectedExit -and
                $report.status -eq $expectedStatus -and
                $report.ast_status -eq $expectedAst -and
                $report.mir_status -eq $expectedMir)
        }
        if ($ok) { $script:passed++ } else {
            $script:failed++
            Write-Host ('FAIL ' + $name + ' exit=' + $exitCode + "`n" + (Norm ($lines -join "`n")))
        }
    } finally {
        if (Test-Path -LiteralPath $outRoot) { Remove-Item -LiteralPath $outRoot -Recurse -Force }
    }
}

$equalSource = Join-Path $root 'tests\diagnostics\s510_mir_f32_rounding.uxb'
CheckCompare 'AST/MIR equal output' $equalSource 0 'PASS' 'PASS' 'PASS'

$runtimeFailureSource = Join-Path $root 'tests\diagnostics\s444_uncaught_assert.uxb'
CheckCompare 'AST/MIR prerequisite failure' $runtimeFailureSource 25 'FAIL' 'FAIL' 'FAIL'

# The historical S-464 reproducer is now rejected earlier by S-459/S-460.
# Keep this check so the BOTH surface cannot silently accept that old program.
$mixedSource = Join-Path $root 'tests\diagnostics\s459_mixed_numeric_string_add_left.uxb'
$total++
$diagPath = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s464_diag_' + [Guid]::NewGuid().ToString('N') + '.json')
try {
    & $compiler run $mixedSource --interpreter-backend BOTH --all-diagnostics-json-out $diagPath *> $null
    $exitCode = $LASTEXITCODE
    $ok = $false
    if (Test-Path -LiteralPath $diagPath) {
        $report = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
        $codes = @($report.diagnostics | ForEach-Object { $_.code })
        $ok = ($exitCode -eq 1 -and $codes.Count -eq 1 -and $codes[0] -eq 'UXB_MIXED_STRING_NUMERIC')
    }
    if ($ok) { $passed++ } else { $failed++; Write-Host ('FAIL historical mixed-type guard exit=' + $exitCode) }
} finally {
    if (Test-Path -LiteralPath $diagPath) { Remove-Item -LiteralPath $diagPath -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
