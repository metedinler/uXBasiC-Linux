[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\cli_flags", [switch]$OnlyResponse)
# CLI bayrak/fiil testleri (Mete'nin CLI denetim programinin ilk parcasi): her durum uxb'yi verilen argumanlarla
# calistirir; cikis kodu ve (birlesik stdout+stderr icinde) beklenen metin denetlenir. Sonsuz donguler zaman asimiyla kesilir.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path $TestRoot).Path
$exe = (Resolve-Path $Uxb).Path
# Kendi build klasorlerini gecici bir --out-root'a yonlendir (sarmalayici .cmd zaten yapiyorsa ekleme)
$appendScratch = $exe -notmatch '\.cmd$'
$scratch = Join-Path ([IO.Path]::GetTempPath()) ("uxb_cli_runs_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $scratch | Out-Null
function Invoke-Uxb([string[]]$ArgList, [int]$TimeoutSec = 90) {
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
  if ($appendScratch -and $ArgList -notcontains '--out-root') { [void]$psi.ArgumentList.Add("--out-root"); [void]$psi.ArgumentList.Add($scratch) }
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
  @("uxcli @ run MIR", @("@tests/options/run.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli bare run MIR", @("tests/options/run.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli nested", @("@tests/options/nested.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli quoted path", @("@tests/options/quoted run.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli missing", @("@tests/options/missing.uxcli"), 20, "CLI_RESPONSE_FILE_NOT_FOUND", 60),
  @("uxcli quote error", @("@tests/options/unclosed.uxcli"), 20, "CLI_RESPONSE_FILE_PARSE_FAIL", 60),
  @("uxcli recursion limit", @("@tests/options/cycle.uxcli"), 20, "CLI_RESPONSE_FILE_DEPTH_LIMIT", 60),
  @("uxcli option fragment", @("run", "tests/options/response_source.uxb", "@tests/options/backend.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli UTF8 BOM", @("@tests/options/bom.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli AST run", @("@tests/options/ast.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli inline options", @("@tests/options/inline.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli language after 64", @("@tests/options/long_language.uxcli"), 0, "Unsupported message language requested", 60),
  @("uxcli adjacent comments", @("@tests/options/adjacent_comments.uxcli"), 0, "UXCLI_OK", 60),
  @("uxcli missing MIR gate parent", @("run", "tests/options/response_source.uxb", "--interpreter-backend", "MIR", "--mir-verify-semantic-json-out", (Join-Path $scratch 'new/gate/result.json')), 0, "UXCLI_OK", 60),
  @("uxcli invalid MIR gate parent", @("run", "tests/options/response_source.uxb", "--interpreter-backend", "MIR", "--mir-verify-semantic-json-out", (Join-Path $root 'loop_40000.uxb/gate.json')), 18, "report write", 60),
  @("uxcli raw overflow rejected", (@('run','tests/options/response_source.uxb','--out-root',$scratch) + (@('--strict') * 514)), 20, 'CLI_ARG_LIMIT', 60),
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
# S-466: ust klasoru olmayan yolla verilen cikti bayraklari programi iptal etmez; klasor olusturulur ve dosya yazilir.
# Eskiden bu bayraklarin 12'si FreeBASIC "runtime error 2 (file not found)" ile derleyiciyi dusuruyordu (-exx altinda ciplak Open).
foreach ($b466 in @('--parser-diagnostics-json-out', '--parser-surface-contract-json-out', '--final-screen-json-out', '--program-output-json-out', '--hir-json-out', '--hir-inventory-json-out', '--inventory-json-out', '--ir-json-out', '--mir-opcodes-json-out', '--mir-surface-json-out', '--mir-pipeline-json-out', '--pipeline-json-out', '--semantic-enums-json-out')) {
  $hedef466 = Join-Path $scratch ('s466/' + $b466.Substring(2) + '/yeni/klasor/o.json')
  $cases += ,@("S-466 klasor olusturulur $b466", @("run", "tests/options/response_source.uxb", $b466, $hedef466), 0, "UXCLI_OK", 60, $hedef466)
}
# S-467 / S-356: `--interop`, `run` disindaki fiillerde derleyiciyi dusurmez (eskiden hedef klasor olusmadan ciplak Open: runtime error 2).
foreach ($v467 in @('bld', 'x64', 'jsw', 'wat', 'mir')) {
  $cases += ,@("S-467 $v467 --interop", @($v467, "tests/options/response_source.uxb", "--interop"), 0, "", 120)
}
if ($OnlyResponse) { $cases = @($cases | Where-Object { $_[0] -like 'uxcli *' }) }
$pass = 0; $fail = 0
try {
  foreach ($c in $cases) {
    $r = Invoke-Uxb $c[1] $c[4]
    $okExit = ($c[2] -eq -1) -or ($r.Exit -eq $c[2])
    $okText = $r.Text.Contains($c[3])
    if ($c.Count -gt 5 -and $c[5]) { $okText = $okText -and (Test-Path -LiteralPath $c[5]) }   # 6. oge: yazilmasi beklenen dosya
    if ($okExit -and $okText) { $pass++; Write-Host "  PASS $($c[0])" -ForegroundColor Green }
    else { $fail++; Write-Host "  FAIL $($c[0])`n    beklenen: cikis=$($c[2]) metin='$($c[3])'`n    gelen   : cikis=$($r.Exit) metin='$(($r.Text -split "`n" | Where-Object { $_ -notmatch '^INFO|^\s*$' } | Select-Object -First 3) -join ' | ')'" -ForegroundColor Red }
  }
} finally {
  # Invoke-Uxb owns and time-bounds each child. Never kill another session's
  # process merely because it happens to use this compiler binary.
  if ($scratch -and (Test-Path $scratch)) { try { [IO.Directory]::Delete($scratch, $true) } catch {} }
}
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti." } else { exit 1 }
