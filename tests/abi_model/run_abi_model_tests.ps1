[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\abi_model")
# S-079 tur ABI (SIZEOF, F80 yuk 10 / adim 16): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te
# calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.
$ErrorActionPreference = "Continue"
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^\s*$' }) -join "`n" }
$pass = 0; $fail = 0
foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
  $enginesFile = Join-Path $TestRoot "expected\$($f.BaseName).engines.txt"
  $only = if (Test-Path $enginesFile) { ((Get-Content $enginesFile -Raw).Trim() -split "\s+") } else { @("AST","MIR","x64","AST-x64") }
  $expected = (Get-Content (Join-Path $TestRoot "expected\$($f.BaseName).txt") -Raw).Trim() -replace "`r",""
  $results = [ordered]@{}
  if ($only -contains "AST") { $results["AST"] = Norm ((& $Uxb run $f.FullName 2>&1) -join "`n") }
  if ($only -contains "MIR") { $results["MIR"] = Norm ((& $Uxb run $f.FullName --interpreter-backend MIR 2>&1) -join "`n") }
  foreach ($mode in @(@("x64", @()), @("AST-x64", @("--x64-mode","AST")))) {
    if ($only -notcontains $mode[0]) { continue }
    $o = (& $Uxb bld $f.FullName @($mode[1]) -o "out\abi_$($mode[0]).exe" 2>&1) -join "`n"
    $m = [regex]::Match($o, "build tamamlandi: (.+)")
    $results[$mode[0]] = if ($m.Success) { Norm ((& $m.Groups[1].Value.Trim() 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $o) }
  }
  foreach ($k in $results.Keys) {
    if ($results[$k] -eq $expected) { $pass++; Write-Host "  PASS $k/$($f.BaseName)" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $k/$($f.BaseName)`n    beklenen: $($expected -replace "`n",' | ')`n    gelen   : $($results[$k] -replace "`n",' | ')" -ForegroundColor Red }
  }
}
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }



