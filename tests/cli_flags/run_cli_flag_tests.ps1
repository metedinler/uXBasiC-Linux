[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\cli_flags")
# CLI bayrak/fiil testleri (Mete'nin CLI denetim programinin ilk parcasi): her durum uxb'yi verilen argumanlarla
# calistirir; cikis kodu ve (birlesik stdout+stderr icinde) beklenen metin denetlenir. Sonsuz donguler zaman asimiyla kesilir.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path $TestRoot).Path
$exe = (Resolve-Path $Uxb).Path
# Kendi build klasorlerini gecici bir --out-root'a yonlendir (sarmalayici .cmd zaten yapiyorsa ekleme)
$scratch = $null
if ($exe -notmatch '\.cmd$') { $scratch = Join-Path ([IO.Path]::GetTempPath()) ("uxb_cli_runs_" + [Guid]::NewGuid().ToString("N").Substring(0, 8)); New-Item -ItemType Directory -Force $scratch | Out-Null }
function Invoke-Uxb([string[]]$ArgList, [int]$TimeoutSec = 90) {
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
  if ($scratch) { [void]$psi.ArgumentList.Add("--out-root"); [void]$psi.ArgumentList.Add($scratch) }
  $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.UseShellExecute = $false
  $p = [Diagnostics.Process]::Start($psi)
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  if (-not $p.WaitForExit($TimeoutSec * 1000)) { try { $p.Kill($true) } catch {}; return [pscustomobject]@{ Exit = -999; Text = "TIMEOUT" } }
  [pscustomobject]@{ Exit = $p.ExitCode; Text = ((($so.Result + "`n" + $se.Result) -replace "`r", "")) }
}
$loop = Join-Path $root "loop_40000.uxb"
$inf = Join-Path $root "infinite_do_loop.uxb"
# Ad, argumanlar, beklenen cikis kodu (-1 = onemsiz), beklenen metin, zaman asimi (sn)
$cases = @(
  @("help (fiil)",             @("help"),          0, "uXBasic CLI Compiler Infrastructure", 60),
  @("yardim (fiil)",           @("yardim"),        0, "uXBasic CLI Compiler Infrastructure", 60),
  @("? (fiil)",                @("?"),             0, "uXBasic CLI Compiler Infrastructure", 60),
  @("hlp (fiil)",              @("hlp"),           0, "uXBasic CLI Compiler Infrastructure", 60),
  @("--help",                  @("--help"),        0, "uXBasic CLI Compiler Infrastructure", 60),
  @("help --max-steps satiri", @("--help"),        0, "--max-steps", 60),
  @("version (fiil)",          @("version"),       0, "uXBasic CLI", 60),
  @("surum (fiil)",            @("surum"),         0, "uXBasic CLI", 60),
  @("ver (fiil)",              @("ver"),           0, "uXBasic CLI", 60),
  @("--version",               @("--version"),     0, "uXBasic CLI", 60),
  @("AST 40000 tur, sinir yok",     @("run", $loop),                                        0, "800020000", 120),
  @("MIR 40000 tur, sinir yok",     @("run", $loop, "--interpreter-backend", "MIR"),        0, "800020000", 120),
  @("MIR --max-steps 0 = sinirsiz", @("run", $loop, "--interpreter-backend", "MIR", "--max-steps", "0"), 0, "800020000", 120),
  @("AST --max-steps 100",          @("run", $loop, "--max-steps", "100"),                  5, "step limit exceeded (--max-steps 100)", 60),
  @("MIR --max-steps 100",          @("run", $loop, "--interpreter-backend", "MIR", "--max-steps", "100"), 13, "step limit exceeded (--max-steps 100)", 60),
  @("AST sonsuz dongu --max-steps", @("run", $inf, "--max-steps", "5000"),                  5, "step limit exceeded (--max-steps 5000)", 60),
  @("MIR sonsuz dongu --max-steps", @("run", $inf, "--interpreter-backend", "MIR", "--max-steps", "5000"), 13, "step limit exceeded (--max-steps 5000)", 60),
  @("--max-steps gecersiz metin",   @("run", $loop, "--max-steps", "abc"),                  2, "--max-steps sifir veya pozitif", 60),
  @("--max-steps negatif",          @("run", $loop, "--max-steps", "-5"),                   2, "--max-steps sifir veya pozitif", 60),
  @("help --task-workers satiri",   @("--help"),                                            0, "--task-workers", 60),
  @("--task-workers 0",             @("run", $loop, "--task-workers", "0"),                 2, "--task-workers 1 ile 1024", 60),
  @("--task-workers 2000",          @("run", $loop, "--task-workers", "2000"),              2, "--task-workers 1 ile 1024", 60),
  @("--task-workers metin",         @("run", $loop, "--task-workers", "abc"),               2, "--task-workers 1 ile 1024", 60),
  @("--task-workers 4 kabul (yorumlayicida etkisiz)", @("run", $loop, "--task-workers", "4"), 0, "800020000", 120),
  @("sonsuz dongu sinirsiz = zaman asimi", @("run", $inf, "--interpreter-backend", "MIR"), -999, "TIMEOUT", 6)
)
$pass = 0; $fail = 0
try {
  foreach ($c in $cases) {
    $r = Invoke-Uxb $c[1] $c[4]
    $okExit = ($c[2] -eq -1) -or ($r.Exit -eq $c[2])
    $okText = $r.Text.Contains($c[3])
    if ($okExit -and $okText) { $pass++; Write-Host "  PASS $($c[0])" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $($c[0])`n    beklenen: cikis=$($c[2]) metin='$($c[3])'`n    gelen   : cikis=$($r.Exit) metin='$(($r.Text -split "`n" | Where-Object { $_ -notmatch '^INFO|^\s*$' } | Select-Object -First 3) -join ' | ')'" -ForegroundColor Red }
  }
} finally {
  Get-Process uxb -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe } | ForEach-Object { try { $_.Kill() } catch {} }
  if ($scratch -and (Test-Path $scratch)) { try { [IO.Directory]::Delete($scratch, $true) } catch {} }
}
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }