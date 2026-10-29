[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$Filtre = "")
# Kilavuz V2 kayitlarinin (SORUN_TAKIP S-numaralari) kapanis testleri. Dosya adi onekleri kaydi gosterir (s623_..., s569_...).
# Her program AST, MIR, native x64 (bld), eski AST-x64, JS ve WASM'da kosulur; expected\<ad>.engines.txt motor listesini daraltir.
#   expected\<ad>.txt           : birebir beklenen cikti (INFO/WARN satirlari atilir)
#   expected\<ad>.contains.txt  : "MOTOR=metin" satirlari -> cikti metni icermeli (birebir yerine)
#   expected\<ad>.rc.txt        : "MOTOR=kod" satirlari -> programin cikis kodu (yorumlayicilar: uxb run cikisi; native: exe cikisi)
# Her program kendi gecici calisma dizininde kosar (dosya acan programlar depoyu kirletmez); her yol mutlaktir.
# Native yollar icin yalitilmis calisma ani dizini UXB_NATIVE_RUNTIME_DIR ortam degiskeniyle verilebilir (derleyiciye aktarilir).
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$wat2wasmExe = Join-Path $repo "tools\wabt\bin\wat2wasm.exe"
$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not [IO.Path]::IsPathRooted($Uxb)) { $Uxb = (Resolve-Path $Uxb).Path }
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_kvk_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$sure = 90
$script:sonRc = $null

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
  if (-not $p.WaitForExit($sure * 1000)) { try { $p.Kill() } catch {}; $t = "ZAMAN-ASIMI"; $script:sonRc = -9 } else { $p.WaitForExit(); $script:sonRc = $p.ExitCode }
  $out = ""
  if (Test-Path $so) { $out = (Get-Content $so -Raw) }
  if (Test-Path $se) { $out += (Get-Content $se -Raw) }
  $n = Norm $out $ham
  if ($t) { return $t + "`n" + $n }
  return $n
}
function Motor([string]$m, [string]$prog, [string]$work) {
  $script:sonRc = $null
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
function Harita([string]$yol) {
  $h = @{}
  if (Test-Path $yol) { foreach ($ln in (Get-Content $yol -Encoding utf8)) { if ($ln -match "^\s*([^=]+)=(.*)$") { $h[$Matches[1].Trim()] = $Matches[2] } } }
  return $h
}

$pass = 0; $fail = 0
try {
  foreach ($f in Get-ChildItem $root -Filter *.uxb | Sort-Object Name) {
    if ($Filtre -ne "" -and $f.BaseName -notlike "*$Filtre*") { continue }
    $ef = Join-Path $root "expected\$($f.BaseName).engines.txt"
    $only = if (Test-Path $ef) { ((Get-Content $ef -Raw).Trim() -split "\s+") } else { @("AST", "MIR", "x64", "AST-x64", "JS", "WASM") }
    $contains = Harita (Join-Path $root "expected\$($f.BaseName).contains.txt")
    # "ALL=<metin>": motor anahtari olmayan her motor icin gecerlidir (language_guards / task_model kosucularindaki gibi)
    if ($contains.ContainsKey("ALL")) { foreach ($mAll in $only) { if (-not $contains.ContainsKey($mAll)) { $contains[$mAll] = $contains["ALL"] } } }
    $rcMap = Harita (Join-Path $root "expected\$($f.BaseName).rc.txt")
    $xf = Join-Path $root "expected\$($f.BaseName).txt"
    $expected = if (Test-Path $xf) { "$(Get-Content $xf -Raw -Encoding utf8)".Trim() -replace "`r", "" } else { "" }
    foreach ($m in $only) {
      $work = Join-Path $tmpRoot ($f.BaseName + "_" + $m)
      New-Item -ItemType Directory -Force $work | Out-Null
      $r = Motor $m $f.FullName $work
      $rc = $script:sonRc
      if ($contains.ContainsKey($m)) { $ok = $r.Contains($contains[$m]) } else { $ok = ($r -eq $expected) }
      $rcNot = ""
      if ($ok -and $rcMap.ContainsKey($m)) { if ("$rc" -ne $rcMap[$m].Trim()) { $ok = $false; $rcNot = "cikis kodu beklenen=$($rcMap[$m].Trim()) gelen=$rc" } }
      if ($ok) { $pass++; Write-Host "  PASS $m/$($f.BaseName)" -ForegroundColor Green }
      else {
        $fail++
        $bek = if ($contains.ContainsKey($m)) { "icerir: " + $contains[$m] } else { $expected -replace "`n", ' | ' }
        $gel = ($r -replace "`n", ' | '); if ($gel.Length -gt 400) { $gel = $gel.Substring(0, 400) + " ..." }
        Write-Host "  FAIL $m/$($f.BaseName)`n    beklenen: $bek`n    gelen   : $gel (rc=$rc) $rcNot" -ForegroundColor Red
      }
    }
  }
} finally { if (Test-Path $tmpRoot) { try { [IO.Directory]::Delete($tmpRoot, $true) } catch {} } }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
