[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\oop_parity")
# S-037 OOP esitligi (sinif/kalitim/sanal dagitim/SUPER/arayuz/erisim): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te
# calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.
$ErrorActionPreference = "Continue"
# 2026-10-16: JS ve WASM de istege bagli motorlardir (varsayilan yine AST, MIR, x64, AST-x64): bir testin
# expected\<ad>.engines.txt dosyasina "JS" / "WASM" yazilirsa o test web hedefinde de koşar ve ayni beklentiyle
# karsilastirilir (JS: uxb jsw -> node; WASM: uxb wat --emit-wasm -> wat2wasm -> node run_wasm.js).
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n" }
$webTemp = Join-Path ([IO.Path]::GetTempPath()) ("uxb_oop_web_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
$wat2wasmExe = (Resolve-Path ".\tools\wabt\bin\wat2wasm.exe" -ErrorAction SilentlyContinue).Path
$pass = 0; $fail = 0
foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
  $enginesFile = Join-Path $TestRoot "expected\$($f.BaseName).engines.txt"
  $only = if (Test-Path $enginesFile) { ((Get-Content $enginesFile -Raw).Trim() -split "\s+") } else { @("AST","MIR","x64","AST-x64") }
  $containsFile = Join-Path $TestRoot "expected\$($f.BaseName).contains.txt"
  $contains = @{}
  if (Test-Path $containsFile) { foreach ($ln in (Get-Content $containsFile)) { if ($ln -match "^\s*([^=]+)=(.*)$") { $contains[$Matches[1].Trim()] = $Matches[2] } } }
  $expected = if (Test-Path (Join-Path $TestRoot "expected\$($f.BaseName).txt")) { "$(Get-Content (Join-Path $TestRoot "expected\$($f.BaseName).txt") -Raw)".Trim() -replace "`r","" } else { "" }
  $results = [ordered]@{}
  if ($only -contains "AST") { $results["AST"] = Norm ((& $Uxb run $f.FullName 2>&1) -join "`n") }
  if ($only -contains "MIR") { $results["MIR"] = Norm ((& $Uxb run $f.FullName --interpreter-backend MIR 2>&1) -join "`n") }
  foreach ($mode in @(@("x64", @()), @("AST-x64", @("--x64-mode","AST")))) {
    if ($only -notcontains $mode[0]) { continue }
    $o = (& $Uxb bld $f.FullName @($mode[1]) -o "out\op_$($mode[0]).exe" 2>&1) -join "`n"
    $m = [regex]::Match($o, "build tamamlandi: (.+)")
    $results[$mode[0]] = if ($m.Success) { Norm ((& $m.Groups[1].Value.Trim() 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $o) }
  }
  if ($only -contains "JS") {
    if (-not $nodeExe) { $results["JS"] = "BUILDFAIL: node bulunamadi" }
    else {
      $jd = Join-Path $webTemp ($f.BaseName + "_js"); New-Item -ItemType Directory -Force $jd | Out-Null
      $jo = (& $Uxb jsw $f.FullName --js-out "$jd\p.js" 2>&1) -join "`n"
      $results["JS"] = if (Test-Path "$jd\p.js") { Norm ((& $nodeExe "$jd\p.js" 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $jo) }
    }
  }
  if ($only -contains "WASM") {
    if (-not $nodeExe -or -not $wat2wasmExe) { $results["WASM"] = "BUILDFAIL: node ya da wat2wasm bulunamadi" }
    else {
      $wd = Join-Path $webTemp ($f.BaseName + "_wasm"); New-Item -ItemType Directory -Force $wd | Out-Null
      $wo = (& $Uxb wat $f.FullName --emit-wasm --wasm-out "$wd\p.wasm" --wat-out "$wd\p.wat" "--wat2wasm=$wat2wasmExe" 2>&1) -join "`n"
      $results["WASM"] = if (Test-Path "$wd\p.wasm") { Norm ((& $nodeExe "$wd\run_wasm.js" 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $wo) }
    }
  }
  foreach ($k in $results.Keys) {
    if ($contains.ContainsKey($k)) { $okCase = $results[$k].Contains($contains[$k]) } else { $okCase = ($results[$k] -eq $expected) }
    if ($okCase) { $pass++; Write-Host "  PASS $k/$($f.BaseName)" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $k/$($f.BaseName)`n    beklenen: $(if ($contains.ContainsKey($k)) { "icerir: " + $contains[$k] } else { $expected -replace "`n",' | ' })`n    gelen   : $($results[$k] -replace "`n",' | ')" -ForegroundColor Red }
  }
}
if (Test-Path $webTemp) { try { [IO.Directory]::Delete($webTemp, $true) } catch {} }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }




