param([string]$Uxb='.\bin\uxb.exe')
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$output = Join-Path (Get-Location) ('test_results\task_lvalue_sync\' + [guid]::NewGuid().ToString('N'))
$previousWorkers = $env:UXB_TASK_WORKERS
try {
    $env:UXB_TASK_WORKERS = '2'
    & python (Join-Path $PSScriptRoot '..\turkce_ad\run_tests.py') --uxb $compiler --test-root (Join-Path $PSScriptRoot 'lvalue_sync') --output $output --temp-builds --jobs 2
    $code = $LASTEXITCODE
} finally { $env:UXB_TASK_WORKERS = $previousWorkers }
exit $code
