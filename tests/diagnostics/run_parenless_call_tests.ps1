[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$targets = @('par', 'ast', 'mir', 'x64', 'jsw', 'wat', 'run')
$negativeSources = @(
    (Join-Path $root 'tests\diagnostics\parenless_call_with_argument.uxb'),
    (Join-Path $root 'tests\diagnostics\parenless_call_bare_name.uxb')
)
$passed = 0
$total = 0
$failed = 0

foreach ($source in $negativeSources) {
    foreach ($target in $targets) {
        $total++
        $diagPath = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s440_' + [Guid]::NewGuid().ToString('N') + '.json')
        $cliArgs = @($target, $source, '--diag-format=json', '--all-diagnostics-json-out', $diagPath)
        & $compiler @cliArgs *> $null
        $exitCode = $LASTEXITCODE
        $ok = $false
        if ($exitCode -eq 1 -and (Test-Path -LiteralPath $diagPath)) {
            $report = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
            $codes = @($report.diagnostics | ForEach-Object { $_.code })
            $ok = ($codes.Count -eq 1 -and $codes[0] -eq 'UXB_CALL_PAREN_REQUIRED')
        }
        if ($ok) {
            $passed++
        } else {
            $failed++
            Write-Host ('FAIL ' + $target + ' ' + [IO.Path]::GetFileName($source) + ' exit=' + $exitCode)
        }
    }
}

$total++
$positiveDiag = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s440_positive_' + [Guid]::NewGuid().ToString('N') + '.json')
& $compiler @('run', (Join-Path $root 'tests\diagnostics\explicit_call.uxb'), '--diag-format=json', '--all-diagnostics-json-out', $positiveDiag) *> $null
$positiveExit = $LASTEXITCODE
$positiveOk = $false
if ($positiveExit -eq 0 -and (Test-Path -LiteralPath $positiveDiag)) {
    $positiveReport = Get-Content -LiteralPath $positiveDiag -Raw | ConvertFrom-Json
    $positiveOk = ($positiveReport.count -eq 0)
}
if ($positiveOk) {
    $passed++
} else {
    $failed++
    Write-Host ('FAIL explicit call exit=' + $positiveExit)
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
