[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe")
# S-548 / S-549: FREEFILE ve FILE_HANDLE. Her program AST, MIR, native x64 (bld), eski AST-x64 ve istege bagli JS / WASM'da kosulur
# (expected\<ad>.engines.txt); cikti expected\<ad>.txt ile birebir ya da expected\<ad>.contains.txt (motor=metin) ile karsilastirilir.
# Dosya yazan programlar icin HER program kendi gecici calisma dizininde kosar (olusan dosyalar depoyu ve diger kosulari kirletmez,
# out\ klasorunu paylasan koşucularla da cakismaz); bu yuzden her yol mutlaktir.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$wat2wasmExe = Join-Path $repo "tools\wabt\bin\wat2wasm.exe"
$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not [IO.Path]::IsPathRooted($Uxb)) { $Uxb = (Resolve-Path $Uxb).Path }
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_dosya_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$sure = 60

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
    $ef = Join-Path $root "expected\$($f.BaseName).engines.txt"
    $only = if (Test-Path $ef) { ((Get-Content $ef -Raw).Trim() -split "\s+") } else { @("AST", "MIR", "x64", "AST-x64") }
    $cf = Join-Path $root "expected\$($f.BaseName).contains.txt"
    $contains = @{}
    if (Test-Path $cf) { foreach ($ln in (Get-Content $cf)) { if ($ln -match "^\s*([^=]+)=(.*)$") { $contains[$Matches[1].Trim()] = $Matches[2] } } }
    $xf = Join-Path $root "expected\$($f.BaseName).txt"
    $expected = if (Test-Path $xf) { "$(Get-Content $xf -Raw)".Trim() -replace "`r", "" } else { "" }
    foreach ($m in $only) {
      $work = Join-Path $tmpRoot ($f.BaseName + "_" + $m)
      New-Item -ItemType Directory -Force $work | Out-Null
      $r = Motor $m $f.FullName $work
      if ($contains.ContainsKey($m)) { $ok = $r.Contains($contains[$m]) } else { $ok = ($r -eq $expected) }
      if ($ok) { $pass++; Write-Host "  PASS $m/$($f.BaseName)" -ForegroundColor Green }
      else {
        $fail++
        $bek = if ($contains.ContainsKey($m)) { "icerir: " + $contains[$m] } else { $expected -replace "`n", ' | ' }
        $gel = ($r -replace "`n", ' | '); if ($gel.Length -gt 400) { $gel = $gel.Substring(0, 400) + " ..." }
        Write-Host "  FAIL $m/$($f.BaseName)`n    beklenen: $bek`n    gelen   : $gel" -ForegroundColor Red
      }
    }
  }
} finally { if (Test-Path $tmpRoot) { try { [IO.Directory]::Delete($tmpRoot, $true) } catch {} } }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
