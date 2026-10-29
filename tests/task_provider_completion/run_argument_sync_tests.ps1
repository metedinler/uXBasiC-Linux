param([string]$Uxb='.\bin\uxb.exe')
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$output = Join-Path (Get-Location) ('test_results\task_argument_sync\' + [guid]::NewGuid().ToString('N'))
$previousWorkers = $env:UXB_TASK_WORKERS
$passed = 0; $total = 0
try {
    $env:UXB_TASK_WORKERS = '2'
    foreach ($suite in @('argument_sync','string_snapshot','string_storage','lock_lifetime','expression_reads','console_services')) {
        $evidence = Join-Path $output $suite
        $lines = & python (Join-Path $PSScriptRoot '..\turkce_ad\run_tests.py') --uxb $compiler --test-root (Join-Path $PSScriptRoot $suite) --output $evidence --temp-builds --jobs 2 2>&1
        $runExit = $LASTEXITCODE
        $lines | Where-Object { $_ -notmatch '^Toplam:' } | ForEach-Object { Write-Output $_ }
        $summary = Get-Content (Join-Path $evidence 'summary.json') -Raw | ConvertFrom-Json
        if ($runExit -ne 0 -and $summary.passed -eq $summary.total) { throw 'Runner failed without a recorded failing check.' }
        $passed += $summary.passed; $total += $summary.total
    }
} finally { $env:UXB_TASK_WORKERS = $previousWorkers }
Write-Output "Toplam: $total   PASS: $passed   FAIL: $($total - $passed)"
exit [int]($passed -ne $total)
