[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\task_model")
# S-030 TASK/SPAWN/TASKGROUP modeli: her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64 motorlarinda calistirilir.
# expected/_engines.txt  : motor basina durum, "MOTOR=run" veya "MOTOR=reject" (S-030 faz durumu; tek yerde tutulur).
#   run    -> cikti expected/<ad>.txt ile birebir ayni olmali (ya da <ad>.contains.txt'deki o motor satirini icermeli).
#   reject -> motor TEMIZ reddetmeli: sonuc "ERROR:" icermeli ve "Execution completed successfully" icermemeli
#             (sessiz yanlis sonuc yasak). Red metni kasten sabitlenmez; acik red iletileri Faz 1B/2'de eklenince
#             _engines.txt "MOTOR=reject:<metin>" bicimiyle o metni zorunlu kilabilir.
# expected/<ad>.contains.txt : "MOTOR=alt dize" ya da "ALL=alt dize"; neg_* derleme hatalari tum motorlarda ayni tanidir
#             ve motor durumundan bagimsiz uygulanir (semantik kapi motordan once calisir).
# JS bu pakete Faz 3'te (Antigravity, S-030 K8) eklenecek.
$ErrorActionPreference = "Continue"
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO: uXBasic started|^WARN|^\s*$' }) -join "`n" }
function Invoke-UxbWithInput([string[]]$Arguments, [string]$InputText) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = (Resolve-Path $Uxb).Path
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  foreach ($arg in $Arguments) { [void]$psi.ArgumentList.Add([string]$arg) }
  $p = [System.Diagnostics.Process]::new()
  $p.StartInfo = $psi
  if (-not $p.Start()) { return "ERROR: test process baslatilamadi" }
  $p.StandardInput.Write($InputText)
  $p.StandardInput.Close()
  if (-not $p.WaitForExit(30000)) {
    try { $p.Kill() } catch {}
    return "ERROR: test process 30 saniyede tamamlanmadi"
  }
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  if ($stderr -ne "") { $stdout += "`n" + $stderr }
  return $stdout
}
$engineMode = [ordered]@{}
foreach ($ln in (Get-Content (Join-Path $TestRoot "expected\_engines.txt"))) {
  if ($ln -match "^\s*([^#=][^=]*)=(.*)$") { $engineMode[$Matches[1].Trim()] = $Matches[2].Trim() }
}
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_task_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$pass = 0; $fail = 0
try {
  foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
    $base = $f.BaseName
    $containsFile = Join-Path $TestRoot "expected\$base.contains.txt"
    $contains = @{}
    if (Test-Path $containsFile) { foreach ($ln in (Get-Content $containsFile)) { if ($ln -match "^\s*([^=]+)=(.*)$") { $contains[$Matches[1].Trim()] = $Matches[2] } } }
    $expectedFile = Join-Path $TestRoot "expected\$base.txt"
    $expected = if (Test-Path $expectedFile) { "$(Get-Content $expectedFile -Raw)".Trim() -replace "`r","" } else { $null }
    $stdinFile = Join-Path $TestRoot "expected\$base.stdin.txt"
    $stdinText = if (Test-Path $stdinFile) { "$(Get-Content $stdinFile -Raw)" } else { $null }
    $results = [ordered]@{}
    foreach ($eng in $engineMode.Keys) {
      switch ($eng) {
        "AST" {
          $args = @("run", $f.FullName, "--out-root", $tmpRoot)
          $results[$eng] = if ($null -ne $stdinText) { Norm (Invoke-UxbWithInput $args $stdinText) } else { Norm ((& $Uxb @args 2>&1) -join "`n") }
        }
        "MIR" {
          $args = @("run", $f.FullName, "--interpreter-backend", "MIR", "--out-root", $tmpRoot)
          $results[$eng] = if ($null -ne $stdinText) { Norm (Invoke-UxbWithInput $args $stdinText) } else { Norm ((& $Uxb @args 2>&1) -join "`n") }
        }
        { $_ -eq "x64" -or $_ -eq "AST-x64" } {
          $extra = if ($eng -eq "AST-x64") { @("--x64-mode","AST") } else { @() }
          $o = (& $Uxb bld $f.FullName @extra --out-root $tmpRoot -o (Join-Path $tmpRoot "tm_${base}_$eng.exe") 2>&1) -join "`n"
          $m = [regex]::Match($o, "build tamamlandi: (.+)")
          $results[$eng] = if ($m.Success) { Norm ((& $m.Groups[1].Value.Trim() 2>&1) -join "`n") } else { "BUILDFAIL: " + (Norm $o) }
        }
        default { $results[$eng] = "HATA: bilinmeyen motor $eng" }
      }
    }
    # expected/<ad>.engines.txt: bu test icin motor durumunu ezer ("MOTOR=run"). Ornek: SPAWN icermeyen
    # TRIGGER testi (S-146/K3) native ve legacy x64'te de calismali -- red beklenmez.
    $engineOverride = @{}
    $overrideFile = Join-Path $TestRoot "expected\$base.engines.txt"
    if (Test-Path $overrideFile) { foreach ($ln in (Get-Content $overrideFile)) { if ($ln -match "^\s*([^#=][^=]*)=(.*)$") { $engineOverride[$Matches[1].Trim()] = $Matches[2].Trim() } } }
    foreach ($k in $results.Keys) {
      $mode = if ($engineOverride.ContainsKey($k)) { $engineOverride[$k] } else { $engineMode[$k] }
      $want = ""
      if ($contains.ContainsKey("ALL")) {
        $want = "icerir: " + $contains["ALL"]
        $okCase = $results[$k].Contains($contains["ALL"])
      }
      elseif ($mode -like "reject*") {
        # Teste ozel red metni (<ad>.contains.txt'de "MOTOR=...") motor genel red metninden onceliklidir:
        # ornegin JOINALL tum motorlarda MIR derleme asamasinda S-147 iletisiyle, emitter'dan ONCE reddedilir.
        $rejectText = if ($contains.ContainsKey($k)) { $contains[$k] } elseif ($mode -match "^reject:(.+)$") { $Matches[1] } else { "" }
        $want = "temiz red (ERROR:" + $(if ($rejectText) { " + '$rejectText'" } else { "" }) + ")"
        $okCase = $results[$k].Contains("ERROR:") -and -not $results[$k].Contains("Execution completed successfully")
        if ($okCase -and $rejectText) { $okCase = $results[$k].Contains($rejectText) }
      }
      elseif ($contains.ContainsKey($k)) {
        $want = "icerir: " + $contains[$k]
        $okCase = $results[$k].Contains($contains[$k])
      }
      elseif ($null -ne $expected) {
        $want = $expected -replace "`n", ' | '
        $okCase = ((($results[$k] -split "`n") | Where-Object { $_ -notmatch '^INFO' }) -join "`n") -eq $expected
      }
      else {
        $want = "beklenen dosya yok: expected\$base.txt veya $base.contains.txt"
        $okCase = $false
      }
      if ($okCase) { $pass++; Write-Host "  PASS $k/$base" -ForegroundColor Green }
      else { $fail++; Write-Host "  FAIL $k/$base`n    beklenen: $want`n    gelen   : $($results[$k] -replace "`n",' | ')" -ForegroundColor Red }
    }
  }
} finally { if (Test-Path $tmpRoot) { try { [IO.Directory]::Delete($tmpRoot, $true) } catch {} } }
"==================== OZET ===================="
"Toplam: $($pass+$fail)   PASS: $pass   FAIL: $fail"
if ($fail -eq 0) { "Tum kontroller gecti."; exit 0 } else { exit 1 }
