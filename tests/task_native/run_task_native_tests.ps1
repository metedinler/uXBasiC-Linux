[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\task_native", [int]$Repeat = 3, [int]$TimeoutSec = 60)
# S-030 Faz 2A: YALNIZ native x64'te anlamli gercek eszamanlilik testleri (AST/MIR senkron referansta
# bu programlar ya sonsuza kadar doner -- iptal testi -- ya da zamanlama anlamini tasimaz).
# Her program bir kez derlenir, sonra isci sayisi 1, 2 ve AUTO (UXB_TASK_WORKERS) ile $Repeat kez
# calistirilir; zamanlamaya bagli hatalar tekrarla yakalanir. Zaman asimi = takilma = FAIL.
# expected/<ad>.txt: birebir cikti. native_print_lines ozel denetim: her satir tek parca.
$ErrorActionPreference = "Continue"
function Norm([string]$s) { (($s -replace "`r","") -split "`n" | Where-Object { $_ -notmatch '^INFO|^WARN|^\s*$' }) -join "`n" }
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ("uxb_tasknat_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$pass = 0; $fail = 0
try {
  foreach ($f in Get-ChildItem $TestRoot -Filter *.uxb | Sort-Object Name) {
    $base = $f.BaseName
    $exe = Join-Path $tmpRoot "$base.exe"
    $o = (& $Uxb bld $f.FullName --out-root $tmpRoot -o $exe 2>&1) -join "`n"
    $m = [regex]::Match($o, "build tamamlandi: (.+)")
    if (-not $m.Success) { $fail++; Write-Host "  FAIL $base derleme: $(Norm $o)"; continue }
    $built = $m.Groups[1].Value.Trim()
    $expectedFile = Join-Path $TestRoot "expected\$base.txt"
    $expected = if (Test-Path $expectedFile) { ("$(Get-Content $expectedFile -Raw)".Trim()) -replace "`r","" } else { $null }
    foreach ($workers in @("1", "2", "")) {
      $label = if ($workers -eq "") { "AUTO" } else { $workers }
      for ($r = 1; $r -le $Repeat; $r++) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $built
        $psi.WorkingDirectory = Split-Path $built -Parent
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        if ($workers -ne "") { $psi.EnvironmentVariables["UXB_TASK_WORKERS"] = $workers } else { [void]$psi.EnvironmentVariables.Remove("UXB_TASK_WORKERS") }
        $p = [System.Diagnostics.Process]::Start($psi)
        $outTask = $p.StandardOutput.ReadToEndAsync()
        $errTask = $p.StandardError.ReadToEndAsync()
        if (-not $p.WaitForExit($TimeoutSec * 1000)) {
          try { $p.Kill() } catch {}
          $fail++; Write-Host "  FAIL isci=$label tur=$r ${base}: $TimeoutSec sn zaman asimi (takildi)"; continue
        }
        $got = Norm ($outTask.Result + $errTask.Result)
        $ok = $false
        if ($base -eq "native_print_lines") {
          $lines = @($got -split "`n")
          $wLines = @($lines | Where-Object { $_ -like "W*" })
          $bad = @($wLines | Where-Object { ($_ -replace '\s', '') -notmatch '^W(\d+):(\d+):\1:\2:END$' })
          $ok = ($wLines.Count -eq 480) -and ($bad.Count -eq 0) -and ($lines[-1].Trim() -eq "BITTI")
          if (-not $ok) { Write-Host "    satir=$($wLines.Count) bozuk=$($bad.Count) ilk bozuk: $($bad | Select-Object -First 1)" }
        } else {
          $ok = ($null -ne $expected) -and ($got -eq $expected)
        }
        if ($ok -and $p.ExitCode -eq 0) { $pass++ }
        else { $fail++; Write-Host "  FAIL isci=$label tur=$r ${base}: cikis=$($p.ExitCode)"; Write-Host "    beklenen: $($expected -replace "`n", ' | ')"; Write-Host "    gelen   : $($got -replace "`n", ' | ')" }
      }
    }
  }
} finally {
  $resolvedTemp = [IO.Path]::GetFullPath($tmpRoot)
  $tempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')
  if ([IO.Path]::GetDirectoryName($resolvedTemp) -ne $tempParent -or
      -not [IO.Path]::GetFileName($resolvedTemp).StartsWith('uxb_tasknat_')) {
    throw 'Refusing cleanup outside this task-native invocation temp directory.'
  }
  Remove-Item -LiteralPath $resolvedTemp -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "Toplam: $($pass + $fail)   PASS: $pass   FAIL: $fail"
if ($fail -gt 0) { exit 1 }
Write-Host "Tum kontroller gecti."
exit 0
