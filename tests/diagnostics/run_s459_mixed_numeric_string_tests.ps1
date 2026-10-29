[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$negativeSources = @(
    's459_mixed_numeric_string_add_left.uxb',
    's459_mixed_numeric_string_add_right.uxb',
    's459_mixed_numeric_string_eq.uxb',
    's459_mixed_numeric_string_lt.uxb'
) | ForEach-Object { Join-Path $root ('tests\diagnostics\' + $_) }
$targets = @(
    @{ Name = 'AST'; Args = @('run') },
    @{ Name = 'MIR'; Args = @('run', '--interpreter-backend', 'MIR') },
    @{ Name = 'MIR-x64'; Args = @('x64') },
    @{ Name = 'AST-x64'; Args = @('x64', '--x64-mode', 'AST') },
    @{ Name = 'JS'; Args = @('jsw') },
    @{ Name = 'WAT'; Args = @('wat') }
)
$total = 0
$passed = 0
$failed = 0

function Norm([string]$text) {
    (($text -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n"
}

foreach ($source in $negativeSources) {
    foreach ($targetSpec in $targets) {
        $target = $targetSpec.Name
        $total++
        $diagPath = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s459_' + [Guid]::NewGuid().ToString('N') + '.json')
        $cli = @($targetSpec.Args) + @($source, '--diag-format=json', '--all-diagnostics-json-out', $diagPath)
        & $compiler @cli *> $null
        $exitCode = $LASTEXITCODE
        $ok = $false
        if ($exitCode -eq 1 -and (Test-Path -LiteralPath $diagPath)) {
            $report = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
            $codes = @($report.diagnostics | ForEach-Object { $_.code })
            $ok = ($codes.Count -eq 1 -and $codes[0] -eq 'UXB_MIXED_STRING_NUMERIC')
        }
        if ($ok) { $passed++ } else {
            $failed++
            Write-Host ('FAIL ' + $target + ' ' + [IO.Path]::GetFileName($source) + ' exit=' + $exitCode)
        }
        if (Test-Path -LiteralPath $diagPath) { Remove-Item -LiteralPath $diagPath -Force }
    }
}

# Explicit conversion remains the portable positive path. WAT is excluded
# because this source intentionally exercises the existing F64 WAT capability
# gate rather than the mixed-type rule.
$positive = Join-Path $root 'tests\diagnostics\s459_explicit_conversion.uxb'
$expected = "2.5a`na2.5`n6"
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s459_positive_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null
try {
    foreach ($backend in @(@('AST', @()), @('MIR', @('--interpreter-backend', 'MIR')))) {
        $total++
        $lines = @(& $compiler run $positive @($backend[1]) 2>&1)
        $actual = Norm ($lines -join "`n")
        if ($LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected) { $passed++ } else {
            $failed++
            Write-Host ('FAIL positive ' + $backend[0] + ' actual=' + $actual)
        }
    }
    foreach ($mode in @(@('MIR-x64', @('--x64-mode', 'MIR')), @('AST-x64', @('--x64-mode', 'AST')))) {
        $total++
        $buildLines = @(& $compiler bld $positive --build-x64 @($mode[1]) --out-root (Join-Path $temp $mode[0]) 2>&1)
        $match = [regex]::Match(($buildLines -join "`n"), 'build tamamlandi: (.+)')
        $ok = $false
        if ($LASTEXITCODE -eq 0 -and $match.Success) {
            $exe = $match.Groups[1].Value.Trim()
            $runLines = @(& $exe 2>&1)
            $actual = Norm ($runLines -join "`n")
            $ok = $LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected
        }
        if ($ok) { $passed++ } else { $failed++; Write-Host ('FAIL positive ' + $mode[0]) }
    }
    $total++
    $js = Join-Path $temp 's459.js'
    $emit = @(& $compiler jsw $positive --js-out $js 2>&1)
    $ok = $false
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $js)) {
        $runLines = @(& node $js 2>&1)
        $actual = Norm ($runLines -join "`n")
        $ok = $LASTEXITCODE -eq 0 -and $actual.Trim() -eq $expected
    }
    if ($ok) { $passed++ } else { $failed++; Write-Host 'FAIL positive JS' }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
