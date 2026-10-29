param([string]$Uxb='.\bin\uxb.exe')
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$output = Join-Path (Get-Location) ('test_results\task_loader_contract\' + [guid]::NewGuid().ToString('N'))
$previousWorkers = $env:UXB_TASK_WORKERS
$passed = 0; $total = 0
try {
    $env:UXB_TASK_WORKERS = '2'
    foreach ($suite in @('incdec_sync')) {
        $evidence = Join-Path $output $suite
        $lines = & python (Join-Path $PSScriptRoot '..\turkce_ad\run_tests.py') --uxb $compiler --test-root (Join-Path $PSScriptRoot $suite) --output $evidence --temp-builds --jobs 2 2>&1
        $runExit = $LASTEXITCODE
        # Publish one combined count for INCDEC and native loader acceptance.
        $lines | Where-Object { $_ -notmatch '^Toplam:' } | ForEach-Object { Write-Output $_ }
        $summary = Get-Content (Join-Path $evidence 'summary.json') -Raw | ConvertFrom-Json
        if ($runExit -ne 0 -and $summary.passed -eq $summary.total) { throw 'Runner failed without a recorded failing check.' }
        $total += $summary.total
        $passed += $summary.passed
    }
    $loaderEvidence = Join-Path $output 'native_loader'
    $loaderLines = & python (Join-Path $PSScriptRoot 'run_loader_contract.py') --uxb $compiler --output $loaderEvidence 2>&1
    $loaderExit = $LASTEXITCODE
    $loaderLines | Where-Object { $_ -notmatch '^Total ' } | ForEach-Object { Write-Output $_ }
    New-Item -ItemType Directory -Force $loaderEvidence | Out-Null
    $loaderLines | Set-Content -LiteralPath (Join-Path $loaderEvidence 'runner.log') -Encoding utf8
    if (!(Test-Path -LiteralPath (Join-Path $loaderEvidence 'summary.json'))) {
        throw "Loader runner produced no summary (exit=$loaderExit); raw error: $(Join-Path $loaderEvidence 'runner.log')"
    }
    $loaderSummary = Get-Content (Join-Path $loaderEvidence 'summary.json') -Raw | ConvertFrom-Json
    if ($loaderExit -ne 0 -and $loaderSummary.passed -eq $loaderSummary.total) { throw 'Loader runner failed without a recorded failing check.' }
    $total += $loaderSummary.total
    $passed += $loaderSummary.passed
} finally {
    $env:UXB_TASK_WORKERS = $previousWorkers
}
Write-Output "Toplam: $total   PASS: $passed   FAIL: $($total - $passed)"
exit [int]($passed -ne $total)
