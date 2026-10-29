[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$targets = @('par', 'ast', 'mir', 'x64', 'jsw', 'wat', 'run')
$negativeSources = @(
    (Join-Path $root 'tests\diagnostics\const_write_direct.uxb'),
    (Join-Path $root 'tests\diagnostics\const_write_compound.uxb'),
    (Join-Path $root 'tests\diagnostics\const_write_routine.uxb'),
    (Join-Path $root 'tests\diagnostics\const_write_byref.uxb')
)
$passed = 0
$total = 0
$failed = 0

foreach ($source in $negativeSources) {
    foreach ($target in $targets) {
        $total++
        $diagPath = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s441_' + [Guid]::NewGuid().ToString('N') + '.json')
        & $compiler @($target, $source, '--diag-format=json', '--all-diagnostics-json-out', $diagPath) *> $null
        $exitCode = $LASTEXITCODE
        $ok = $false
        if ($exitCode -eq 1 -and (Test-Path -LiteralPath $diagPath)) {
            $report = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
            $codes = @($report.diagnostics | ForEach-Object { $_.code })
            $ok = ($codes.Count -eq 1 -and $codes[0] -eq 'UXB_CONST_ASSIGNMENT')
        }
        if ($ok) { $passed++ }
        else {
            $failed++
            Write-Host ('FAIL ' + $target + ' ' + [IO.Path]::GetFileName($source) + ' exit=' + $exitCode)
        }
    }
}

foreach ($target in $targets) {
    $total++
    $source = Join-Path $root 'tests\diagnostics\const_write_shadow_allowed.uxb'
    $diagPath = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s441_shadow_' + [Guid]::NewGuid().ToString('N') + '.json')
    & $compiler @($target, $source, '--diag-format=json', '--all-diagnostics-json-out', $diagPath) *> $null
    $exitCode = $LASTEXITCODE
    $ok = $false
    if ($exitCode -eq 0 -and (Test-Path -LiteralPath $diagPath)) {
        $report = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
        $ok = (@($report.diagnostics).Count -eq 0)
    }
    if ($ok) { $passed++ }
    else {
        $failed++
        Write-Host ('FAIL shadow ' + $target + ' exit=' + $exitCode)
    }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
