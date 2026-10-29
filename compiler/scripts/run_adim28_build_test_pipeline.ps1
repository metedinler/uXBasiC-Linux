param([switch]$NoRepair)

$ErrorActionPreference = "Stop"
$repo = Get-Location
while ($repo -and !(Test-Path (Join-Path $repo "uxb/src/main.bas"))) {
  $parent = Split-Path $repo -Parent
  if ($parent -eq $repo) { break }
  $repo = $parent
}
if (!(Test-Path (Join-Path $repo "uxb/src/main.bas"))) {
  Write-Error "Repo root bulunamadi: uxb/src/main.bas yok"
  exit 1
}
Set-Location $repo

$current = "uxb/reports/control/current"
$history = "uxb/reports/control/history"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path $current) {
  $items = Get-ChildItem $current -Force -ErrorAction SilentlyContinue
  if ($items) {
    $dst = Join-Path $history "adim28_build_test_$stamp"
    New-Item -ItemType Directory -Force $dst | Out-Null
    Move-Item "$current/*" $dst -Force
  }
}
New-Item -ItemType Directory -Force $current | Out-Null

$compileLog = Join-Path $current "adim28_compile.log"
$gateJson = Join-Path $current "adim28_build_test_gate.json"

$buildExit = 1
if (Test-Path "build_64.bat") {
  cmd /c "build_64.bat" *> $compileLog
  $buildExit = $LASTEXITCODE
} elseif (Test-Path "uxb/compiler/scripts/build_uxb_main_64.bat") {
  cmd /c "uxb\compiler\scripts\build_uxb_main_64.bat" *> $compileLog
  $buildExit = $LASTEXITCODE
} else {
  "ERROR: build_64.bat veya compiler/scripts/build_uxb_main_64.bat bulunamadi." | Set-Content -Encoding UTF8 $compileLog
  $buildExit = 1
}

$adim25Exit = 999
$adim22Exit = 999

if ($buildExit -eq 0 -and (Test-Path "uxb/compiler/scripts/run_adim25_26_27_close_gates.ps1")) {
  powershell -NoProfile -ExecutionPolicy Bypass -File "uxb/compiler/scripts/run_adim25_26_27_close_gates.ps1" -NoRepair
  $adim25Exit = $LASTEXITCODE
}

if ($buildExit -eq 0 -and (Test-Path "uxb/compiler/scripts/run_adim22_full_layer_expected_suite.ps1")) {
  powershell -NoProfile -ExecutionPolicy Bypass -File "uxb/compiler/scripts/run_adim22_full_layer_expected_suite.ps1" -NoRepair
  $adim22Exit = $LASTEXITCODE
}

$ok = (($buildExit -eq 0) -and (($adim25Exit -eq 0) -or ($adim25Exit -eq 999)) -and (($adim22Exit -eq 0) -or ($adim22Exit -eq 999)))
$json = @"
{
  "step": "ADIM28_BUILD_TEST",
  "ok": $($ok.ToString().ToLower()),
  "build_exit_code": $buildExit,
  "adim25_26_27_exit_code": $adim25Exit,
  "adim22_exit_code": $adim22Exit,
  "compile_log": "uxb/reports/control/current/adim28_compile.log",
  "note": "Bu script tamirat yapmaz; derleme/test durumunu raporlar."
}
"@
$json | Set-Content -Encoding UTF8 $gateJson

if ($ok) { exit 0 } else { exit 1 }
