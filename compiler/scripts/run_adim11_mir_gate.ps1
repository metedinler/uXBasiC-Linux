param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if ($RepoRoot -eq "") {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
Set-Location $RepoRoot

$current = "reports/control/current"
$historyRoot = "reports/control/history"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$historyTarget = Join-Path $historyRoot "adim11_mir_$stamp"
New-Item -ItemType Directory -Force $historyRoot | Out-Null
if (Test-Path $current) {
    $files = Get-ChildItem $current -Force -ErrorAction SilentlyContinue
    if ($files) {
        New-Item -ItemType Directory -Force $historyTarget | Out-Null
        Move-Item "$current\*" $historyTarget -Force
    }
}
New-Item -ItemType Directory -Force $current | Out-Null

$exe = "build\uxb_main_64.exe"
if (!(Test-Path $exe)) {
    $exe = "bin\uxb.exe"
}
if (!(Test-Path $exe)) {
    Write-Error "uXBasic executable bulunamadi. Once compiler\scripts\build_uxb_main_64.bat calistir."
    exit 1
}

$positive = @(
    "tests\adim11\positive\adim11_i32_arithmetic.bas",
    "tests\adim11\positive\adim11_f64_arithmetic.bas",
    "tests\adim11\positive\adim11_if_branch.bas"
)
$negative = @(
    "tests\adim11\negative\adim11_type_mismatch.bas",
    "tests\adim11\negative\adim11_unknown_label.bas"
)

$posRows = @()
$negRows = @()
$allOk = $true

foreach ($t in $positive) {
    $name = [IO.Path]::GetFileNameWithoutExtension($t)
    $mir = "reports\control\current\$name.mir.json"
    $ver = "reports\control\current\$name.verify.json"
    & $exe $t --codegen-source MIR --mir-json-out $mir --mir-verify-json-out $ver
    $code = $LASTEXITCODE
    $status = if ($code -eq 0 -and (Test-Path $mir) -and (Test-Path $ver)) { "PASS" } else { "FAIL" }
    if ($status -ne "PASS") { $allOk = $false }
    $posRows += [pscustomobject]@{ test=$t; exit_code=$code; mir=$mir; verify=$ver; status=$status }
}

foreach ($t in $negative) {
    $name = [IO.Path]::GetFileNameWithoutExtension($t)
    $mir = "reports\control\current\$name.mir.json"
    $ver = "reports\control\current\$name.verify.json"
    & $exe $t --codegen-source MIR --mir-json-out $mir --mir-verify-json-out $ver
    $code = $LASTEXITCODE
    $status = if ($code -ne 0) { "PASS_EXPECTED_FAIL" } else { "FAIL_UNEXPECTED_PASS" }
    if ($status -ne "PASS_EXPECTED_FAIL") { $allOk = $false }
    $negRows += [pscustomobject]@{ test=$t; exit_code=$code; mir=$mir; verify=$ver; status=$status }
}

$posRows | Export-Csv "reports/control/current/adim6_positive_tests.csv" -NoTypeInformation -Encoding UTF8
$negRows | Export-Csv "reports/control/current/adim6_negative_tests.csv" -NoTypeInformation -Encoding UTF8

$gate = [ordered]@{
    step = "ADIM11_ADIM6_MIR_LOWER_VERIFY_OPT"
    status = if ($allOk) { "PASS" } else { "FAIL" }
    positive_count = $positive.Count
    negative_count = $negative.Count
    history = $historyTarget
}
$gate | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 "reports/control/current/adim6_gate.json"

$md = @()
$md += "# Adim 11 / Adim 6 MIR Gate"
$md += ""
$md += "Status: **$($gate.status)**"
$md += ""
$md += "History: `$historyTarget`"
$md += ""
$md += "## Positive"
$md += ($posRows | Format-Table -AutoSize | Out-String)
$md += "## Negative"
$md += ($negRows | Format-Table -AutoSize | Out-String)
$md -join "`n" | Set-Content -Encoding UTF8 "reports/control/current/adim6_gate.md"

if (-not $allOk) { exit 1 }
exit 0
