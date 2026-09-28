[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\float_text")
# S-142b: ondalik sayi metni her motorda ayni kural: tipin izin verdigi hane sayisi (F64 16, F32 7), ilave sifir yok,
# us en az iki haneli ("1e+20"), inf/nan yazimi. AST, canonical-MIR, native x64 (bld), legacy AST-x64 ve JS (node)
# ayni programla, ayni expected/<ad>.txt ile birebir karsilastirilir. expected/<ad>.engines.txt varsa yalniz o motorlar.
$ErrorActionPreference = "Continue"
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n" }
$node = (Get-Command node -ErrorAction SilentlyContinue).Source
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_ft_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$pass = 0; $fail = 0
try {
  foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
    $enginesFile = Join-Path $TestRoot "expected\$($f.BaseName).engines.txt"
    $only = if (Test-Path $enginesFile) { ((Get-Content $enginesFile -Raw).Trim() -split "\s+") } else { @("AST","MIR","x64","AST-x64","JS") }
    $expected = "$(Get-Content (Join-Path $TestRoot "expected\$($f.BaseName).txt") -Raw)".Trim() -replace "`r",""
    $results = [ordered]@{}
    if ($only -contains "AST") { $results["AST"] = Norm ((& $Uxb run $f.FullName 2>&1) -join "`n") }
    if ($only -contains "MIR") { $results["MIR"] = Norm ((& $Uxb run $f.FullName --interpreter-backend MIR 2>&1) -join "`n") }
    foreach ($mode in @(@("x64", @()), @("AST-x64", @("--x64-mode","AST")))) {
      if ($only -notcontains $mode[0]) { continue }
      $od = Join-Path $tmpRoot ($f.BaseName + "_" + $mode[0])
      $o = (& $Uxb bld $f.FullName @($mode[1]) --out-root $od 2>&1) -join "`n"
      $m = [regex]::Match($o, "build tamamlandi: (.+)")
      $results[$mode[0]] = if ($m.Success) { $exe = $m.Groups[1].Value.Trim(); Push-Location (Split-Path $exe); try { Norm ((& $exe 2>&1) -join "`n") } finally { Pop-Location } } else { "BUILDFAIL: " + (Norm $o) }
    }
    if ($only -contains "JS") {
      if (-not $node) { $results["JS"] = "node bulunamadi" }
      else {
        $jd = Join-Path $tmpRoot ($f.BaseName + "_js"); New-Item -ItemType Directory -Force $jd | Out-Null
        $jo = (& $Uxb jsw $f.FullName --js-out "$jd\p.js" 2>&1) -join "`n"
        $results["JS"] = if (Test-Path "$jd\p.js") { Norm ((& $node "$jd\p.js" 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $jo) }
      }
    }
    foreach ($k in $results.Keys) {
      if ($results[$k] -eq $expected) { $pass++; Write-Host "  PASS $k/$($f.BaseName)" -ForegroundColor Green }
      else { $fail++; Write-Host "  FAIL $k/$($f.BaseName)`n    beklenen: $($expected -replace "`n",' | ')`n    gelen   : $($results[$k] -replace "`n",' | ')" -ForegroundColor Red }
    }
  }
} finally { if (Test-Path $tmpRoot) { try { [IO.Directory]::Delete($tmpRoot, $true) } catch {} } }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }