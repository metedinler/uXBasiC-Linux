[CmdletBinding()]
param([string]$Gxx = "C:\msys64\ucrt64\bin\g++.exe", [int]$Repeat = 3)
# S-030 Faz 2A adim 1: gorev ABI v2 calisma zamaninin DLL'siz stres testi.
# uxb_runtime_task_v2.cpp + task_v2_stress.cpp dogrudan derlenir (DLL derleme bayraklariyla ayni: -Wall -Wextra -Werror).
# Her kip ayri surectir; beklenen cikis kodu ve stdout/stderr alt dizesi denetlenir. Zamanlamaya bagli
# hatalari yakalamak icin her kip $Repeat kez, farkli isci sayilariyla (1, 2, AUTO) calistirilir.
$ErrorActionPreference = "Continue"
$here = $PSScriptRoot
$uxb = (Resolve-Path (Join-Path $here "..\..\..")).Path
$src = Join-Path $uxb "native\uxb_runtime"
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("uxb_task_v2_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmp | Out-Null
$exe = Join-Path $tmp "task_v2_stress.exe"
$env:PATH = (Split-Path $Gxx -Parent) + ";" + $env:PATH
# DLL derleme listesinin aynisi (native/uxb_runtime/build_runtime_dll.ps1, std arka ucu) + test kaynagi.
$runtimeSources = @('uxb_runtime.cpp','uxb_runtime_mir.cpp','uxb_runtime_state.cpp','uxb_runtime_task.cpp','uxb_runtime_task_v2.cpp','uxb_runtime_shell.cpp','backends\runtime_backend.cpp','backends\std_backend.cpp','backends\libuv_backend.cpp','backends\tbb_backend.cpp') | ForEach-Object { Join-Path $src $_ }
$build = & $Gxx -std=gnu++17 -O2 -Wall -Wextra -Werror -DUXB_RT_BUILD_DLL "-I$src" @runtimeSources (Join-Path $here "task_v2_stress.cpp") -static-libgcc -static-libstdc++ -o $exe 2>&1
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $exe)) { Write-Host "DERLEME HATASI:"; $build | ForEach-Object { Write-Host "  $_" }; exit 1 }

$cases = @(
  @{ mode = "many";            code = 0; want = "many OK sum=1499500" },
  @{ mode = "parallel";        code = 0; want = "parallel OK workers=" },
  @{ mode = "nested";          code = 0; want = "nested OK fib15=610" },
  @{ mode = "string";          code = 0; want = "string OK merhaba dunya status=DONE" },
  @{ mode = "error_errortext"; code = 0; want = "ERROR|native: uncaught THROW patladi" },
  @{ mode = "error_join";      code = 1; want = "gorev hatasi (Boom): native: uncaught THROW patladi" },
  @{ mode = "error_unread";    code = 1; want = "okunmamis gorev hatasi (Boom): native: uncaught THROW patladi" },
  @{ mode = "cancel";          code = 0; want = "CANCELLED|CANCELLED" },
  @{ mode = "group";           code = 0; want = "group OK sum=72" },
  @{ mode = "group_error";     code = 1; want = "gorev hatasi (Boom)" },
  @{ mode = "print_atomic";    code = 0; want = "print_atomic BITTI" },
  @{ mode = "embedded_workers"; code = 0; want = "embedded_workers OK workers=" },
  @{ mode = "deep_recursion";  code = 0; want = "deep_recursion OK depth=20000" },
  @{ mode = "null_join";       code = 1; want = "TASK.JOIN(): bos (NULL) gorev tutamaci" }
)
$pass = 0; $fail = 0
foreach ($workers in @("1", "2", "")) {
  if ($workers -eq "") { Remove-Item Env:UXB_TASK_WORKERS -ErrorAction SilentlyContinue } else { $env:UXB_TASK_WORKERS = $workers }
  $label = if ($workers -eq "") { "AUTO" } else { $workers }
  for ($r = 1; $r -le $Repeat; $r++) {
    foreach ($c in $cases) {
      $out = (& $exe $c.mode 2>&1 | ForEach-Object { "$_" }) -join " | "
      $code = $LASTEXITCODE
      $lineOk = $true
      if ($c.mode -eq "print_atomic") {
        # Her "L<n>" satiri tam olarak "L<n>" + 20 kez ":<n>" olmali (K9: tek satir baska gorevle bolunmez).
        foreach ($ln in ($out -split ' \| ')) {
          $ln2 = $ln -replace '^(YARIM)+', ''
          if ($ln2 -match '^L(\d+)') { $n = $Matches[1]; if ($ln2 -ne ("L$n" + (":$n" * 20))) { $lineOk = $false; Write-Host "    bozuk satir: $ln"; break } }
        }
        if (([regex]::Matches($out, 'YARIM')).Count -ne 8) { $lineOk = $false; Write-Host "    YARIM sayisi 8 degil" }
      }
      if ($code -eq $c.code -and $out.Contains($c.want) -and $lineOk) { $pass++ }
      else { $fail++; Write-Host "  FAIL isci=$label tur=$r $($c.mode): kod=$code (beklenen $($c.code)) cikti=$out" }
    }
  }
}
Remove-Item Env:UXB_TASK_WORKERS -ErrorAction SilentlyContinue
Write-Host "Toplam: $($pass + $fail)   PASS: $pass   FAIL: $fail"
if ($fail -gt 0) { exit 1 }
Write-Host "Tum kontroller gecti."
exit 0
