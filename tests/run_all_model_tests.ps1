[CmdletBinding()]
param(
  [string]$Uxb = ".\bin\uxb.exe",
  # Yalnız belirli paketleri koşmak için: -Only oop_parity,iterators
  [string[]]$Only = @(),
  # Hızlı tur: yalnız AST + canonical-MIR yerine tüm dört motor değil, paketin kendi koşucusu ne yapıyorsa o.
  [string]$ReportPath = ".\test_results\model_suite_summary.md",
  # Varsayilan: her uxb cagrisinin urettigi build\<zaman> klasoru (S-117: ~1,7 MB, FFI'li programlarda +53 MB DLL)
  # gecici bir --out-root altina yonlendirilir ve koşu bitince silinir. Klasorleri build\ altinda tutmak icin:
  [switch]$KeepBuildFolders
)
# S-072 (ilk parça): dil davranış paketlerinin TEK koşucusu.
# Her paket kendi klasöründeki run_*.ps1 ile çalışır (AST, canonical-MIR, native x64, legacy AST-x64;
# beklenen çıktı expected/<ad>.txt, hata metni expected/<ad>.contains.txt, motor süzgeci expected/<ad>.engines.txt).
# Bu betik: hepsini sırayla koşar, "Toplam/PASS/FAIL" satırını okur, tek tablo yazar, bir paket bile
# düşerse çıkış kodu 1 verir. Sessiz atlama yoktur: bir koşucu çalışmazsa o paket "CALISMADI" sayılır ve tabloda görünür.
$ErrorActionPreference = "Continue"
$root = (Get-Location).Path

$suites = @(
  @{ Name = "numeric_model";   Script = "tests\numeric_model\run_numeric_model_tests.ps1";      Konu = "U64/I64/dar tamsayi/onaltilik literal" },
  @{ Name = "library_type_contract"; Script = "tests\library_type_contract\run_library_type_tests.ps1"; Konu = "LIBTYPE lifecycle, RATIONAL deger aktarimi ve provider tanilari (MIR)" },
  @{ Name = "abi_model";       Script = "tests\abi_model\run_abi_model_tests.ps1";              Konu = "SIZEOF, F80 ABI, TYPE alanlari, VARPTR(a(i))" },
  @{ Name = "memoryref_model"; Script = "tests\memoryref_model\run_memoryref_model_tests.ps1";  Konu = "MemoryRef bolge/omur denetimi" },
  @{ Name = "memory_model";    Script = "tests\memory_model\run_memory_model_tests.ps1";        Konu = "AUTO/NATIVE/VIRTUAL, VARPTR, isaretci aritmetigi" },
  @{ Name = "array_params";    Script = "tests\array_params\run_array_param_tests.ps1";         Konu = "dizi parametreleri + sinir denetimi" },
  @{ Name = "sadd_model";      Script = "tests\sadd_model\run_sadd_model_tests.ps1";            Konu = "SADD, CODEPTR, LPTR" },
  @{ Name = "language_guards"; Script = "tests\language_guards\run_language_guard_tests.ps1";   Konu = "rezerve adlar, bellek deyimleri kapisi" },
  @{ Name = "oop_parity";      Script = "tests\oop_parity\run_oop_parity_tests.ps1";            Konu = "OOP: sanal dagitim, SUPER, miras, erisim, null alici" },
  @{ Name = "array_bounds";    Script = "tests\array_bounds\run_array_bounds_tests.ps1";        Konu = "LBOUND/UBOUND: sabit, REDIM, parametre, cok boyutlu (AST/MIR/x64/legacy/JS)" },
  @{ Name = "iterators";       Script = "tests\iterators\run_iterator_tests.ps1";               Konu = "FOR EACH / DO EACH" },
  @{ Name = "typed_task";      Script = "tests\typed_task_routines\run_typed_task_tests.ps1";   Konu = "tipli gorev rutinleri" },
  @{ Name = "task_model";      Script = "tests\task_model\run_task_model_tests.ps1";            Konu = "S-030 SPAWN/TASK/TASKGROUP + S-146 izolasyon: AST/MIR/native x64 calisir, legacy temiz red (expected\_engines.txt)" },
  @{ Name = "program_end";     Script = "tests\program_end\run_program_end_tests.ps1"; Konu = "S-156: rutin/ic ice ifade icindeki END programi bitirir (AST/MIR/x64; legacy rutin ici acik red)" },
  @{ Name = "string_lifetime"; Script = "tests\string_lifetime\run_string_lifetime_tests.ps1"; Konu = "S-157/S-158: STRING degisken/dizi/alan/yerel donus metni ezilmez; AST TYPE/CLASS STRING alanlari (AST/MIR/x64)" },
  @{ Name = "task_native";     Script = "tests\task_native\run_task_native_tests.ps1";          Konu = "S-030 Faz 2A: native gercek eszamanlilik (iptal, ic ice SPAWN, PRINT satiri, isci 1/2/AUTO x3)" },
  @{ Name = "task_sync";       Script = "tests\task_sync\run_task_sync_tests.ps1";              Konu = "S-146 Model D: otomatik senkron, LOCK, MUTEX, ATOMIC, UNSAFE ve kilitlenme tanilari (AST/MIR/x64; legacy acik red)" },
  @{ Name = "routine_scope";   Script = "tests\routine_scope\run_routine_scope_tests.ps1";     Konu = "S-167/S-168: BYREF gercek takma ad (ic ice, takas, ozyineleme, STRING); rutin yereli/parametresi ayni adli globali golgeler (AST/MIR/x64; legacy BYREF acik red)" },
  @{ Name = "exceptions_cross"; Script = "tests\exceptions_cross\run_exceptions_cross_tests.ps1"; Konu = "S-160: THROW/ASSERT rutin sinirini gecer; cagirandaki TRY yakalar, TRY disinda program durur, gorevde gorev hatasi; LOCK CATCH girisinde birakilir (AST/MIR/x64; legacy acik red)" },
  @{ Name = "uxgsl";           Script = "tests\libraries\uxgsl\run_uxgsl_smoke_tests.ps1";       Konu = "uxgsl (GSL) dort motorda; callback yalniz native" },
  @{ Name = "uxraylib";        Script = "tests\libraries\uxraylib\run_uxraylib_smoke_tests.ps1"; Konu = "uxraylib Image API (CPU-tarafi) dort motorda" },
  @{ Name = "uxsdl3";          Script = "tests\libraries\uxsdl3\run_uxsdl3_smoke_tests.ps1";     Konu = "uxsdl3 (SDL3): pencere/cizim/girdi/gamepad/ses/dosya sistemi, basliksiz (dummy surucu), dort motorda" },
  @{ Name = "const_scope";     Script = "tests\const_scope\run_const_scope_tests.ps1";            Konu = "CONST kapsami: modul/NAMESPACE/rutin ici, tamsayi/F64/STRING, golgeleme; bes motor (S-140)" },
  @{ Name = "float_text";      Script = "tests\float_text\run_float_text_tests.ps1";              Konu = "ondalik sayi metni: F64 16 / F32 7 hane, ilave sifir yok, ayni kural tum motorlarda (S-142b)" },
  @{ Name = "wasm_model";      Script = "tests\wasm_model\run_wasm_model_tests.ps1";              Konu = "WASM/WAT: global degisken/dizi, golgeleme (node ile gercek calistirma)" },
  @{ Name = "cli_flags";       Script = "tests\cli_flags\run_cli_flag_tests.ps1";               Konu = "CLI fiil/bayrak: help, version, --max-steps" }
)
if ($Only.Count -gt 0) { $suites = $suites | Where-Object { $Only -contains $_.Name } }

$results = @()
$started = Get-Date
$scratch = $null
$UxbLabel = $Uxb
if (-not $KeepBuildFolders) {
  $scratch = Join-Path ([IO.Path]::GetTempPath()) ("uxb_model_runs_" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
  New-Item -ItemType Directory -Force $scratch | Out-Null
  $realUxb = (Resolve-Path $Uxb).Path
  $wrapper = Join-Path $scratch "uxb_wrap.cmd"
  # her cagriya --out-root eklenir; cikis kodu aynen iletilir
  [IO.File]::WriteAllText($wrapper, "@echo off`r`n`"$realUxb`" %* --out-root `"$scratch\runs`"`r`nexit /b %ERRORLEVEL%`r`n", [Text.Encoding]::ASCII)
  $Uxb = $wrapper
}
try {
foreach ($s in $suites) {
  $scriptPath = Join-Path $root $s.Script
  $row = [ordered]@{ Paket = $s.Name; Konu = $s.Konu; Toplam = 0; Gecen = 0; Kalan = 0; Durum = "CALISMADI"; Sure = 0 }
  if (-not (Test-Path $scriptPath)) { $row.Durum = "KOSUCU-YOK"; $results += [pscustomobject]$row; continue }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  # *>&1: paketlerin Write-Host (PASS/FAIL) satırları da yakalanır, konsolu doldurmaz
  $out = & $scriptPath -Uxb $Uxb *>&1 | Out-String
  $sw.Stop()
  $row.Sure = [int]$sw.Elapsed.TotalSeconds
  $m = [regex]::Match($out, "Toplam:\s*(\d+)\s+PASS:\s*(\d+)\s+FAIL:\s*(\d+)")
  if ($m.Success) {
    $row.Toplam = [int]$m.Groups[1].Value; $row.Gecen = [int]$m.Groups[2].Value; $row.Kalan = [int]$m.Groups[3].Value
    $row.Durum = if ($row.Kalan -eq 0 -and $row.Toplam -gt 0) { "GECTI" } else { "DUSTU" }
  }
  if ($row.Durum -ne "GECTI") {
    # düşen/çalışmayan paketin kanıtı: FAIL satırları
    # FAIL satiri + hemen ardindaki "beklenen/gelen" satirlari (kanit kaybolmasin)
    $lines = $out -split "`r?`n"
    $failParts = @()
    for ($li = 0; $li -lt $lines.Count -and $failParts.Count -lt 24; $li++) {
      if ($lines[$li] -match "FAIL ") { $failParts += $lines[$li]; if ($li + 1 -lt $lines.Count) { $failParts += $lines[$li + 1] }; if ($li + 2 -lt $lines.Count) { $failParts += $lines[$li + 2] } }
    }
    $fails = $failParts -join "`n"
    if ($fails) { Write-Host $fails -ForegroundColor Red }
  }
  $results += [pscustomobject]$row
  # her paketten sonra o pakete ait gecici klasorler silinir (tepe disk kullanimi bir paketle sinirli kalir)
  if ($scratch -and (Test-Path "$scratch\runs")) { try { [IO.Directory]::Delete("$scratch\runs", $true) } catch {} }
}
} finally {
  # yalniz bu betigin kendi olusturdugu gecici klasor silinir
  if ($scratch -and (Test-Path $scratch)) { try { [IO.Directory]::Delete($scratch, $true) } catch { Write-Host "UYARI: gecici klasor silinemedi: $scratch" -ForegroundColor Yellow } }
}

$toplam = ($results | Measure-Object Toplam -Sum).Sum
$gecen = ($results | Measure-Object Gecen -Sum).Sum
$bad = @($results | Where-Object { $_.Durum -ne "GECTI" })
"==================== TUM MODEL PAKETLERI ===================="
$results | Format-Table Paket, Toplam, Gecen, Kalan, Durum, Sure, Konu -AutoSize | Out-String -Width 200
"Genel: $gecen / $toplam kontrol gecti; $($results.Count - $bad.Count) / $($results.Count) paket temiz.   Sure: $([int]((Get-Date) - $started).TotalSeconds) sn"

# rapor (Markdown) -- sonraki turlarda karsilastirma icin
$dir = Split-Path $ReportPath -Parent
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$md = @("# Model paketleri özeti", "", "Tarih: $(Get-Date -Format 's')  ·  ikili: $UxbLabel", "", "| Paket | Toplam | Geçen | Kalan | Durum | Süre (sn) | Konu |", "|---|---:|---:|---:|---|---:|---|")
foreach ($r in $results) { $md += "| $($r.Paket) | $($r.Toplam) | $($r.Gecen) | $($r.Kalan) | $($r.Durum) | $($r.Sure) | $($r.Konu) |" }
$md += ""; $md += "Genel: **$gecen / $toplam** kontrol geçti."
[IO.File]::WriteAllText((Join-Path $root $ReportPath), ($md -join "`r`n") + "`r`n", (New-Object Text.UTF8Encoding($false)))
if ($bad.Count -gt 0) { exit 1 }
"Tum paketler temiz."
