# Model test paketlerini (tests\run_all_model_tests.ps1) koşar; sonucu build\claude_reports\ altina yazar ve
# yalniz ozet + dusen kontrolleri basar.
#   .\tools\claude\uxb_regression.ps1 -Uxb .\bin\uxb_claude1_f2f.exe [-Only task_sync,routine_scope]
# Uzun surer (tam kosu ~1 saat): arka planda baslatilmasi onerilir. Dusen bir testin bu degisiklikten mi yoksa
# onceden mi geldigini ayirmak icin: .\tools\claude\uxb_run3.ps1 -File <test> -Uxb <eski exe> ile karsilastir.
param(
    [string]$Uxb = '.\bin\uxb.exe',
    [string[]]$Only = @()
)
$ErrorActionPreference = 'Continue'
$uxbRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $uxbRoot
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force 'build\claude_reports' | Out-Null
$report = "build\claude_reports\regression_$stamp.md"
$log = "build\claude_reports\regression_$stamp.log"
$args2 = @{ Uxb = $Uxb; ReportPath = $report }
if ($Only.Count -gt 0) { $args2.Only = $Only }
& .\tests\run_all_model_tests.ps1 @args2 *>&1 | Tee-Object -FilePath $log | Out-Null
$code = $LASTEXITCODE
$lines = Get-Content $log
"=== DUSENLER ==="
$lines | Where-Object { $_ -match '^\s*FAIL ' } | ForEach-Object { $_.Trim() } | Select-Object -First 60
"=== OZET ==="
$start = ($lines | Select-String -Pattern 'TUM MODEL PAKETLERI' | Select-Object -Last 1).LineNumber
if ($start) { $lines[($start)..($lines.Count - 1)] | Where-Object { $_ -match '\S' } }
"rapor: $report  gunluk: $log  cikis=$code"
exit $code
