[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$Filtre = "")
# S-624: TIMER = yerel gece yarisindan beri gecen saniye (F64, kesirli), altı yolun hepsinde AYNI tanim.
# Her program AST, MIR, native x64 (bld), eski AST-x64, JS ve WASM'da kosulur (expected\<ad>.engines.txt ile daraltilir);
# cikti expected\<ad>.txt ile birebir karsilastirilir. Programlar deterministiktir: TIMER'in kendisini degil
# aralik/kesir/fark ozelliklerini yazdirir (-1 = dogru).
# Native yollar __uxb_rt_timer_f64 isteyen bir uxb_runtime.dll ister: UXB_NATIVE_RUNTIME_DIR ortam degiskeni
# (yalitilmis calisma ani dizini) oldugu gibi derleyiciye aktarilir.
# Her program kendi gecici calisma dizininde kosar (out\ klasorunu paylasan koşucularla cakismaz); her yol mutlaktir.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$wat2wasmExe = Join-Path $repo "tools\wabt\bin\wat2wasm.exe"
$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not [IO.Path]::IsPathRooted($Uxb)) { $Uxb = (Resolve-Path $Uxb).Path }
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_timer_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$sure = 90

function Norm([string]$s, [bool]$ham = $false) {
  $l = ($s -replace "`r", "") -split "`n"
  if ($ham) { $l = $l | Where-Object { $_ -notmatch '^\s*$' } } else { $l = $l | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' } }
  return ($l -join "`n")
}
function Kos([string]$exe, [string[]]$arglist, [string]$cwd, [bool]$ham = $false) {
  $so = Join-Path $cwd ("o_" + [Guid]::NewGuid().ToString("N").Substring(0, 6) + ".out")
  $se = $so + ".err"
  $p = Start-Process -FilePath $exe -ArgumentList $arglist -WorkingDirectory $cwd -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
  $t = ""
  if (-not $p.WaitForExit($sure * 1000)) { try { $p.Kill() } catch {}; $t = "ZAMAN-ASIMI" }
  $out = ""
  if (Test-Path $so) { $out = (Get-Content $so -Raw) }
  if (Test-Path $se) { $out += (Get-Content $se -Raw) }
  $n = Norm $out $ham
  if ($t) { return $t + "`n" + $n }
  return $n
}
function Motor([string]$m, [string]$prog, [string]$work) {
  switch ($m) {
    "AST" { return Kos $Uxb @("run", "`"$prog`"") $work }
    "MIR" { return Kos $Uxb @("run", "`"$prog`"", "--interpreter-backend", "MIR") $work }
    { $_ -in "x64", "AST-x64" } {
      $extra = @(); if ($m -eq "AST-x64") { $extra = @("--x64-mode", "AST") }
      $o = Kos $Uxb (@("bld", "`"$prog`"") + $extra + @("-o", "out_$m.exe")) $work $true
      $mm = [regex]::Match($o, "build tamamlandi: (\S+)")
      if ($mm.Success) { $exeAbs = $mm.Groups[1].Value.Trim(); if (-not [IO.Path]::IsPathRooted($exeAbs)) { $exeAbs = Join-Path $work $exeAbs }; return Kos $exeAbs @() $work }
      return "BUILDFAIL: " + (Norm $o)
    }
    "JS" {
      if (-not $nodeExe) { return "BUILDFAIL: node bulunamadi" }
      $js = Join-Path $work "p.js"
      $o = Kos $Uxb @("jsw", "`"$prog`"", "--js-out", "`"$js`"") $work
      if (Test-Path $js) { return Kos $nodeExe @("`"$js`"") $work }
      return "BUILDFAIL: " + $o
    }
    "WASM" {
      if (-not $nodeExe -or -not (Test-Path $wat2wasmExe)) { return "BUILDFAIL: node ya da wat2wasm bulunamadi" }
      $wd = Join-Path $work "wasm"; New-Item -ItemType Directory -Force $wd | Out-Null
      $o = Kos $Uxb @("wat", "`"$prog`"", "--emit-wasm", "--wasm-out", "`"$wd\p.wasm`"", "--wat-out", "`"$wd\p.wat`"", "`"--wat2wasm=$wat2wasmExe`"") $work
      if (Test-Path "$wd\p.wasm") { return Kos $nodeExe @("`"$wd\run_wasm.js`"") $work }
      return "BUILDFAIL: " + $o
    }
  }
}

$pass = 0; $fail = 0
try {
  foreach ($f in Get-ChildItem $root -Filter *.uxb | Sort-Object Name) {
    if ($Filtre -ne "" -and $f.BaseName -notlike "*$Filtre*") { continue }
    $ef =Join-Path $root "expected\$($f.BaseName).engines.txt"
    $only = if (Test-Path $ef) { ((Get-Content $ef -Raw).Trim() -split "\s+") } else { @("AST", "MIR", "x64", "AST-x64", "JS", "WASM") }
    $xf = Join-Path $root "expected\$($f.BaseName).txt"
    $expected = if (Test-Path $xf) { "$(Get-Content $xf -Raw)".Trim() -replace "`r", "" } else { "" }
    foreach ($m in $only) {
      $work = Join-Path $tmpRoot ($f.BaseName + "_" + $m)
      New-Item -ItemType Directory -Force $work | Out-Null
      $r = Motor $m $f.FullName $work
      if ($r -eq $expected) { $pass++; Write-Host "  PASS $m/$($f.BaseName)" -ForegroundColor Green }
      else {
        $fail++
        $bek = $expected -replace "`n", ' | '
        $gel = ($r -replace "`n", ' | '); if ($gel.Length -gt 400) { $gel = $gel.Substring(0, 400) + " ..." }
        Write-Host "  FAIL $m/$($f.BaseName)`n    beklenen: $bek`n    gelen   : $gel" -ForegroundColor Red
      }
    }
  }
} finally { if (Test-Path $tmpRoot) { try { [IO.Directory]::Delete($tmpRoot, $true) } catch {} } }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
