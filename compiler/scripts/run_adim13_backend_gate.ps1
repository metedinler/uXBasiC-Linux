param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location $Root

$current = "reports/control/current"
$historyRoot = "reports/control/history"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$historyTarget = Join-Path $historyRoot "13_adim8_backend_x64_x86_$stamp"
New-Item -ItemType Directory -Force $historyRoot | Out-Null
if (Test-Path $current) {
    if (Get-ChildItem $current -Force -ErrorAction SilentlyContinue) {
        New-Item -ItemType Directory -Force $historyTarget | Out-Null
        Move-Item "$current\*" $historyTarget -Force
    }
}
New-Item -ItemType Directory -Force $current | Out-Null
Write-Host "CURRENT_ARCHIVED_TO=$historyTarget"

$buildScript = "compiler/scripts/build_uxb_main_64.bat"
if (!(Test-Path $buildScript)) {
    throw "build script bulunamadi: $buildScript"
}

& $buildScript
if ($LASTEXITCODE -ne 0) { throw "FreeBASIC compiler build failed" }

$exeCandidates = @(
    "build/uxb_main_64.exe",
    "bin/uxb.exe"
)
$uxbExe = $exeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $uxbExe) { throw "uxb executable bulunamadi" }

$results = @()

function Run-Test($name, $argv, $expectSuccess) {
    Write-Host "RUN $name $argv"
    & $uxbExe @argv
    $code = $LASTEXITCODE
    $ok = if ($expectSuccess) { $code -eq 0 } else { $code -ne 0 }
    $script:results += [pscustomobject]@{ name=$name; exit_code=$code; expected_success=$expectSuccess; ok=$ok }
    if (-not $ok) { Write-Host "TEST_FAIL $name exit=$code" }
}

Run-Test "x64_i32" @("tests/adim13/positive/adim13_i32_backend.bas", "--emit-x64-nasm", "--codegen-source", "MIR") $true
Run-Test "x64_f64" @("tests/adim13/positive/adim13_f64_backend.bas", "--emit-x64-nasm", "--codegen-source", "MIR") $true
Run-Test "x64_runtime" @("tests/adim13/positive/adim13_call_runtime.bas", "--emit-x64-nasm", "--codegen-source", "MIR") $true

# x86 hedefi emekli (S-666, Asama 3): --emit-x86 her program icin CLI_TARGET_RETIRED ile reddedilir (cikis kodu != 0).
# Ayrintili sinama: tests/x86_emeklilik. Basit I32 de desteklenmeyen opcode da basarisiz olmali.
Run-Test "x86_i32_retired" @("tests/adim13/positive/adim13_i32_backend.bas", "--emit-x86", "--codegen-source", "MIR") $false
Run-Test "x86_unsupported_retired" @("tests/adim13/negative/adim13_x86_unsupported.bas", "--emit-x86", "--codegen-source", "MIR") $false

$results | Export-Csv -NoTypeInformation -Encoding UTF8 "reports/control/current/adim8_positive_negative_tests.csv"

$failCount = ($results | Where-Object { -not $_.ok }).Count
$status = if ($failCount -eq 0) { "PASS" } else { "FAIL" }

$gate = [ordered]@{
    status = $status
    failed_tests = $failCount
    test_count = $results.Count
    note = "Adim13 native backend x64 gate (x86 retired: S-666)"
}
$gate | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "reports/control/current/adim8_gate.json"

@"
# Adim13 Backend Gate

Status: $status
Failed tests: $failCount
Total tests: $($results.Count)
"@ | Set-Content -Encoding UTF8 "reports/control/current/adim8_gate.md"

if ($failCount -ne 0) { exit 1 }
exit 0
