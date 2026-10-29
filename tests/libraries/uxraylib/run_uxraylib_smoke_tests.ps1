[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\libraries\uxraylib", [int]$TimeoutSec = 1200, [string[]]$Only = @())
# uxraylib (raylib/raygui koprusu, CPU-tarafi Image API'si) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64)
# calistirilir. Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. CODEPTR kullanan (geri cagirma) testlerde
# yorumlayicilar (AST/MIR) gercek kod adresi veremez -> NET "requires native x64" hatasi beklenir (S-076); native ve legacy PASS verir.
# Onkosul: bin\uxraylib.dll (+ libraylib.dll, glfw3.dll); runtime_ext\uxraylib\build_wrappers.bat uretir; derleme bagimliliklari PE import tablosundan bulup cikti klasorune kopyalar. Testler PENCERE ACMAZ.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot '..\..\support\controlled_process.ps1')
$Uxb = (Resolve-Path -LiteralPath $Uxb).Path
$TestRoot = (Resolve-Path -LiteralPath $TestRoot).Path
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n" }
function RunTimed([string]$exe, [string[]]$argList) {
  $run = Invoke-UxbControlledProcess $exe $argList $tmpRoot $TimeoutSec
  if ($run.TimedOut) { return "TIMEOUT(${TimeoutSec}s)`n$($run.Output)" }
  if ($run.ExitCode -ne 0) { return "EXIT($($run.ExitCode))`n$($run.Output)" }
  return $run.Output
}
$pass = 0; $fail = 0
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('uxraylib_runner_' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Join-Path $tmpRoot 'out'))
foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
  if ($Only.Count -gt 0 -and ($Only | Where-Object { $f.BaseName -like "*$_*" }).Count -eq 0) { continue }
  $src = Get-Content $f.FullName -Raw
  $m = [regex]::Match($src, 'PRINT\s+"([A-Z0-9_]+_PASS)"')
  if (-not $m.Success) { continue }
  $expected = $m.Groups[1].Value
  $needsNative = $src -match 'CODEPTR'
  $results = [ordered]@{}
  $results["AST"] = Norm (RunTimed $Uxb @('run', $f.FullName, '--out-root', $tmpRoot))
  $results["MIR"] = Norm (RunTimed $Uxb @('run', $f.FullName, '--interpreter-backend', 'MIR', '--out-root', $tmpRoot))
  foreach ($mode in @(@("x64", @()), @("AST-x64", @("--x64-mode","AST")))) {
    $exeOut = Join-Path $tmpRoot ("ray_" + $f.BaseName + '_' + $mode[0] + '.exe')
    $o = RunTimed $Uxb (@('bld', $f.FullName) + $mode[1] + @('-o', $exeOut, '--out-root', $tmpRoot))
    $bm = [regex]::Match($o, "build tamamlandi: (.+)")
    $results[$mode[0]] = if ($bm.Success -and $o -notmatch '^EXIT\(|^TIMEOUT\(') { Norm (RunTimed ($bm.Groups[1].Value.Trim()) @()) } else { "BUILDFAIL: " + (Norm $o) }
  }
  foreach ($k in $results.Keys) {
    $interp = ($k -eq "AST" -or $k -eq "MIR")
    if ($needsNative -and $interp) { $ok = $results[$k].StartsWith('EXIT(1)') -and $results[$k].Contains("requires native x64"); $want = "cikis 1, icerir: requires native x64" }
    else { $ok = ($results[$k] -eq $expected); $want = $expected }
    if ($ok) { $pass++; Write-Host "  PASS $k/$($f.BaseName)" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $k/$($f.BaseName)`n    beklenen: $want`n    gelen   : $($results[$k] -replace "`n",' | ')" -ForegroundColor Red }
  }
}
try { Remove-UxbOwnedTemporaryDirectory $tmpRoot } catch { Write-Warning $_ }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
