[CmdletBinding()]
param(
  [string]$Uxb = ".\bin\uxb.exe",
  # Yalnız belirli paketleri koşmak için: -Only oop_parity,iterators
  [string[]]$Only = @(),
  # Selected packages must expose their existing -Only case filter.
  [string[]]$Cases = @(),
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
foreach ($filterName in @('Only','Cases')) {
  $rawFilter = [string[]](Get-Variable -Name $filterName).Value
  $normalizedFilter = @($rawFilter | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
  if ($rawFilter.Count -gt 0 -and $normalizedFilter.Count -eq 0) { throw "$filterName filter is empty" }
  Set-Variable -Name $filterName -Value $normalizedFilter
}
$root = (Get-Location).Path

$suites = @(
  @{ Name = "compiler_consolidation"; Script = "tests\compiler_consolidation\run_consolidation_tests.ps1"; Konu = "matris, dosya/metin, SELECT, DIM, DECLARE, PRINT, float/property ve Win64 ABI" },
  @{ Name = "numeric_model";   Script = "tests\numeric_model\run_numeric_model_tests.ps1";      Konu = "U64/I64/dar tamsayi/onaltilik literal" },
  @{ Name = "library_type_contract"; Script = "tests\library_type_contract\run_library_type_tests.ps1"; Konu = "LIBTYPE lifecycle, RATIONAL deger aktarimi ve provider tanilari (MIR)" },
  @{ Name = "libtype_target_gate"; Script = "tests\diagnostics\run_s499_libtype_target_gate_tests.ps1"; Konu = "S-499: kullanilan birinci sinif library type icin hedef provider kapisi" },
  @{ Name = "abi_model";       Script = "tests\abi_model\run_abi_model_tests.ps1";              Konu = "SIZEOF, F80 ABI, TYPE alanlari, VARPTR(a(i))" },
  @{ Name = "memoryref_model"; Script = "tests\memoryref_model\run_memoryref_model_tests.ps1";  Konu = "MemoryRef bolge/omur denetimi" },
  @{ Name = "memory_model";    Script = "tests\memory_model\run_memory_model_tests.ps1";        Konu = "AUTO/NATIVE/VIRTUAL, VARPTR, isaretci aritmetigi" },
  @{ Name = "array_params";    Script = "tests\array_params\run_array_param_tests.ps1";         Konu = "dizi parametreleri + sinir denetimi" },
  @{ Name = "sadd_model";      Script = "tests\sadd_model\run_sadd_model_tests.ps1";            Konu = "SADD, CODEPTR, LPTR" },
  @{ Name = "language_guards"; Script = "tests\language_guards\run_language_guard_tests.ps1";   Konu = "rezerve adlar, bellek deyimleri kapisi" },
  @{ Name = "oop_parity";      Script = "tests\oop_parity\run_oop_parity_tests.ps1";            Konu = "OOP: sanal dagitim, SUPER, miras, erisim, null alici" },
  @{ Name = "oop_remaining"; Script = "tests\oop_remaining\run_oop_remaining_tests.ps1"; Konu = "S-578/S-585/S-627: arayuz ABI, sonuc tipi ve USING; alti motor" },
  @{ Name = "oop_class_arrays"; Script = "tests\oop_class_arrays\run_oop_class_array_tests.ps1"; Konu = "S-617: sinif dizisi basvurusu, alias, NULL, dinamik indeks ve DELETE; alti motor" },
  @{ Name = "wasm_types"; Script = "tests\wasm_types\run_wasm_types_tests.ps1"; Konu = "S-001/S-007 ve WASM F32/F64/STRING gercek alti motor kabul" },
  @{ Name = "task_legacy_v2"; Script = "tests\task_legacy_v2\run_task_legacy_v2_tests.ps1"; Konu = "S-030 native v2: typed TASK/group/STRING/NUL, cancel/error, local DIM and FFI identity; scoped positive execution" },
  @{ Name = "task_aggregate_assign"; Script = "tests\task_provider_completion\run_aggregate_assign_tests.ps1"; Konu = "S-645..S-650: actual numeric aggregate assignment, once-resolved targets, calls outside locks and typed stores" },
  @{ Name = "task_lvalue_sync"; Script = "tests\task_provider_completion\run_lvalue_sync_tests.ps1"; Konu = "S-634..S-644: once-resolved numeric INCDEC, typed aggregate storage and PROPERTY VALUE/ABI/scope" },
  @{ Name = "task_argument_sync"; Script = "tests\task_provider_completion\run_argument_sync_tests.ps1"; Konu = "S-030: numeric shared arguments, nested calls and typed INCDEC_EXPR with actual workers" },
  @{ Name = "task_scalar_sync"; Script = "tests\task_provider_completion\run_scalar_sync_tests.ps1"; Konu = "S-030 shared scalar statement locks, call snapshots, declared numeric storage and two real workers" },
  @{ Name = "task_loader_contract"; Script = "tests\task_provider_completion\run_loader_and_incdec_tests.ps1"; Konu = "S-030 numeric INCDEC and real native loader/copy fault contract" },
  @{ Name = "native_nul"; Script = "tests\native_nul\run_native_nul_tests.ps1"; Konu = "S-630: NUL uzunlugu, sahiplik, dilimleme ve gercek cikti; alti motor" },
  @{ Name = "task_nul"; Script = "tests\task_native\run_task_nul_tests.ps1"; Konu = "S-630/S-030: SPAWN STRING kopyasi ve JOIN sonucu NUL uzunlugunu korur; AST/MIR/native" },
  @{ Name = "print_zones"; Script = "tests\print_zones\run_print_zone_tests.ps1"; Konu = "S-251/S-180: PRINT bolge/kolon, sona virgul ve bos satir; ham stdout alti motor" },
  @{ Name = "console_cursor"; Script = "tests\print_zones\run_print_zone_tests.ps1"; TestRoot = "tests\console_cursor"; Konu = "S-716: CSRLIN/POS guncel konum, LOCATE/CLS/PRINT bolgeleri ve Unicode; gercek alti motor" },
  @{ Name = "oop_redim"; Script = "tests\oop_redim\run_oop_redim_tests.ps1"; Konu = "S-629/M7: dinamik CLASS sekli ve REDIM PRESERVE kesisimi; alti motor" },
  @{ Name = "oop_multidim"; Script = "tests\oop_multidim\run_oop_multidim_tests.ps1"; Konu = "S-629: cok boyutlu CLASS, eksen siniri, sekil sorgusu ve yerel golgeleme; alti motor" },
  @{ Name = "declare_siki";    Script = "tests\declare_siki\run_declare_siki_tests.ps1";        Konu = "S-544: siki DECLARE (ileri kullanim, tanimsiz DECLARE, ad+parametre sayisi); altı yol" },
  @{ Name = "dosya_tutamaci";  Script = "tests\dosya_tutamaci\run_dosya_tutamaci_tests.ps1";    Konu = "S-548/S-549: FREEFILE ve FILE_HANDLE (OPEN AS handle, CLOSE handle, kanal defteri); AST/MIR/x64/eski AST-x64, JS/WASM acik ret" },
  @{ Name = "turkce_ad";       Script = "tests\turkce_ad\run_turkce_ad_tests.ps1";              Konu = "S-579: Turkce adlar, harf esleme, kod cakismasi ve WASM tanimsiz cagri; alti motor" },
  @{ Name = "array_bounds";    Script = "tests\array_bounds\run_array_bounds_tests.ps1";        Konu = "LBOUND/UBOUND: sabit, REDIM, parametre, cok boyutlu (AST/MIR/x64/legacy/JS)" },
  @{ Name = "iterators";       Script = "tests\iterators\run_iterator_tests.ps1";               Konu = "FOR EACH / DO EACH" },
  @{ Name = "typed_task";      Script = "tests\typed_task_routines\run_typed_task_tests.ps1";   Konu = "tipli gorev rutinleri" },
  @{ Name = "task_model";      Script = "tests\task_model\run_task_model_tests.ps1";            Konu = "S-030 SPAWN/TASK/TASKGROUP + S-146 izolasyon: AST/MIR/native x64 calisir, legacy temiz red (expected\_engines.txt)" },
  @{ Name = "program_end";     Script = "tests\program_end\run_program_end_tests.ps1"; Konu = "S-156: rutin/ic ice ifade icindeki END programi bitirir (AST/MIR/x64/eski AST-x64; S-538)" },
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
  @{ Name = "output_isolation"; Script = "tests\output_isolation\run_output_isolation_tests.ps1"; Konu = "S-028/S-632: shared INCLUDE macro state and CWD/out-root isolation with six actual engines" },
  @{ Name = "preprocessor_unified"; Script = "tests\preprocessor_unified\run_unified_tests.ps1"; Konu = "S-321: shared blocks/manifest, removed selectors and inactive-branch effects" },
  @{ Name = "web_report_evidence"; Script = "tests\cli_mir_semantic\run_web_report_tests.ps1"; Konu = "S-027: web static MIR evidence is separate from actual JS/WASM execution" },
  @{ Name = "cli_mir_semantic"; Script = "tests\cli_mir_semantic\run_cli_mir_semantic_tests.ps1"; Konu = "S-024: MIR CLI alias semantic gate, typed parameters and invalid assignment" },
  @{ Name = "diagnostics";     Script = "tests\diagnostics\run_parenless_call_tests.ps1";       Konu = "S-440: parantezsiz cagri reddi ve tum hedeflerde ortak tanı kodu" },
  @{ Name = "const_write";     Script = "tests\diagnostics\run_const_write_tests.ps1";          Konu = "S-441: CONST yazma ve BYREF sabit gecisi ortak tanisi" }
  @{ Name = "union_overlay";   Script = "tests\diagnostics\run_union_overlay_tests.ps1";        Konu = "S-442: UNION ortak MIR alan ortusu AST/MIR/x64/JS/WAT" }
  @{ Name = "magic_bitwise";   Script = "tests\diagnostics\run_s443_magic_tests.ps1";           Konu = "S-443: MAGIC AND/OR/XOR primitive ve object-return AST/MIR/x64/JS" }
  @{ Name = "js_exceptions";   Script = "tests\diagnostics\run_s444_js_exception_tests.ps1";    Konu = "S-444: JS uncaught THROW/ASSERT async hata siniri" },
  @{ Name = "dll_type_list";   Script = "tests\diagnostics\run_s445_dll_type_list_tests.ps1";  Konu = "S-445: CALL(DLL) bilinmeyen arguman tip listesinin tum hedeflerde ortak reddi" },
  @{ Name = "f32_parity";      Script = "tests\diagnostics\run_s446_f32_tests.ps1";             Konu = "S-446: F32 saklama, aritmetik ve metin cikti paritysi" },
  @{ Name = "s480_ast_regressions"; Script = "tests\diagnostics\run_s480_ast_regression_tests.ps1"; Konu = "S-480: AST cok boyutlu dizi, sinir denetimi ve I32 donusum geri uyumlulugu" }
  @{ Name = "s502_f32_array_direct"; Script = "tests\diagnostics\run_s502_f32_array_direct_tests.ps1"; Konu = "S-502: F32 dizi elemaninin dogrudan okuma, STR ve F64 donusumu" }
  @{ Name = "s503_f32_storage"; Script = "tests\diagnostics\run_s503_f32_storage_tests.ps1"; Konu = "S-503: F32 DIM baslangici, atama ve dizi saklama paritysi" }
  @{ Name = "s505_unary_comparison"; Script = "tests\diagnostics\run_s505_unary_comparison_tests.ps1"; Konu = "S-505: karsilastirma sonucuna tekli eksi, MIR-x64 kanonik I64 ve WASM gercek F64 yurutme" }
  @{ Name = "s506_float_to_integer"; Script = "tests\diagnostics\run_s506_float_to_integer_tests.ps1"; Konu = "S-506: AST ondalik-tamsayi donusumu sifira dogru kesme paritysi" }
  @{ Name = "s508_fix_type"; Script = "tests\diagnostics\run_s508_fix_type_tests.ps1"; Konu = "S-508: FIX sonucu statik I32 turu ve tum hedeflerde kullanilabilirligi" }
  @{ Name = "s510_mir_f32_rounding"; Script = "tests\diagnostics\run_s510_mir_f32_rounding_tests.ps1"; Konu = "S-510: MIR F32 saklama ve donusumde gercek tek duyarlik yuvarlamasi" }
@{ Name = "s459_mixed_numeric_string"; Script = "tests\diagnostics\run_s459_mixed_numeric_string_tests.ps1"; Konu = "S-459/S-460: sayisal ve STRING operandlar icin ortak acik tip tanisi" }
  @{ Name = "s464_interpreter_compare"; Script = "tests\diagnostics\run_s464_interpreter_compare_tests.ps1"; Konu = "S-464: AST/MIR BOTH karsilastirmasi ve sessiz ayrisma kapisi" }
  @{ Name = "s500_libtype_diagnostics"; Script = "tests\diagnostics\run_s500_libtype_diagnostic_consistency_tests.ps1"; Konu = "S-500: birinci sinif kutuphane tipi provider tanilarinda ortak alan sozlesmesi" }
  @{ Name = "s219_rotate_width"; Script = "tests\diagnostics\run_s219_rotate_width_tests.ps1"; Konu = "S-219: ROL/ROR sol operand genisligi ve signedness paritysi" }
  @{ Name = "kv_kapanis"; Script = "tests\kv_kapanis\run_kv_kapanis_tests.ps1"; Konu = "Kilavuz V2 kayit kapanislari (S-523, S-532, S-535, S-539..S-543, S-562..S-569, S-623): AST/MIR/x64/eski AST-x64/JS/WASM (motor listesi expected\*.engines.txt)" }
  @{ Name = "preprocessor_effects"; Script = "tests\preprocessor_effects\run_effects_tests.ps1"; Konu = "S-672: her onislemci yonergesinin gozlenebilir etkisi (terminal, kaynak metni, paket dosyalari, manifest, sayfa, WAT/JS, yerel x64)" }
  @{ Name = "x86_emeklilik"; Script = "tests\x86_emeklilik\run_x86_emeklilik_tests.ps1"; Konu = "S-666: x86 adi her yoldan acik emekli iletisi verir (CLI fiilleri/bayraklari/--target, INLINE arch, UXB_TARGET_ARCH ve ARCH= politikasi); x64 kontrolleri degismez" }
)
if ($Only.Count -gt 0) {
  $unknownSuites = @($Only | Where-Object { $_ -notin $suites.Name })
  if ($unknownSuites.Count -gt 0) { throw ('Unknown test suite: ' + ($unknownSuites -join ', ')) }
  $suites = @($suites | Where-Object { $Only -contains $_.Name })
}

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
  Write-Output "MODEL_START $($s.Name) compiler=$UxbLabel"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  # *>&1: paketlerin Write-Host (PASS/FAIL) satırları da yakalanır, konsolu doldurmaz
  $packageOutput = [Collections.Generic.List[string]]::new()
  try {
    $invocationArguments = @{ Uxb = $Uxb }
    if ($s.ContainsKey('TestRoot')) { $invocationArguments.TestRoot = (Join-Path $root $s.TestRoot) }
    if ($Cases.Count -gt 0) {
      if (!(Get-Command $scriptPath).Parameters.ContainsKey('Only')) {
        throw "Package $($s.Name) does not support a case filter; no cases were silently skipped."
      }
      $invocationArguments.Only = $Cases
    }
    & $scriptPath @invocationArguments *>&1 | ForEach-Object { $packageOutput.Add(($_ | Out-String)) }
  } catch {
    $packageOutput.Add(($_ | Out-String))
    $row.Durum = 'KOSUCU-HATASI'
    $row['Hata'] = $_.Exception.Message
    Write-Output "RUNNER_ERROR $($s.Name): $($row['Hata'])"
  }
  $out = $packageOutput -join "`n"
  $sw.Stop()
  $row.Sure = [int]$sw.Elapsed.TotalSeconds
  $m = [regex]::Match($out, "Toplam:\s*(\d+)\s+PASS:\s*(\d+)\s+FAIL:\s*(\d+)")
  if ($m.Success -and $row.Durum -ne 'KOSUCU-HATASI') {
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
  $packageLog = [IO.Path]::GetFullPath((Join-Path ($ReportPath + '.logs') ($s.Name + '.log')))
  New-Item -ItemType Directory -Force (Split-Path $packageLog -Parent) | Out-Null
  [IO.File]::WriteAllText($packageLog, $out, [Text.UTF8Encoding]::new($false))
  Write-Output "MODEL_DONE $($s.Name) passed=$($row.Gecen)/$($row.Toplam) status=$($row.Durum) seconds=$($row.Sure)"
  # Compact, inspectable progress without rereading the full console transcript.
  $progressPath = [IO.Path]::GetFullPath($ReportPath + '.progress.json')
  $progressParent = Split-Path $progressPath -Parent
  New-Item -ItemType Directory -Force $progressParent | Out-Null
  [ordered]@{
    schema = 'uxb.model_suite_progress.v1'
    compiler = $UxbLabel
    started = $started.ToString('o')
    updated = (Get-Date).ToString('o')
    completed_packages = $results.Count
    requested_packages = $suites.Count
    packages = $results
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $progressPath -Encoding UTF8
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
$md += ""; $md += "Genel: **$gecen / $toplam** ölçülen kontrol geçti; **$($results.Count - $bad.Count) / $($results.Count)** paket temiz."
foreach ($failedRunner in @($results | Where-Object { $_.Durum -eq 'KOSUCU-HATASI' })) {
  $md += ""; $md += "Koşucu hatası ($($failedRunner.Paket)): $($failedRunner.Hata)"
}
# S-542: mutlak -ReportPath, kok klasorun sonuna eklenip gecersiz yol uretiyordu (108 dakikalik kosunun raporu yazilamiyordu)
$reportFullPath = if ([IO.Path]::IsPathRooted($ReportPath)) { $ReportPath } else { Join-Path $root $ReportPath }
[IO.File]::WriteAllText($reportFullPath, ($md -join "`r`n") + "`r`n", (New-Object Text.UTF8Encoding($false)))
if ($bad.Count -gt 0) { exit 1 }
"Tum paketler temiz."
exit 0
