[CmdletBinding()]
param([string]$Uxb='.\bin\uxb.exe', [string]$TestRoot='.\tests\compiler_consolidation')
$ErrorActionPreference='Stop'
$compiler=(Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $text=[IO.File]::ReadAllText($compiler)
    $match=[regex]::Match($text,'(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the real compiler in the model-test wrapper.' }
    $compiler=$match.Groups[1].Value
}
$root=(Get-Location).Path
$reportDir=Join-Path $root ('reports\compiler_consolidation\'+(Get-Date -Format 'yyyyMMdd_HHmmss_ffff'))
New-Item -ItemType Directory -Force $reportDir | Out-Null
$passed=0; $total=0; $failed=0
foreach($part in @(
    @{Script='run_consolidation_tests.py';Name='language'},
    @{Script='run_matrix_export_tests.py';Name='matrices'}
    @{Script='run_diagnostic_contract_tests.py';Name='diagnostics'}
)) {
    $report=Join-Path $reportDir ($part.Name+'.json')
    $arguments=@('--compiler',$compiler,'--report',$report)
    if ($part.Name -eq 'language') { $arguments += '--temp-builds' }
    if ($part.Name -eq 'diagnostics') {
        $runtimeDir = if ($env:UXB_NATIVE_RUNTIME_DIR) { $env:UXB_NATIVE_RUNTIME_DIR } else { Split-Path $compiler -Parent }
        $arguments += @('--runtime',(Join-Path $runtimeDir 'uxb_runtime.dll'),'--with-iff')
    }
    $output=@(& python (Join-Path $TestRoot $part.Script) @arguments 2>&1)
    $rc=$LASTEXITCODE
    $output | Where-Object {$_ -notmatch '^Toplam:'} | ForEach-Object {Write-Host $_}
    $summary=[regex]::Match(($output -join "`n"),'Toplam:\s*(\d+)\s+PASS:\s*(\d+)\s+FAIL:\s*(\d+)')
    if ($summary.Success) {
        $total += [int]$summary.Groups[1].Value
        $passed += [int]$summary.Groups[2].Value
        $failed += [int]$summary.Groups[3].Value
        if ($rc -ne 0 -and [int]$summary.Groups[3].Value -eq 0) {$total++;$failed++}
    } else {$total++;$failed++}
}
"Toplam: $total   PASS: $passed   FAIL: $failed"
"Evidence: $reportDir"
if ($failed -gt 0) {exit 1}
exit 0
