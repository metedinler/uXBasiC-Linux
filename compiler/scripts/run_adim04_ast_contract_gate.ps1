$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..\..").Path

$step = "04_ast_contract_child_model"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$current = "reports/control/current"
$history = "reports/control/history/${step}_$stamp"
New-Item -ItemType Directory -Force "reports/control/history" | Out-Null
if (Test-Path $current) {
    $items = Get-ChildItem $current -Force -ErrorAction SilentlyContinue
    if ($items) {
        New-Item -ItemType Directory -Force $history | Out-Null
        Move-Item "$current\*" $history -Force
    }
}
New-Item -ItemType Directory -Force $current | Out-Null
Write-Host "CURRENT_ARCHIVED_TO=$history"

cmd /c compiler\scripts\run_step2_ast_contract_gate.bat
if ($LASTEXITCODE -ne 0) { throw "Mevcut AST contract gate FAIL" }

cmd /c compiler\scripts\build_uxb_main_64.bat
if ($LASTEXITCODE -ne 0) { throw "FreeBASIC compiler build FAIL" }

$exeCandidates = @("bin\uxb.exe")
$exe = $exeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $exe) { throw "uxb_main_64.exe bulunamadi" }

$positiveTests = @(
    "tests\adim04\positive\adim04_binary_expr.bas",
    "tests\adim04\positive\adim04_if_call.bas",
    "tests\adim04\positive\adim04_class.bas"
)

foreach ($t in $positiveTests) {
    $name = [IO.Path]::GetFileNameWithoutExtension($t)
    & $exe $t --ast-contract-check --ast-contract-json-out "reports/control/current/$name.ast_contract.json"
    if ($LASTEXITCODE -ne 0) { throw "ADIM04 pozitif test FAIL: $t" }
}

$fbc = "tools\FreeBASIC-1.10.1-win64\fbc.exe"
if (!(Test-Path $fbc)) { throw "fbc bulunamadi: $fbc" }
& $fbc "tests\adim04\negative_harness\adim04_ast_contract_negative_harness.bas" -x "reports\control\current\adim04_ast_contract_negative_harness.exe"
if ($LASTEXITCODE -ne 0) { throw "ADIM04 negative harness derleme FAIL" }
& "reports\control\current\adim04_ast_contract_negative_harness.exe"
if ($LASTEXITCODE -ne 0) { throw "ADIM04 negative harness FAIL" }

$required = @(
    "reports/control/current/adim04_gate.json",
    "reports/control/current/adim04_gate.md",
    "reports/control/current/ast_child_model_matrix.csv"
)
foreach ($r in $required) {
    if (!(Test-Path $r)) { throw "Eksik rapor: $r" }
}

Get-ChildItem reports/control/current | Select-Object Name,Length
Write-Host "ADIM04_AST_CONTRACT_CHILD_MODEL_PASS"
