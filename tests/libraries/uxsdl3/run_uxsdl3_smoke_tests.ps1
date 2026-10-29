[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\libraries\uxsdl3", [int]$TimeoutSec = 240, [string[]]$Only = @())
# uxsdl3 (SDL3 sarmalayicisi) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) calistirilir.
# Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. Testler PENCERE/HOPARLOR ACMAZ: SDL'in dummy video/ses suruculeri
# programin icinde ipucu (SDL_VIDEO_DRIVER/SDL_AUDIO_DRIVER) ile secilir. Yazilan gecici dosyalar out\ altindadir ve test sonunda silinir.
# Onkosul: bin\uxsdl3.dll + bin\SDL3.dll (runtime_ext\uxraylib\build_wrappers.bat uretir; native derleme bagimliliklari PE import tablosundan kopyalar).
# Her calistirma zaman asimina bagli: takilan bir motor TIMEOUT olarak raporlanir, koşucuyu kilitlemez.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot '..\..\support\controlled_process.ps1')
$Uxb = (Resolve-Path -LiteralPath $Uxb).Path
$TestRoot = (Resolve-Path -LiteralPath $TestRoot).Path
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n" }
function RunTimed([string]$exe, [string[]]$argList, [int]$sec) {
  $run = Invoke-UxbControlledProcess $exe $argList $tmpRoot $sec
  if ($run.TimedOut) { return "TIMEOUT(${sec}s)`n$($run.Output)" }
  if ($run.ExitCode -ne 0) { return "EXIT($($run.ExitCode))`n$($run.Output)" }
  return $run.Output
}
$pass = 0; $fail = 0
$tmpRoot = Join-Path $env:TEMP ("uxsdl3_runner_" + [guid]::NewGuid().ToString("N"))
[void][System.IO.Directory]::CreateDirectory($tmpRoot)
[void][System.IO.Directory]::CreateDirectory((Join-Path $tmpRoot 'out'))
foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
  if ($Only.Count -gt 0 -and ($Only | Where-Object { $f.BaseName -like "*$_*" }).Count -eq 0) { continue }
  $src = Get-Content $f.FullName -Raw
  $m = [regex]::Match($src, 'PRINT\s+"([A-Z0-9_]+_PASS)"')
  if (-not $m.Success) { continue }
  $expected = $m.Groups[1].Value
  $results = [ordered]@{}
  $results["AST"] = Norm (RunTimed $Uxb @("run", $f.FullName, "--out-root", $tmpRoot) $TimeoutSec)
  $results["MIR"] = Norm (RunTimed $Uxb @("run", $f.FullName, "--interpreter-backend", "MIR", "--out-root", $tmpRoot) $TimeoutSec)
  foreach ($mode in @(@("x64", @()), @("AST-x64", @("--x64-mode","AST")))) {
    $exeOut = Join-Path $tmpRoot ("sdl_" + $f.BaseName + "_" + $mode[0] + ".exe")
    $o = RunTimed $Uxb (@("bld", $f.FullName) + $mode[1] + @("-o", $exeOut, "--out-root", $tmpRoot)) $TimeoutSec
    $bm = [regex]::Match($o, "build tamamlandi: (.+)")
    if ($bm.Success -and $o -notmatch '^EXIT\(|^TIMEOUT\(') { $results[$mode[0]] = Norm (RunTimed ($bm.Groups[1].Value.Trim()) @() $TimeoutSec) }
    else { $results[$mode[0]] = "BUILDFAIL: " + (Norm $o) }
  }
  foreach ($k in $results.Keys) {
    if ($results[$k] -eq $expected) { $pass++; Write-Host "  PASS $k/$($f.BaseName)" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $k/$($f.BaseName)`n    beklenen: $expected`n    gelen   : $(($results[$k] -replace "`n",' | ').Substring(0, [Math]::Min(600, $results[$k].Length)))" -ForegroundColor Red }
  }
}
try { Remove-UxbOwnedTemporaryDirectory $tmpRoot } catch { Write-Warning $_ }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
