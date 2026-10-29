# uXBasic araç, derleme ve test kullanım rehberi

Bu belge, komut satırına hiç alışık olmayan bir kullanıcı için hazırlanmıştır.
Komutları uXBasic klasöründe PowerShell açarak çalıştırın.

Güncel çalışma kuralları: 29 Ekim 2026. Bu belge araç kullanımının ortak
başvurusudur; her koşu için yeni bir kullanım belgesi açılmaz. Sonuçlar
`reports/workspace_maintenance/` veya paketin sonuç klasöründe tutulur.

## 0. Komut penceresi ve `.uxcli` dosyası

`uxb.cmd` dosyasına çift tıklamak komut yazılabilen bir Windows komut
penceresi açar; `exit` ile kapanır. PowerShell'de aynı başlatıcıya seçenek
verilebilir. `UXB_EXE` ortam değişkeniyle özel bir aday seçilmediyse
son doğrulanmış özel aday `build/compilers/codex33/uxb.exe` kullanılır; kaynak ve sürüm kanıtı `reports/workspace_maintenance/current_acceptance.json` içindedir;
bu aday yoksa `bin/uxb.exe` seçilir. Eşleşen private runtime
`build/runtime/codex7` olur; `UXB_NATIVE_RUNTIME_DIR` açıkça verilmişse
başlatıcı onu korur. Claude'un ortak `bin` kurulumunun üzerine yazılmaz.
Komutlara verilen göreli yollar çağrılan klasöre
göredir; başlatıcı bu yolları sessizce değiştirmez.

```powershell
.\uxb.cmd --help
.\uxb.cmd "@tests/options/run.uxcli"
.\uxb.cmd tests/options/run.uxcli
```

`.uxcli`, tek bir compiler çağrısının argüman dosyasıdır; ayrı ayrı
komutları çalıştıran bir shell dili değildir. Örneğin:

```text
# tests/options/run.uxcli
run
tests/options/response_source.uxb
--interpreter-backend MIR
--max-steps 1000
```

Boşlukla ayrılan argümanlar ve satır sonları eşdeğerdir; boşluklu bir yol
çift tırnak içine alınır. `#` tırnak dışında yorum başlatır. İç içe
`@dosya.uxcli` çağrısı en çok 8 düzeydir; yollar çalışma klasörüne göredir.
Eksik dosya, kapanmamış tırnak ve aşırı iç içelik açık CLI hatasıdır.
S-325 düzeltmesinin önce/sonra ölçümleri `reports/workspace_maintenance/cli_response*.log`
altındadır. Bu ölçüm eski dağıtım ikililerinin de düzeldiği anlamına gelmez.

## 0.1 Dosya yerleşimi ve çalışma sınırları

| İçerik | Yer ve kural |
|---|---|
| Compiler kaynakları | `src/`; giriş `src/wrappers/uxb_main_wrapper.bas`, kancalar `src/hooks/`; `src/compiler` oluşturulmaz |
| Yeni ve üretilen test kaynakları | `tests/<paket>/` veya `xtestx/`; örnek programı rapora veya köke yazma |
| Ortak compiler / CLI adayı | `bin/uxb.exe` ortak kurulumdur; bu tur üzerine yazılmaz. `uxb.cmd` yukarıda belirtilen doğrulanmış özel adayı seçer; `UXB_EXE` ile değiştirilebilir |
| Özel compiler adayı | `build/compilers/<oturum>/`; `build_64.ps1 -OutputPath` ile ayrı hedef |
| Özel runtime | `build/runtime/<oturum>/`; DLL, import library ve gerekli bağımlılıklar birlikte; `UXB_NATIVE_RUNTIME_DIR` ile seçilir |
| Geçici program/derleme çıktısı | Koşucunun `--temp-builds` ya da geçici `--out-root` alanı; iş bitince kaldırılır |
| Sonuç kanıtı | `reports/` veya `test_results/`: komut, çıkış, stdout/stderr, kimlik/hash ve ölçüm; çoğaltılmış EXE/DLL deposu değildir |
| Gerekli benzersiz eski ikililer | `build/compilers/retained/` veya `build/artifacts/`; taşıma/silme haritası `reports/workspace_maintenance/binary_*.json*` |

Claude ve Codex güncel CLAIM/dosya değişikliklerini okuyup ayrı hedefler
kullanır. Birbirinin sürecini durdurmaz. Yeni aday gerekli testlerle
doğrulandıktan sonra kullanımda olmayan eski kendi compiler çıktısı
kaldırılır. Son doğrulanmış aday ve gerekli çalışma zamanı korunur.
Kaynaklar, test kaynakları, belgeler, rapor kanıtları ve RAG silinmez.

Önce aşağıdaki mevcut aracı kullan; eksikse onu genişlet. Kaynak yamalarını
geçici Python/PowerShell kod üreticisiyle yazdırma: ilgili FreeBASIC, C/C++
veya Python dosyasını doğrudan düzenle. Betik envanteri CLI bildirimlerini
kaynaktan okur; araçların çalıştığına dair kanıt değildir.

## 0.2 Okunan ve bu iş akışında kullanılacak araçlar

S-030 gerçek kabulü için `tests/turkce_ad/run_tests.py` mevcut görev
paketlerini de okuyabilir. `--test-root tests/task_sync` veya
`tests/task_model`; `--uxb`, `--native-runtime-dir`, `--output` açıkça
verilir. `--jobs 1 --timeout 300`, uzun yorumlayıcı döngülerini başka
ağır paketlerle aynı anda koşturmadan ölçer. Varsayılan süreç bütçesi90
saniyedir; zaman aşımı yine FAIL'dir. `--resume` yalnız aynı EXE/DLL ve
test kimliğiyle geçen hücreleri kullanır, başarısız denemeyi saklayıp yeniden
çalıştırır. Süre bütçesini artırmak kendi başına compiler düzeltmesi değildir.
`expected/<test>.directories.txt` yalnız izole çalışma alanı altında gereken
dizinleri açar; `.stdin.txt` gerçek girdi verir; kısmi `.engines.txt` motor
beklentisini ezer. JSON fixture'ında `environment: {"UXB_TASK_WORKERS":"1"}`
tek işçide iç içe görev kanıtını sabitler. `new_console: true` yalnız native programı gerçek fakat gizli Windows konsoluyla başlatır; ekran tamponu ve tuş kuyruğu sınanabilir. `--timeout` aşımında kısmi stdout/stderr saklanır, sonuç yine FAIL olur. Normal testler süreç çıkışı0 ve
beklenen çıktıyı birlikte gerektirir; beklenen hata süreç başarısı sayılmaz.
Geçici EXE/DLL/assembly varsayılan olarak kaldırılır; ham sonuç/hash saklanır.

| Araç | İşlev ve çağrı |
|---|---|
| `tools/maintenance/uxb_context_index.py` | Belgelerde bölüm arar: `search "S-030" --chars 4000`; belge güncellenince `build`. Word sahiplik kilitleri (~$) belge sayılmaz. Okunamayan gerçek DOCX dosya/hash/hata ile `reports/context_index/document_errors.json` içinde raporlanır; arama uyarıyı da gösterir. Anlamsal doğrulama yapmaz. |
| `tools/maintenance/uxb_coordination_inventory.py` | S kayıt/durum/G eşlemesini çıkarır: `--output reports/coordination_status`. Kayıt durumu çalışan özellik kanıtı değildir. |
| `tools/maintenance/uxb_acceptance_inventory.py` | Varsayılan: anahtar/builtin/dispatch/deklarasyon kaydı; kabul hücreleri UNMEASURED. `--tools`: betik kaynaklarını okuyup bu rehberin aşağıdaki dökümünü ve `tools.json` dosyasını yeniler. `--output`, `--guide` ile yer seçilir. |
| `06_Clean_Release_Runner_Products.ps1` | Eski ürün modu: release_runner alanını bütünüyle kaldırma (`-Force`); bu turun temizliği bu modu kullanmaz. `-Root . -Binaries`: ikili envanteri; `-Binaries -Force`: hash ile aynı gereksiz kopyaları kaldırır, benzersizleri doğru build klasörüne taşır. `-Keep` açık koruma listesidir; verilirse varsayılan listeyi değiştirir, gerekli runtime/host yollarını da listeye katın. Çalışan/yeni/korunan compiler ve DLL dosyaları korunur. Önce envanter incelenir. |
| `tools/maintenance/archive_freebasic_c_output.py` | Kaynak ağacındaki generated `main.c` veya büyük C çıktısını `build/generated/freebasic_c` altına taşır. `--root .` önizlemedir, `--apply` uygular; hashli manifest bırakır. Elle yazılmış C'yi genel temizlik diye silmez. |
| `tools/maintenance/uxb_dead_code_scan.py` | Tohum dosyadan başlayıp yalnız ölü koda bağlı dosyaları sembol düzeyinde çağrı grafiğiyle bulur (dosyaya yazmaz): `--seed src/backend/backend_pipeline.fbs` (tekrarlanır), `--root`, `--src`, `--also tests compiler tools`, `--skip PARÇA` (arşiv yama klasörleri), `--json YOL`. Rapor: ölü küme, canlı kalanlar ve nedenleri, include edenler, dolaylı include tehlikesi, include SIRASI uyarısı, betik adları. Çıkış 1 = ölü kümenin bir adı canlı kodda kullanılıyor. Ad temellidir (makro ile üretilen ad bulunamaz) ve `#include once` ilk yüklenme konumunu değiştirebilir: taşımadan sonra derleme ve tam regresyonla doğrulayın (S-688'de `backend_step6` kaldırılınca WASM/JS/x64 dosyaları bu yüzden bir kez kırıldı). |
| `tools/claude/uxb_build.ps1` | Claude adayı için mevcut FreeBASIC koşucusu: `-Name <ad> [-SourceRoot <dondurulmuş-kök>]`. Ana compiler adı korunur; eski snapshot yerleşimi için fallback vardır. Yeni kaynak wrapper yolu `src/wrappers` olur. |
| `tools/claude/uxb_run3.ps1` | `-File <tests/...uxb> [-Uxb <compiler>] [-Legacy] [-NativeRepeat N] [-Workers N]`: AST/MIR ve gerçek native çıktılarını yan yana verir; geçici native çıktıyı kaldırır. Bu çıktı tam test kabulünün yerine geçmez. |
| `tools/claude/uxb_regression.ps1` | `-Uxb <compiler> [-Only paket1,paket2]`: mevcut model paketlerini çağırır; başarısız kontroller ve özet yazar. |
| `tests/run_all_model_tests.ps1` | Kayıtlı paketleri çağırır: `-Uxb`, `-Only`, `-Cases`, `-ReportPath`; Only paketleri, Cases paketin mevcut vaka filtresini seçer. `-Only uxgsl -Cases full_abi` örneğinde dört motor sınanır. Native terminalde virgülle liste kabul edilir. Filtresi olmayan pakete Cases vermek veya bilinmeyen paket açık hatadır. Varsayılan geçici çıktı temizliği; `-KeepBuildFolders` yalnız özel tanı içindir. |
| `tests/turkce_ad/run_tests.py` | Altı motorun ortak program koşucusu: `--uxb`, `--test-root`, `--output`, `--only`, `--engines`, `--jobs 1..8`, `--resume`, `--resume-sha256`, `--native-runtime-dir`, `--temp-builds` (varsayılan), `--keep-builds` (geçici seçeneğiyle karşılıklı dışlayan tanı seçeneği). `cases.json` veya expected dosyalarını okur; komut/çıkış/ham sonucu ve binary kimliğini raporda saklar. Bütün çalıştırma çıktıları varsayılan SystemTemp'te silinir; özellikle saklanan tanı çıktıları build/test_outputs altındadır. |
| `tests/compiler_consolidation/run_consolidation_tests.py` | Gerçek program/native callback kabulü: `--compiler`, zorunlu `--report`, `--runtime-dir`, `--only`, `--engines`, varsayılan `--temp-builds` veya açık `--keep-builds`. İkinci seçenek yalnız build/test_outputs kullanır. Callback probe DLL'si geçici modda temizlenir; rendered UXB test kaynakları tests/compiler_consolidation/generated altında korunur. JSON kanıtında kaynak/runner/compiler/probe hashleri ve çıktı yolları bulunur. |
| `tests/cli_flags/run_cli_flag_tests.ps1` | `-Uxb`, `-TestRoot`, `-OnlyResponse`: CLI fiilleri, bütçeler ve `.uxcli` çağrılarını gerçek süreçlerde sınar. Yalnız kendi oluşturduğu zaman aşımına uğrayan çocuğu sonlandırır. |
| `tests/task_provider_completion/run_native_proofs.py` | `--uxb`, `--output`, `--repeat`: iki native yolda gerçek OS işçisi, örtüşme ve çalışan görevin iptalini ölçer; yalnız JOIN çıktısına bakmaz. |
| `tools/kitap/kilavuz_v2/uret.py` | Mevcut şablon/veri/ölçüm önbelleğinden V2'yi üretir: `--sert`, `--yardim`, `--cikti`. Kitap üretimi program örneklerini yeniden çalıştırmaz. |

Diğer Python/PowerShell/BAT araçlarının gerçek parametre bildirimleri,
rutinleri ve çağırdığı alt dosyalar bu belgenin sonundaki dökümdedir.
Kapsam kökteki betikler ile `tools`, `compiler/scripts` ve `tests` altıdır.
`tool_py`, rapor, dağıtım, RAG ve eski paket kopyaları aktif araç yerine
sayılmaz; bunlardan bir araç gerektiğinde önce canlı eşinin olup olmadığı
doğrulanır. Eski pathfix paketini yeniden kurmak yeni src yerleşimini bozabilir.
Bir seçeneği bilmeden yeni koşucu yazmak yerine burada dosya adı veya
işlev anahtar sözcüğü ara, sonra ilgili kaynağı aç. Dinamik aktarılan
`%*` veya `sys.argv` seçeneğinin anlamı çağrılan araçtan okunur.

## 0.3 Güncel doğrulama ve açık kapsam — 29 Ekim

Güncel kabulün tek makine-okunur kaydı reports/workspace_maintenance/current_acceptance.json,
insan-okunur sonucu aynı klasörde SONUC.md'dir. Önceki adayların sayıları
bu kaydın tarihsel kanıtıdır; güncel çalıştırma gibi toplanmaz. Günlük
başlatıcı ve runtime yolu bu rehberin0. bölümündedir. Genel S-030 açık:
CLASS sahibi/generation, tüm kaynak-slot kilitleri, hata/iptal cleanup,
FFI ömrü ve gerçek JS/WASM worker kabulü tamamlanmadan kapatılmaz.

TUR10–15 uygulanırken eski kümülatif kaynaklar canlı src üzerine kopyalanmadı.
Yeni farklar kontrol edilip birleştirildi; TUR13'ün hazırlama betiği yerine
mevcut tests/turkce_ad/run_tests.py kullanıldı. Paketlerin116 özgün testinin
hash'i korunur. TUR7'nin eksik REDIM AS tipi ayrı _v2.uxb uyarlamasında
düzeltilmiştir; özgün kaynak veya hata beklentisi gevşetilmedi. İki boyutlu
sınır sorgusu legacy hariç beş motorda ölçülür; bu filtre düzeltmesi compiler
onarımı sayılmaz. TUR14 strateji ve TUR15 genel planları topluca yapılmış
ilan edilmez;16. tur kullanıcı tarafından sonraki mesaja bırakılmıştır.

Mevcut koşucuyla örnek:

```powershell
python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/submitted_20261029/package13/tests --output reports/workspace_maintenance/round13_current --jobs 2 --timeout 180
```

Doğrudan JS sözleşmeleri aktif runtime/js/common/ux_runtime_core.js üzerinde
Node ile çalışır. FB I32 testi gerçek ortak yardımcıyı çağırır; bozuk MIR'in
bütün zorunlu kapılarına enjeksiyon veya bütün S-034 kapanışı sayılmaz.
C++ STRING sözleşmesi gerçek DLL'yi ve iki OS işçisini kullanır:

```powershell
$env:PATH = 'C:/msys64/ucrt64/bin;' + $env:PATH
New-Item -ItemType Directory -Force build/test_outputs/round10_15_contracts | Out-Null
& C:/msys64/ucrt64/bin/x86_64-w64-mingw32-g++.exe -std=c++17 -O2 -Wall -Wextra -Werror -pthread tests/submitted_20261029/extra/string_runtime_contract.cpp -Lbuild/runtime/codex7 -luxb_runtime -o build/test_outputs/round10_15_contracts/string_runtime_contract.exe
$env:PATH = (Resolve-Path build/runtime/codex7).Path + ';' + $env:PATH
& ./build/test_outputs/round10_15_contracts/string_runtime_contract.exe
```

PATH yalnız bu terminal sürecinde değişir. Sonuç kaydedildikten sonra bu
geçici test EXE'si kaldırılır; kaynak ve log korunur. C++ testi ortak
kaynak-slot kilidi olmadan stale raw pointer kullanma izni vermez.

### Özel compiler DLL paketini düzeltmek — S-685

`build_64.ps1 -OutputPath build/compilers/<ad>/uxb.exe -StageRuntimeOnly`
var olan özel EXE'yi yeniden derlemeden gerekli DLL setini tamamlar.
Varsayılan `-HostLibraries` kökleri uxgsl.dll, uxraylib.dll, uxsdl3.dll ve
uxcapi.dll'dir; uxffi/libffi de zorunludur. Yalnız seçilen DLL'lerin gerçek
PE import bağımlılıkları alınır, eksik dosya açık hatadır; sistem DLL'leri
kopyalanmaz. `compiler_interpreter_runtime.json` dosya/hash listesidir.
`-HostLibraries uxgsl.dll,uxcapi.dll` terminalde virgüllü liste kabul eder.

```powershell
$env:UXB_NATIVE_RUNTIME_DIR = (Resolve-Path build/runtime/codex7).Path
pwsh -NoProfile -ExecutionPolicy Bypass -File build_64.ps1 -OutputPath build/compilers/codex33/uxb.exe -StageRuntimeOnly
pwsh -NoProfile -ExecutionPolicy Bypass -File tests/run_all_model_tests.ps1 -Uxb build/compilers/codex33/uxb.exe -Only uxgsl -Cases full_abi -ReportPath reports/workspace_maintenance/gsl_contract.md
pwsh -NoProfile -ExecutionPolicy Bypass -File tests/compiler_consolidation/run_host_package_contract.ps1 -Uxb build/compilers/codex33/uxb.exe
```

`UXB_NATIVE_RUNTIME_DIR` DLL ile import library'nin birlikte bulunduğu
native runtime klasörüdür; `UXB_RUNTIME_DIR` eşdeğeri değildir. GSL koşucusu
mevcut ortak Python koşucusuna bağlanır: gerçek exit/çıktı ve kimlikler
`test_results/libraries_uxgsl/<koşu>/` altında, geçici EXE/DLL silinir.
Callback yorumlayıcı retleri gerçek callback çalışması sayılmaz; native
iki sağlayıcı gerçekten çalıştırılır. Son sözleşme testi10/10'dur.
Örneklerdeki Bypass yalnız açılan PowerShell sürecine uygulanır; sistemin
genel yürütme ilkesi değiştirilmez. Bu bilgisayarda işaretli UXB-Common.ps1
normal RemoteSigned çağrısında engellendiği için bu açık seçenek kullanıldı.

S-325/S-661–S-663 komut dosyası, S-657/S-658 STRING ve önceki adayların
ayrıntılı ölçümleri SONUC.md ile current_acceptance.json tarihçesinde korunur.
Bu rehberde eski aday yolunu güncel varsayılan gibi kullanmayın. Native DLL
paket sözleşmesi için yukarıdaki mevcut StageRuntimeOnly aracını kullanın;
senkron ret testi gerçek worker kabulünün yerine geçmez.

## 0.3 Verilen28 Ekim yama paketlerinin kabulü

Test kaynakları `tests/submitted_20261028/` altındadır. Özgün ve uyarlanmış hashler `reports/workspace_maintenance/submitted_tests_20261028.json` içinde izlenir. ZIP içindeki eski tam kaynak canlı ağaca kopyalanmaz. DECLARE namespace taslağındaki PRINT, bildirim kabının dışındaki nitelikli ileri çağrıya taşındı; dil davranışı değiştirilmedi. S288 checker kökü src/main.bas işaretiyle bulur.

```powershell
python tests/submitted_20261028/s288/check_registry_coverage.py
python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/submitted_20261028/declare --output reports/workspace_maintenance/declare_current --jobs 1 --timeout 120
python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/submitted_20261028/s288 --output reports/workspace_maintenance/s288_current --jobs 1 --timeout 120
```

Bunlar kullanım örneğidir; kayıtlı compiler20 kabulü DECLARE50/50, eski politika176/176, S28884/84, MemoryRef9/9 ve derlenmiş FreeBASIC yordam12/12. Compiler21 konsol12/12 ve OS36/36 ayrı kimlikle kaydedildi. Son compiler21 geniş kapısı `merged21.md`:7/7 paket,1152/1152. Başlatıcının @ ve doğrudan .uxcli biçimleri gerçek UXCLI_OK ile geçti.148 kendi eski/tekrar çıktısı hash/etkin kullanım kontrolüyle kaldırıldı; son compiler21/runtime5 korunur. Eski örnek/raporlardaki kendi compiler yolları tarihsel olabilir. Örnek komut yazılması yeni koşu kanıtı değildir.

## 0.4 Node/WASM dosya kabulü ve TUR3/TUR4

Okunabilir runtime kaynağı `runtime/wasm/ux_value_runtime.js` doğrudan düzenlenir. Mevcut `python tools/maintenance/uxb_wasm_value_runtime.py` bu tek kaynağı compiler’a gömer; `--check` gömülü kopyanın aynı olduğunu doğrular. Yeni kaynak-yama üreticisi eklenmez.

`tests/turkce_ad/run_tests.py` dosya etkisini de denetler: cases.json `files: {"WASM": {"yol": {"hex":"..."}}, "ALL": {...}}`; `text` UTF-8 tam byte eşitliği, `absent: true` yokluk ister. Expected düzeninde aynı veri `<ad>.files.json` dosyasındadır. Yol izole çalışma alanında kalır; byte/hash/başarı file_checks alanında kaydedilir, geçici ürün sonra kaldırılır.

```powershell
python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/wasm_file_provider --engines WASM --output reports/workspace_maintenance/wasm_file_current --jobs 1
```

`check_browser_host.js runtime.js module.wasm [entry]` gerçek üretilen modülü Node erişimi olmayan browser-benzeri VM’de çalıştırır; eksik dosya yeteneği açık ret ve dosya yokluğu gerektirir. `check_file_cleanup.js run_wasm.js [beklenen_program_exit]` gerçek Node open/close çağrılarını gözler; normal/END/THROW bitişinde bütün gerçek fd’ler kapanmalıdır. Bunlar tests/wasm_file_provider altında odaklı kabul araçlarıdır; yeni genel test koşucusu değildir.

TUR3/TUR4 testleri tests/submitted_20261028/tur3 ve tur4 altında;15 özgün ithal dosyanın hashleri submitted_rounds34_20261028.json içinde. Verilen1000 çağrı kaynağı zaten arşivde olduğundan yeniden kaynak üretilmedi. `sem_stress.uxcli` tekrar kullanılır; ölçüm PowerShell Stopwatch ile üçer gerçek çağrı, semantic_index_perf34.csv. Sonuç yalnız bu yükün compiler21/22 kıyasıdır. TYPE[]/BYREF pending kaynakları geçiyor diye sayılmaz.

S-655 eski negatif WASM hücresi, Mete’nin gerçek sağlayıcı kararıyla pozitif dosya/çıktı kabulüne çevrildi. JS ret beklentisi korundu. Önceki başarısız raporlar tutulur; yalnız hata metni değiştirilerek başarı üretilmedi.

## 1. Derleyiciyi üretme

64 bit Windows derleyicisini üretmek için:

```powershell
.\build_64.bat
```

Bu BAT dosyası sırasıyla FreeBASIC araçlarını bulur, ana FreeBASIC sarmalayıcı
kaynağını derler, 64 bit `uxb.exe` üretir ve sonucu `bin\uxb.exe` konumuna
yerleştirir. Kaynaklar değişmediyse zaman kaybetmemek için
`COMPILER_UP_TO_DATE` yazar.

Mete'nin24 Ekim kararıyla x86/32 bit hedef emeklidir. Eski32 bit build
betikleri güncel kullanım yolu değildir; Claude'un S-666 envanteri ve
aşamalı emeklilik işi bunları izler. AST yorumlayıcı ve AST-x64 motoru kalır.

Mimarinin otomatik seçilmesini istiyorsanız:

```powershell
.\build.bat
```

Canlı ana compiler üzerine yazmadan ayrı aday derlemek için:

```powershell
.\build_64.ps1 -Force -OutputPath build/compilers/codex/uxb.exe
```

`build_64.ps1`: `-Force`, `-Release`, `-Debug`, `-OutputPath` seçenekleri
vardır. `-Release` ve `-Debug` birlikte kullanılmaz. Ara nesne dosyası
compiler çıktısının yanında oluşturulur; source/wrapper içine ikili
kopyalanmaz. Alt PS1 ayrıca `-Root` ve `-SkipX86` kabul eder.

Özel runtime DLL'si üretmek için mevcut aracı kullanın:

```powershell
.\native\uxb_runtime\build_runtime_dll.ps1 -Variant auto `
  -OutputDirectory "$PWD/build/runtime/codex" -SkipPublish
$env:UXB_NATIVE_RUNTIME_DIR = "$PWD/build/runtime/codex"
```

Bu aracın diğer seçenekleri `-Root`, `-Variant auto|std|libuv|tbb|full`;
`-SkipPublish` ana DLL'yi değiştirmeden çalışır. Aynı ada sahip eski DLL
ile yeni compiler ABI'sini karıştırmayın; gerekli bağımlılıklar birlikte
doğrulanmalıdır.

## 2. Bir `.uxb` veya `.bas` programını çalıştırma

AST yorumlayıcısı ile hemen çalıştırma:

```powershell
.\bin\uxb.exe int .\program.uxb --interpreter-backend AST
```

MIR yorumlayıcısı ile çalıştırma:

```powershell
.\bin\uxb.exe int .\program.uxb --interpreter-backend MIR
```

Native 64 bit EXE üretme:

```powershell
.\bin\uxb.exe bld .\program.uxb `
  --x64-mode MIR `
  --build-x64-out .\build\program_x64
```

Üretilen programı çalıştırma:

```powershell
.\build\program_x64\program.exe
```

Bir yol boşluk içeriyorsa çift tırnak kullanın:

```powershell
.\bin\uxb.exe int "C:\Benim Projem\program.bas" --interpreter-backend AST
```

Tüm CLI seçeneklerinin güncel açıklaması:

```powershell
.\bin\uxb.exe --help
```

Varsayılan ileti dili İngilizcedir. Türkçe için:

```powershell
.\bin\uxb.exe int .\program.uxb --message-lang tr
```

## 3. Ana doğrulamalar

Tipli EVENT/PIPE/THREAD/PARALEL testleri:

```powershell
.\tests\typed_task_routines\run_typed_task_tests.ps1 -Uxb .\bin\uxb.exe
```

STRUCT/UNION ve UXCAPI testi:

```powershell
.\tests\struct_union_uxcapi\run_struct_union_uxcapi_smoke.ps1 `
  -Uxb .\bin\uxb.exe
```

MIR Full JSON v2:

```powershell
.\tests\mir_full_json_v2\run_mir_full_json_v2_smoke.ps1 `
  -SkipBuild -Uxb .\bin\uxb.exe
```

Kütüphane kaynak, wrapper ve ABI denetimi:

```powershell
python .\tools\library_tools\uxb_library_source_gate.py --root .
python .\tools\library_tools\uxb_library_abi.py --root .
python .\tools\library_tools\uxb_ecosystem_doctor.py --root . --strict-source
```

UXClazz, `uxclz.dll` ve uxbdll testi:

```powershell
.\RUN_UXCLAZZ_UXBDLL_WINDOWS_TESTS.ps1 -Yes
```

VS Code eklentisi:

```powershell
Set-Location .\vscode-extension
npm ci
npm test
npx @vscode/vsce package --out ..\dist\vscode\uxbasic-workbench-0.3.0.vsix
Set-Location ..
```

## 4. PDSX dönüşümü

```powershell
.\tools\pdsx\uxbasic2pdsxS\run_uxbasic_to_pdsx.ps1 `
  -Source .\program.uxb `
  -Out .\build\program_pdsx
```

Araç önce gerçek `uxb.exe` ile AST JSON üretir, ardından pdsX `.prj` ve `.basx`
dosyalarını hazırlar. Ayrıntılı dönüşüm ve kapsam raporları çıktı klasöründeki
`reports` altında bulunur.

## 5. Sorun olduğunda

- `uxb.exe bulunamadı`: önce `.\build_64.bat` çalıştırın.
- DLL bulunamadı: programı dağıtımın `bin` klasöründen çalıştırın; gereken
  runtime DLL’leri aynı klasörde tutulur.
- Kaynak yolu bulunamadı: tam yolu çift tırnakla verin.
- Ayrıntılı compiler tanılama: `--trace` ve `--debug` seçeneklerini ekleyin.
- Makine tarafından okunabilir tanılama için `--all-diagnostics-json-out`
  seçeneğini kullanın.

Daha geniş CLI öğreticisi için `docs\UXB_EXE_CLI_DERLEME_KITABI_TR.md`,
kütüphane API tabloları için `docs\UXB_DLL_WRAPPER_API_ENVANTERI_20260729.md`
dosyasına bakın.

## 0.5 TUR5–9 ve ilk yama paketi kabulü

Mevcut tests/turkce_ad/run_tests.py, TUR5…TUR9 ile patch1 ve abi_extended klasörlerindeki cases.json dosyalarını okur. Örnek: `python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/submitted_20261028/patch1 --output reports/workspace_maintenance/patch1_current --jobs 1 --timeout 180`. --only var olan test adlarını seçer; --engines hedefleri daraltır. Testin motor alt kümesi bütün motorların geçtiği iddiası değildir. Negatif hücre için hem süreç hatası hem doğru tanı gerekir.

Özgün ZIP test kopyaları submitted_round5_20261028.json ve submitted_round6_9_20261028.json ile hashlenir. TUR7 REDIM örneğinde eksik AS I32, ayrı s097_param_dynamic_v2 kaynağında düzeltilmiştir; özgün kaynak ve başarısız26 ölçümü korunur. STATIC array web sağlayıcısı eski24’te de LOCK_ENTER hatası verir; ayrı static_web_before24/static_scope29 raporları bu açık S-245/S-346 kapsamını gerçek olumlu testle gösterir. Bu beklenti geçti diye değiştirilmez.

S-111 iki argümanlı boyut sorgusu iş yükü, dilin mevcut %%FOR/%%ENDFOR önişlemcisiyle test kaynağında açılır: tests/submitted_20261028/tur9/s111_dimension_index_benchmark.uxb. Aynı sem_dimension_benchmark.uxcli dosyasıyla iki adayın SEM süresi Stopwatch ile ölçülebilir. Derleyici/iş yükü kimliği, çıkış ve ham stdout birlikte saklanır; adaylar sırayla ve diğer ağır testler bitince ölçülür. Yeni kaynak yazdıran haricî üretici yoktur.


Konum paketi: `python tests/turkce_ad/run_tests.py --uxb build/compilers/codex33/uxb.exe --native-runtime-dir build/runtime/codex7 --test-root tests/console_cursor --output reports/workspace_maintenance/cursor_current --jobs 2 --timeout 180`. Aynı runner ham byte çıktıyı yakalar; yalnız platform CRLF satır sonunu ham karşılaştırmada normalleştirir, tek CR/TAB/BS/NUL korunur. console_cursor merkezi model listesine mevcut print_zones koşucusu yeniden kullanılarak eklendi: `tests/run_all_model_tests.ps1 -Uxb build/compilers/codex33/uxb.exe -Only console_cursor`. -Cases mevcut test adlarını seçer. Paylaşılan PRINT koşucusu artık -TestRoot ve -Only alır; yeni runner yazılmadı. Native runtime6 için süreçte UXB_NATIVE_RUNTIME_DIR ayarlanır; varsayılan günlük başlatıcı doğrulanmış31/runtime6 kullanır.

Derleme alt süreci yerel UXB-Common.ps1 imzası nedeniyle staging aşamasında engellenirse sistem politikasını değiştirmeden yalnız o süreç için `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build_64.ps1 -StageRuntimeOnly -OutputPath build/compilers/<aday>/uxb.exe` kullanılır. Tam derleme de aynı süreç seçeneğiyle mevcut build_64.ps1 üzerinden yapılabilir. Native API ekleri için mevcut native/uxb_runtime/build_runtime_dll.ps1 -Variant auto -OutputDirectory build/runtime/<aday> -SkipPublish kullanılır; çalışma DLL ve derleyici birlikte doğrulanır.

<!-- UXB_TOOL_CATALOG_BEGIN -->
## Kaynaktan çıkarılan betik ve CLI dökümü

582 betiğin tam içeriği okunarak Python/PowerShell sözdiziminden çıkarıldı. Bu döküm çalıştırma başarısı değildir. Ayrıntılı kaynak kimlikleri: `reports/acceptance_inventory/tools.json`.

Python satırlarında seçenek adları, varsayılanlar, zorunluluk ve choices kaynak ifadeleriyle; PowerShell satırlarında gerçek parametre bildirimleriyle gösterilir. BAT/CMD `%*` seçenekleri çağırdığı araca iletir. Dinamik seçenekler ve alt araçlar ayrıca okunmalıdır.

### `00_Create_Sample_Sources.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\tools\release_runners\ps1\03_Run_Triple_Pipeline_One.ps1, UXB-Common.ps1.

### `01_Build_X64_Exe_One.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Source
[string]$Root = ""
[string]$UxbExe = ""
[string]$OutRoot = ""
[ValidateSet("AST","MIR","BOTH")][string]$X64Mode = "AST"
[switch]$RunExe
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: UXB-Common.ps1, program.exe.

### `02_Build_Web_WAT_WASM_JS_One.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Source
[string]$Root = ""
[string]$UxbExe = ""
[string]$OutRoot = ""
[string]$Wat2Wasm = ""
[switch]$RequireWasm
[switch]$OpenBrowser
[int]$Port = 8765
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: UXB-Common.ps1, wat2wasm.exe.

### `03_Run_Triple_Pipeline_One.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Source
[string]$Root = ""
[string]$UxbExe = ""
[string]$OutRoot = ""
[string]$Wat2Wasm = ""
[ValidateSet("AST","MIR","BOTH")][string]$X64Mode = "AST"
[switch]$RunExe
[switch]$OpenBrowser
[int]$Port = 8765
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: 01_Build_X64_Exe_One.ps1, 02_Build_Web_WAT_WASM_JS_One.ps1, UXB-Common.ps1, x64_build\program.exe.

### `04_Run_Triple_Pipeline_XTestX.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[string]$UxbExe = ""
[string]$TestsRoot = "xtestx"
[string]$Pattern = "*.uxb"
[int]$Limit = 0
[string]$OutRoot = ""
[string]$Wat2Wasm = ""
[ValidateSet("AST","MIR","BOTH")][string]$X64Mode = "AST"
[switch]$RunExe
[switch]$OpenFirstBrowserOnly
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: 03_Run_Triple_Pipeline_One.ps1, UXB-Common.ps1.

### `05_Open_Browser_Result.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$WebDir
[int]$Port = 8765
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `06_Clean_Release_Runner_Products.ps1`

This mode never recursively removes folders or touches source/documents. Exact content duplicates can be removed; unique historical binaries are retained under build/, rather than silently treating uniqueness as waste.

```text
[string]$Root = ""
[switch]$Force
[switch]$Binaries
[string[]]$Keep = @('reports/s030_assign_20261022/runtime7', 'bin/uxb_x86.exe', 'bin/uxb_codex1_oop.exe', 'bin/uxb_codex2_operators.exe')
```
Rutinler: Assert-BinaryPath, Get-BinaryHash.
Çağrı/yol başvuruları: UXB-Common.ps1, bin/uxb_codex1_oop.exe, bin/uxb_codex2_operators.exe, bin/uxb_x86.exe, uxb.exe.

### `APPLY_UXCLAZZ_UXBDLL_PATCH.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$false)]
    [string]$TargetRoot = "."
[switch]$Force
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\tools\tests\verify_uxclazz_uxbdll_patch.py.

### `ARCHIVE_FREEBASIC_C_SOURCES.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \tools\archive_freebasic_c_sources.ps1, powershell.exe.

### `build.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build.bat, dpn1.exe.

### `build_64.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_64.bat, dp0tools\FreeBASIC-1.10.1-win64\fbc.exe, dpn1_64.exe, tools\setup_win64_toolchain.bat.

### `build_64.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$Force
[switch]$Release
[switch]$Debug
[string]$OutputPath=''
[switch]$StageRuntimeOnly
[string[]]$HostLibraries=@('uxgsl.dll','uxraylib.dll','uxsdl3.dll','uxcapi.dll')
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: PSScriptRoot/compiler/scripts/build_uxb_main_64.ps1.

### `build_64_fixed_lower.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \uxb.exe, fbc.exe.

### `build_64_fixed_upper.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \uxb.exe, fbc.exe.

### `build_cbase_libraries.ps1`

Batch/terminal çağrılarında -Modules uxsqlite,uxjson biçimini de kabul et.

```text
[string]$Root = "."
[switch]$InstallDeps
[switch]$FetchDeps
[switch]$Clean
[switch]$RunTests
[string[]]$Modules = @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )
```
Rutinler: Resolve-Tool, Ensure-Directory, Get-PkgFlags, Invoke-GccBuild, Test-Pe64, Get-ImportedDlls, Test-IsSystemDll, Copy-DependenciesRecursive, Fetch-Yyjson.
Çağrı/yol başvuruları: bin\uxb.exe, gcc.exe, objdump.exe, pkg-config.exe, pkgconf.exe, tar.exe, usr\bin\pacman.exe, x86_64-w64-mingw32-gcc.exe, x86_64-w64-mingw32-objdump.exe.

### `build_compiler_64.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, compiler\scripts\build_uxb_main_64.bat, uxb_main_wrapper_64.exe.

### `build_freebasic_a_group.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root="."
[switch]$Clean
[switch]$SkipTests
[string[]]$Modules=@("uxsystem","uxfs","uxpath","uxprocess","uxlog","uxconfig","uxdatetime","uxuuid")
```
Rutinler: Resolve-Fbc.
Çağrı/yol başvuruları: \FreeBASIC\fbc.exe, \FreeBASIC\fbc64.exe, bin\uxb.exe, tools\FreeBASIC-1.10.1-win64\fbc.exe, tools\FreeBASIC-1.10.1-win64\fbc64.exe.

### `build_libraries.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\build_libraries.bat.

### `build_libraries.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet('minimal','core','all')][string]$Set='core'
[string[]]$Library=@()
[switch]$FetchDeps
[switch]$Clean
[switch]$StrictAll
[switch]$StrictRuntime
[switch]$BuildCompiler
[switch]$AuditOnly
[switch]$DeployOnly
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: PSScriptRoot/compiler/scripts/build_libraries.ps1.

### `build_matrix.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_matrix.bat, dp0build_32.bat, dp0build_64.bat.

### `BUILD_UXB_C_FULL_API.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\build_c_full_api.ps1, powershell.exe, pwsh.exe.

### `BUILD_UXB_CBASE_LIBRARIES.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\build_cbase_libraries.ps1, powershell.exe.

### `BUILD_UXB_FREEBASIC_A_GROUP.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\build_freebasic_a_group.ps1, powershell.exe.

### `BUILD_UXB_LIBRARY_SYSTEM.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0BUILD_UXB_LIBRARY_SYSTEM.ps1, powershell.exe.

### `BUILD_UXB_LIBRARY_SYSTEM.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet('core','all')][string]$Set='core'
[switch]$SkipDependencyInstall
[switch]$SkipCompilerBuild
[switch]$SkipSmoke
[switch]$RequireMirX64
[switch]$StrictAll
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: PSScriptRoot/compiler/scripts/build_uxb_library_system.ps1.

### `Collect_UXB_Debug.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$RunBuildAndTests
[switch]$IncludeFullSrc
[switch]$IncludeCBackendProbe
[ValidateSet("Ask","Yes","No")]
    [string]$RebuildCompiler = "Ask"
```
Rutinler: Write-Log, Copy-ItemSafe, Run-CmdLog, Ask-YesNo.
Çağrı/yol başvuruları: .\Collect_UXB_Debug.ps1, .\bin\uxb.exe, .\build_64.bat, .\compiler\scripts\build_libraries.ps1, .\compiler\scripts\build_uxb_main_64.ps1, .\compiler\scripts\run_library_abi10_smoke.ps1, .\tests\libraries\abi10\build_abi10_test_dll.bat, .\tests\libraries\abi10\build_abi10_test_dll.ps1, .\tools\FreeBASIC-1.10.1-win64\fbc.exe, .\tools\FreeBASIC-1.10.1-win64\fbc64.exe, Collect_UXB_Debug.ps1, \msys64\ucrt64\bin\objdump.exe, bin\uxb.exe, build_64.bat, fbc.exe, fbc64.exe, powershell.exe, where.exe.

### `Collect_UXB_Debug_Ask_Rebuild.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$RunBuildAndTests
[switch]$IncludeFullSrc
[switch]$IncludeCBackendProbe
[ValidateSet("Ask","Yes","No")]
    [string]$RebuildCompiler = "Ask"
```
Rutinler: Write-Log, Copy-ItemSafe, Run-CmdLog, Ask-YesNo.
Çağrı/yol başvuruları: .\Collect_UXB_Debug.ps1, .\bin\uxb.exe, .\build_64.bat, .\compiler\scripts\build_libraries.ps1, .\compiler\scripts\build_uxb_main_64.ps1, .\compiler\scripts\run_library_abi10_smoke.ps1, .\tests\libraries\abi10\build_abi10_test_dll.bat, .\tests\libraries\abi10\build_abi10_test_dll.ps1, .\tools\FreeBASIC-1.10.1-win64\fbc.exe, .\tools\FreeBASIC-1.10.1-win64\fbc64.exe, Collect_UXB_Debug.ps1, \msys64\ucrt64\bin\objdump.exe, bin\uxb.exe, build_64.bat, fbc.exe, fbc64.exe, powershell.exe, where.exe.

### `compiler/scripts/apply_adim43_src30_05_5_fixes.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[string]$RepoRoot = "."
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: apply_adim43_src30_05_5_fixes.py, src\tools\control\apply_adim43_src30_05_5_fixes.py, tools\control\apply_adim43_src30_05_5_fixes.py.

### `compiler/scripts/apply_adim44_remaining_gaps.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[string]$RepoRoot = "."
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: apply_adim44_remaining_gaps.py, tools\control\apply_adim44_remaining_gaps.py.

### `compiler/scripts/audit_uxb_library_bundle.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--zip-dir
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_library_importer.py.

### `compiler/scripts/build_all_runtime_ext_dlls.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_libraries.bat.

### `compiler/scripts/build_c_full_api.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$InstallDeps
[switch]$Clean
[switch]$RunTests
[ValidateSet("stable", "experimental")]
    [string]$Profile = "stable"
[string[]]$Modules = @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )
```
Rutinler: Resolve-Root, Ensure-Directory, Resolve-Tool, Invoke-Logged, Get-PkgTokens, Find-VendorDll, Get-ImportedDlls, Test-SystemDll, Copy-DependencyClosure, Assert-Pe64, Build-InlineShim.
Çağrı/yol başvuruları: ../../UXB-Common.ps1, bin\uxb.exe, clang.exe, cmd.exe, gcc.exe, objdump.exe, pkg-config.exe, pkgconf.exe, runtime_ext\uxcapi\build_uxcapi_dll.bat, tools\library_tools\uxb_c_full_bindgen.py, usr\bin\pacman.exe, uxb.exe, x86_64-w64-mingw32-gcc.exe, x86_64-w64-mingw32-objdump.exe.

### `compiler/scripts/build_c_full_api_group.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_c_full_api.ps1, powershell.exe, pwsh.exe.

### `compiler/scripts/build_cbase_libraries.ps1`

Batch/terminal çağrılarında -Modules uxsqlite,uxjson biçimini de kabul et.

```text
[string]$Root = "."
[switch]$InstallDeps
[switch]$FetchDeps
[switch]$Clean
[switch]$RunTests
[string[]]$Modules = @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )
```
Rutinler: Resolve-Tool, Ensure-Directory, Get-PkgFlags, Invoke-GccBuild, Test-Pe64, Get-ImportedDlls, Test-IsSystemDll, Copy-DependenciesRecursive, Fetch-Yyjson.
Çağrı/yol başvuruları: ../../UXB-Common.ps1, bin\uxb.exe, gcc.exe, objdump.exe, pkg-config.exe, pkgconf.exe, tar.exe, usr\bin\pacman.exe, x86_64-w64-mingw32-gcc.exe, x86_64-w64-mingw32-objdump.exe.

### `compiler/scripts/build_freebasic_a_group.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_freebasic_a_group.ps1, powershell.exe, pwsh.exe.

### `compiler/scripts/build_freebasic_a_group.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root="."
[switch]$Clean
[switch]$SkipTests
[string[]]$Modules=@("uxsystem","uxfs","uxpath","uxprocess","uxlog","uxconfig","uxdatetime","uxuuid")
```
Rutinler: Resolve-Fbc, Invoke-UxbTest.
Çağrı/yol başvuruları: \FreeBASIC\fbc.exe, \FreeBASIC\fbc64.exe, bin\uxb.exe, tools\FreeBASIC-1.10.1-win64\fbc.exe, tools\FreeBASIC-1.10.1-win64\fbc64.exe.

### `compiler/scripts/build_imported_library_runtimes.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_library_runtime_builder.py.

### `compiler/scripts/build_libraries.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_libraries.ps1.

### `compiler/scripts/build_libraries.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet("minimal","core","all")][string]$Set = "core"
[string[]]$Library = @()
[switch]$FetchDeps
[switch]$Clean
[switch]$StrictAll
[switch]$StrictRuntime
[switch]$BuildCompiler
[switch]$AuditOnly
[switch]$DeployOnly
[string]$Root = ""
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: tools\library_tools\uxb_library_build.py.

### `compiler/scripts/build_uxb_64_and_libraries.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet("minimal","core","all")][string]$Set = "core"
[switch]$FetchDeps
[switch]$StrictAll
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: PSScriptRoot\build_libraries.ps1.

### `compiler/scripts/build_uxb_library_system.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet("core","all")][string]$Set = "core"
[switch]$SkipDependencyInstall
[switch]$SkipCompilerBuild
[switch]$SkipSmoke
[switch]$RequireMirX64
[switch]$StrictAll
[string]$Root = ""
```
Rutinler: Find-UxbRoot, Invoke-UxbChildScript.
Çağrı/yol başvuruları: build_libraries.ps1, library_doctor.ps1, organize_library_layout.ps1, powershell.exe, resolve_uxb_toolchain.ps1, run_library_abi10_smoke.ps1.

### `compiler/scripts/build_uxb_main_64.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_uxb_main_64.ps1, powershell.exe.

### `compiler/scripts/build_uxb_main_64.ps1`

YAMA: host compiler build is x64-only by default. Set UXB_BUILD_X86=1 to opt in.

```text
[string]$Root = ''
[switch]$Force
[switch]$Release
[switch]$Debug
[switch]$SkipX86
[string]$OutputPath = ''
[switch]$StageRuntimeOnly
[string[]]$HostLibraries = @('uxgsl.dll','uxraylib.dll','uxsdl3.dll','uxcapi.dll')
```
Rutinler: Resolve-UxbRoot, Get-PeMachine, Invoke-FbcBuild, Copy-InterpreterBridge.
Çağrı/yol başvuruları: /msys64/ucrt64/bin/objdump.exe, Files/CodeBlocks/MinGW/bin/objdump.exe, UXB-Common.ps1, bin/uxb_x86.exe, bin/win64/objdump.exe, bin\uxb.exe, fbc32.exe, fbc64.exe, objdump.exe, uxb.exe, uxb_x64.new.exe, uxb_x86.exe, uxb_x86.new.exe.

### `compiler/scripts/build_uxjsruntime.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
[switch]$SkipFetch
[switch]$SkipBuild
[switch]$SkipNativeSmoke
[switch]$RunUxbSmoke
```
Rutinler: Invoke-NativeChecked.
Çağrı/yol başvuruları: bin\uxb.exe, build_uxjsrt.ps1, fetch_quickjs.ps1, python.exe, tests\libraries\uxjsruntime\test_uxjsrt.py.

### `compiler/scripts/collect_latest_review_from_history.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoCurrent
[string]$OutPrefix = "latest_review"
```
Rutinler: Find-UxbRoot, Read-GateSummary, Pick-LatestByName.
Çağrı/yol başvuruları: yok.

### `compiler/scripts/create_step7_release_candidate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_workspace_clean_guard.bat, uxb\tools\uxb_final_gap_audit.py, uxb\tools\uxb_final_merge.py, uxb\tools\uxb_ide_command_contract.py, uxb\tools\uxb_vscode_contract_audit.py.

### `compiler/scripts/create_wasm_publish_release.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `compiler/scripts/fetch_wabt.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[string]$Version = "1.0.41"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tar.exe, wat2wasm.exe.

### `compiler/scripts/import_uxb_library_bundle.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--apply
--conflict
--zip-dir
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_library_ide_contract_extend.py, uxb\tools\uxb_library_importer.py.

### `compiler/scripts/library_doctor.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Root\compiler\scripts\resolve_uxb_toolchain.ps1, Root\tools\library_tools\uxb_library_abi.py, Root\tools\library_tools\uxb_library_export_audit.py, Root\tools\library_tools\uxb_library_layout_doctor.py, bin\uxb.exe, powershell.exe.

### `compiler/scripts/open_latest_reports.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `compiler/scripts/organize_library_layout.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[switch]$RemoveSourceProducts
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Root\tools\library_tools\uxb_library_build.py, Root\tools\library_tools\uxb_library_layout_doctor.py.

### `compiler/scripts/resolve_uxb_toolchain.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[switch]$RequireCompiler
[switch]$RequireNative
[switch]$RequireWabt
```
Rutinler: Resolve-UxbRoot, First-ExistingFile, Command-Path.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \msys64\ucrt64\bin\pkg-config.exe, \msys64\ucrt64\bin\pkgconf.exe, \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, \msys64\usr\bin\pacman.exe, fbc.exe, fbc64.exe, gcc.exe, pkg-config.exe, pkgconf.exe, py.exe, python.exe, tools\wabt\bin\wat2wasm.exe, wat2wasm.exe, x86_64-w64-mingw32-gcc.exe.

### `compiler/scripts/rotate_current_reports.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$StepName = "run"
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: yok.

### `compiler/scripts/run_adim04_ast_contract_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, compiler\scripts\build_uxb_main_64.bat, compiler\scripts\run_step2_ast_contract_gate.bat, reports\control\current\adim04_ast_contract_negative_harness.exe, tools\FreeBASIC-1.10.1-win64\fbc.exe, uxb_main_64.exe.

### `compiler/scripts/run_adim07_lexer_preprocessor.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
[string]$PythonExe = "python"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools/control/uxb_surface_lifecycle_matrix.py.

### `compiler/scripts/run_adim08_parser_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
[string]$Python = "python"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dist/uxb_main_64.exe, uxb_main_64.exe.

### `compiler/scripts/run_adim10_semantic_step5_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
[string]$Python = "python"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, compiler/scripts/run_adim10_semantic_step5_gate.ps1, compiler/scripts/run_step3_semantic_type_layout_gate.bat, compiler\scripts\build_uxb_main_64.ps1, compiler\scripts\run_step3_semantic_type_layout_gate.bat.

### `compiler/scripts/run_adim11_mir_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$RepoRoot = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, build\uxb_main_64.exe, compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim12_runtime_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$RepoRoot = ""
[string]$PythonExe = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_uxb_main_64.bat, compiler/scripts/build_uxb_main_64.bat, compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim13_backend_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
```
Rutinler: Run-Test.
Çağrı/yol başvuruları: bin/uxb.exe, build/uxb_main_64.exe, compiler/scripts/build_uxb_main_64.bat.

### `compiler/scripts/run_adim14_backend_web_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair = $true
[string]$Python = ""
[string]$RepoRoot = ""
```
Rutinler: Write-TextFile, JsonEscape, Add-ExpectedActual, Add-ErrorRow.
Çağrı/yol başvuruları: bin/uxb.exe, build/uxb_main_64.exe, build_64.bat, compiler/scripts/build_uxb_main_64.bat, dist/uxb_main_64.exe, tools/wabt/bin/wat2wasm.exe, uxb_main_64.exe.

### `compiler/scripts/run_adim15_ffi_library_import_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair = $true
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_64.bat, compiler/scripts/build_uxb_main_64.bat, compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim16_diagnostics_source_mapping_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Add-ErrClass.
Çağrı/yol başvuruları: ../tools/FreeBASIC-1.10.1-win64/fbc.exe, /FreeBASIC/fbc.exe, tests/adim16/harness/adim16_common_harness.exe, tests/adim16/harness/adim16_negative_empty_code.exe, tests/adim16/harness/adim16_negative_missing_location.exe, tools/FreeBASIC-1.10.1-win64/fbc.exe.

### `compiler/scripts/run_adim17_cli_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Add-Err, Run-Positive, Run-Negative.
Çağrı/yol başvuruları: bin/uxb.exe, bin\uxb.exe.

### `compiler/scripts/run_adim18_test_suite_release_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[int]$MaxTests = 0
[switch]$AllowSkips
[switch]$RequireBackendOutputs
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: .venv\Scripts\python.exe, build_64.bat, compiler/scripts/build_64.bat, compiler/scripts/build_uxb_main_64.bat, tools/control/uxb_expected_actual_compare.py, tools/control/uxb_run_layer_tests.py, tools/control/uxb_surface_test_generator.py, tools/release/uxb_release_gate.py.

### `compiler/scripts/run_adim19_20_21_contract_gates.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$NoRepair
[switch]$Strict
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\.venv\Scripts\python.exe, tools/control/uxb_copilot_task_boundary_gate.py, tools/control/uxb_layer_output_contract_gate.py, tools/control/uxb_surface_route_matrix_contract_gate.py.

### `compiler/scripts/run_adim19_surface_route_matrix_contract_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\.venv\Scripts\python.exe, tools/control/uxb_surface_route_matrix_contract_gate.py.

### `compiler/scripts/run_adim20_layer_output_contract_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\.venv\Scripts\python.exe, tools/control/uxb_layer_output_contract_gate.py.

### `compiler/scripts/run_adim21_copilot_task_boundary_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[string]$TaskDoc = ""
[string]$Step = ""
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\.venv\Scripts\python.exe, tools/control/uxb_copilot_task_boundary_gate.py.

### `compiler/scripts/run_adim22_full_layer_expected_suite.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[int]$MaxTests = 0
[string]$UxbExe = ""
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: .venv\Scripts\python.exe, build_64.bat, compiler/scripts/build_64.bat, compiler/scripts/build_uxb_main_64.bat, tools/control/uxb_expected_actual_compare.py, tools/control/uxb_run_layer_tests.py.

### `compiler/scripts/run_adim23_lifecycle_web_output_binding_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Resolve-RepoRoot.
Çağrı/yol başvuruları: build_64.bat.

### `compiler/scripts/run_adim24_js_source_emit_fix_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb/compiler/scripts/run_adim23_lifecycle_web_output_binding_gate.ps1.

### `compiler/scripts/run_adim25_26_27_close_gates.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_64.bat.

### `compiler/scripts/run_adim28_build_test_pipeline.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_64.bat, compiler/scripts/build_uxb_main_64.bat, uxb/compiler/scripts/build_uxb_main_64.bat, uxb/compiler/scripts/run_adim22_full_layer_expected_suite.ps1, uxb/compiler/scripts/run_adim25_26_27_close_gates.ps1, uxb\compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim28_runtime_dll_doctor.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: fbc.exe, tools/FreeBASIC-1.10.1-win64/fbc.exe.

### `compiler/scripts/run_adim29_all_runtime_ext_dll_doctor.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[switch]$Build
[switch]$StrictAll
```
Rutinler: Find-RepoRoot, CsvEscape.
Çağrı/yol başvuruları: uxb/runtime_ext/bigfp/build_bigfp_dll.bat, uxb/runtime_ext/fp128/build_fp128_dll.bat, uxb/runtime_ext/fp80/build_fp80_dll.bat, uxb/runtime_ext/uxaimath/build_uxaimath_dll.bat, uxb/runtime_ext/uxaimath/build_uxaimath_fallback_dll.bat, uxb/runtime_ext/uxcollections/build_uxcollections_dll.bat, uxb/runtime_ext/uxdataframe/build_uxdataframe_dll.bat, uxb/runtime_ext/uxdataset/build_uxdataset_dll.bat, uxb/runtime_ext/uxgraph/build_uxgraph_dll.bat, uxb/runtime_ext/uxgraph/build_uxgraph_fallback_dll.bat, uxb/runtime_ext/uxllama/build_uxllama_dll.bat, uxb/runtime_ext/uxmath/build_uxmath_dll.bat, uxb/runtime_ext/uxmathcore/build_uxmathcore_dll.bat, uxb/runtime_ext/uxmatrix/build_uxmatrix_dll.bat, uxb/runtime_ext/uxmatrix/build_uxmatrix_fallback_dll.bat, uxb/runtime_ext/uxnn/build_uxnn_dll.bat, uxb/runtime_ext/uxnn/build_uxnn_fallback_dll.bat, uxb/runtime_ext/uxnn2/build_uxnn2_dll.bat, uxb/runtime_ext/uxnn3/build_uxnn3_dll.bat, uxb/runtime_ext/uxonnx/build_uxonnx_dll.bat, uxb/runtime_ext/uxonnx2/build_uxonnx2_dll.bat, uxb/runtime_ext/uxstats/build_uxstats_dll.bat, uxb/runtime_ext/uxstats2/build_uxstats2_dll.bat, uxb/runtime_ext/uxtensor/build_uxtensor_dll.bat, uxb/runtime_ext/uxtensor/build_uxtensor_fallback_dll.bat.

### `compiler/scripts/run_adim2_differential_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_adim2_toolchain_gate.bat, uxb\tools\uxb_cli_pipeline_gate.py, uxb\tools\uxb_differential_runner.py.

### `compiler/scripts/run_adim2_toolchain_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_toolchain_doctor.py.

### `compiler/scripts/run_adim30_10step_chain_suite.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[int]$MaxTests = 0
[string]$UxbExe = ""
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: .venv\Scripts\python.exe, build_64.bat, compiler/scripts/build_uxb_main_64.bat, tools/control/uxb_10step_chain_runner.py.

### `compiler/scripts/run_adim31_after_patch_check.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: compiler\scripts\run_adim30_10step_chain_suite.ps1.

### `compiler/scripts/run_adim31b_canonical_check.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: compiler/scripts/run_adim30_10step_chain_suite.ps1.

### `compiler/scripts/run_adim32_force_rebuild_adim30.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: build_64.bat, compiler\scripts\build_uxb_main_64.bat, compiler\scripts\run_adim30_10step_chain_suite.ps1.

### `compiler/scripts/run_adim32b_strict_pass.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: .venv\Scripts\python.exe, bin/uxb.exe, compiler\scripts\build_uxb_main_64.bat, compiler\scripts\rotate_current_reports.ps1, tools/control/uxb_adim32b_strict_runner.py.

### `compiler/scripts/run_adim33_prelexer_meta_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: yok.

### `compiler/scripts/run_adim34_extended_meta_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: build_64.bat, compiler/scripts/build_uxb_main_64.bat, compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim35_big_number_suite.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: bin\uxb.exe, build_64.bat, compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_adim36_full_surface_library_suite.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[int]$MaxTests = 0
[string]$UxbExe = ""
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: .venv\Scripts\python.exe, build_64.bat, compiler\scripts\build_uxb_main_64.bat, compiler\scripts\rotate_current_reports.ps1, tools\control\uxb_adim36_full_surface_runner.py.

### `compiler/scripts/run_adim38_after_second_wave.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: compiler\scripts\rotate_current_reports.ps1, compiler\scripts\run_adim30_10step_chain_suite.ps1, compiler\scripts\run_adim32b_strict_pass.ps1, compiler\scripts\run_adim36_full_surface_library_suite.ps1.

### `compiler/scripts/run_adim40_after_report_driven_fixes.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: compiler\scripts\collect_latest_review_from_history.ps1, compiler\scripts\run_adim30_10step_chain_suite.ps1, compiler\scripts\run_adim32b_strict_pass.ps1, compiler\scripts\run_adim36_full_surface_library_suite.ps1.

### `compiler/scripts/run_adim41_cli_full_contract_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: tools\control\uxb_cli_full_contract_gate.py, uxb_cli_full_contract_gate.py.

### `compiler/scripts/run_adim42_source_driven_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: compiler\scripts\collect_latest_review_from_history.ps1, compiler\scripts\run_adim30_10step_chain_suite.ps1, compiler\scripts\run_adim32b_strict_pass.ps1, compiler\scripts\run_adim36_full_surface_library_suite.ps1.

### `compiler/scripts/run_adim43_src30_05_5_status_scan.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[string]$RepoRoot = "."
```
Rutinler: Find-UxbRoot.
Çağrı/yol başvuruları: scan_adim43_src30_05_5_status.py, src\tools\control\scan_adim43_src30_05_5_status.py, tools\control\scan_adim43_src30_05_5_status.py.

### `compiler/scripts/run_adim44_remaining_status_scan.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
[string]$RepoRoot = "."
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: scan_adim44_remaining_status.py, tools\control\scan_adim44_remaining_status.py.

### `compiler/scripts/run_adim45_error_system_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$NoRepair
```
Rutinler: Find-Root.
Çağrı/yol başvuruları: build_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe.

### `compiler/scripts/run_browser_from_source.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--compiler
--mode
--out-dir
--source
--uxb-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: run_browser_from_source.bat, src\main.exe, src\main_64.exe, tools\uxb_browser_build.py.

### `compiler/scripts/run_browser_hybrid_pro_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--mir-json
--mode
--no-node-check
--out-dir
--uxb-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\uxb_browser_build_pro.py.

### `compiler/scripts/run_browser_hybrid_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--backend-report-json-out
--dummy-import-func
--emit-browser
--emit-js
--emit-wasm
--emit-wat
--html-out
--js-out
--js-runtime-out
--manifest-out
--wasm-out
--wat-out
--wat2wasm
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, tools\wabt\bin\wasm-interp.exe, tools\wabt\bin\wasm-validate.exe, tools\wabt\bin\wat2wasm.exe.

### `compiler/scripts/run_browser_js_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--backend-report-json-out
--emit-browser
--emit-js
--html-out
--js-out
--js-runtime-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe.

### `compiler/scripts/run_browser_json_build.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--mir-json
--mode
--out-dir
--uxb-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: run_browser_json_build.bat, tools\uxb_browser_build.py.

### `compiler/scripts/run_browser_surface_contract.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--keyword-layer-csv
--language-surface-csv
--out-dir
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\uxb_surface_to_browser_contract.py.

### `compiler/scripts/run_browser_toolchain_install.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\install_browser_wasm_toolchain.ps1.

### `compiler/scripts/run_emit_js_transpiler.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--backend
--js-only
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_emit_js_transpiler.bat, uxb\bin\uxb.exe, uxb\tools\uxb_js_transpiler_wasm_backend.py.

### `compiler/scripts/run_emit_mir_x64_asm.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--codegen-source
--emit-x64-nasm
--emit-x64-nasm-out
--enable-mir-x64-experimental
--mir-full-json-out
--mir-verify
--x64-codegen-policy-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_emit_mir_x64_asm.bat, uxb\bin\uxb.exe.

### `compiler/scripts/run_emit_wasm_backend.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--backend
--emit-wasm
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_emit_wasm_backend.bat, uxb\bin\uxb.exe, uxb\tools\uxb_js_transpiler_wasm_backend.py.

### `compiler/scripts/run_emit_x64_ast_asm.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--codegen-source
--emit-x64-nasm
--emit-x64-nasm-out
--x64-codegen-policy-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_emit_x64_ast_asm.bat, uxb\bin\uxb.exe.

### `compiler/scripts/run_extfp_codegen_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--asm
--debug
--emit-x64-nasm
--emit-x64-nasm-out
--enable-extfp-runtime
--extfp-runtime-dir
--family
--json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\compiler\scripts\build_uxb_main_64.bat, uxb\runtime_ext\build_fp_runtime_all.bat, uxb\tools\uxb_extfp_codegen_audit.py.

### `compiler/scripts/run_final_ffi_quickjs_release_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..'))
[switch]$SkipCompilerBuild
[switch]$SkipLibraryBuild
[switch]$SkipQuickJsBuild
[switch]$SkipNativeX64
[switch]$SkipFullRegression
[switch]$SkipPackage
```
Rutinler: Invoke-Checked, Run-ScriptCandidate.
Çağrı/yol başvuruları: bin\uxb.exe, build_64.bat, build_64.ps1, cmd.exe, compiler\scripts\build_64.bat, compiler\scripts\build_64.ps1, compiler\scripts\build_freebasic_a_group.bat, compiler\scripts\build_freebasic_a_group.ps1, compiler\scripts\build_uxjsruntime.ps1, compiler\scripts\run_language_surface_full_matrix.bat, pwsh.exe, runtime_ext\uxffi\build_uxffi_dll.bat, runtime_ext\uxjsruntime\build_uxjsrt.bat, runtime_ext\uxjsruntime\build_uxjsrt.ps1, tests\libraries\ffi_final\test_uxffi_uxconfig_roundtrip.py, tests\libraries\uxjsruntime\test_generated_js_e2e.py, tests\libraries\uxjsruntime\test_uxjsrt.py, tools\diagnostics\verify_final_ffi_quickjs_release.py, tools\release\package_uxbasic_distribution_final.ps1, tools\tests\run_ffi_contract_fix.ps1, xtestx\_runners\run_xtestx_expected_tests.py.

### `compiler/scripts/run_full_fp_runtime_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--enable-extfp-runtime
--extfp-diagnostics
--extfp-policy-json-out
--extfp-runtime-dir
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\runtime_ext\build_fp_runtime_all.bat, uxb\tests\fp_runtime\build_and_run_bigfp_runtime_probe.bat.

### `compiler/scripts/run_imported_library_smokes.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--include-probes
--timeout
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_library_smoke_runner.py.

### `compiler/scripts/run_keyword_layer_matrix.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_keyword_layer_decision_gate.py, uxb\tools\uxb_keyword_layer_matrix.py.

### `compiler/scripts/run_language_surface_full_matrix.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_language_surface_full_matrix.py.

### `compiler/scripts/run_layer_json.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory = $true)] [string]$Source
[ValidateSet("AST", "HIR", "MIR", "ALL")] [string]$Layer = "ALL"
[string]$OutDir = "dist/vscode_json"
[ValidateSet("AST", "MIR")] [string]$InterpreterBackend = "AST"
[ValidateSet("AST", "MIR")] [string]$CodegenSource = "AST"
[string]$WorkspaceRoot = ""
```
Rutinler: Read-JsonSafe.
Çağrı/yol başvuruları: build_64.bat, reportJson.exe, workspace_root_helpers.ps1.

### `compiler/scripts/run_library_abi10_smoke.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[switch]$SkipWebFailClose
[switch]$SkipBuild
[switch]$RequireMirX64
```
Rutinler: Read-TextSafe, Invoke-UxbRaw, Run-Case.
Çağrı/yol başvuruları: Name.exe, Root\compiler\scripts\build_libraries.ps1, Root\tests\libraries\abi10\build_abi10_test_dll.ps1, bin\uxb.exe, program.exe.

### `compiler/scripts/run_library_uxpython_smoke.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[switch]$SkipBuild
[switch]$SkipWebFailClose
```
Rutinler: Read-TextSafe, Invoke-InterpreterCase.
Çağrı/yol başvuruları: Root\compiler\scripts\build_libraries.ps1, bin\uxb.exe, uxpython_x64_ast.exe.

### `compiler/scripts/run_localhost_bridge.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--config
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\uxb_localhost_bridge.py.

### `compiler/scripts/run_mir_x64_completion_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--codegen-source
--debug
--emit-x64-nasm
--emit-x64-nasm-out
--enable-mir-x64-experimental
--mir-verify
--x64-codegen-policy-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe.

### `compiler/scripts/run_mir_x64_prompt3_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--codegen-source
--debug
--emit-x64-nasm
--emit-x64-nasm-out
--enable-mir-x64-experimental
--mir-verify
--x64-codegen-policy-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\compiler\scripts\build_uxb_main_64.bat.

### `compiler/scripts/run_mir_x64_surface_audit.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_mir_x64_surface_audit.py.

### `compiler/scripts/run_post_quickjs_ffi_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
[string]$Python = "python"
[switch]$SkipCompilerBuild
[switch]$SkipLibraryBuild
[switch]$SkipNativeX64
[switch]$SkipQuickJsGeneratedE2E
```
Rutinler: Invoke-NativeChecked, Invoke-RepoBuildScript.
Çağrı/yol başvuruları: bin\uxb.exe, build_64.bat, build_64.ps1, cmd.exe, compiler\scripts\build_64.bat, compiler\scripts\build_64.ps1, compiler\scripts\build_freebasic_a_group.bat, compiler\scripts\build_freebasic_a_group.ps1, pwsh.exe, runtime_ext\uxffi\build_uxffi_dll.bat, runtime_ext\uxffi\build_uxffi_dll.ps1, tests\libraries\ffi_final\test_uxffi_uxconfig_roundtrip.py, tests\libraries\uxjsruntime\test_generated_js_e2e.py, tools\diagnostics\verify_post_quickjs_patch.py.

### `compiler/scripts/run_prompt0_baseline.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxbc_baseline_runner.py.

### `compiler/scripts/run_release_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--root
--strict
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\release\uxb_release_gate.py.

### `compiler/scripts/run_runtime_library_probes.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[string]$OnnxModel = ""
[string]$LlamaModel = ""
[string]$LlamaCli = ""
[switch]$SkipPython
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: cmd.exe, run_uxjsruntime_smoke.bat, run_uxpython_smoke.bat, tests\fp_runtime\build_and_run_bigfp_runtime_probe.bat, tests\fp_runtime\build_and_run_fp_runtime_probe.bat, tests\uxaimath\build_and_run_uxaimath_probe.bat, tests\uxcollections\build_and_run_uxcollections_probe.bat, tests\uxdataframe\build_and_run_uxdataframe_probe.bat, tests\uxdataset\build_and_run_uxdataset_probe.bat, tests\uxgraph\build_and_run_uxgraph_probe.bat, tests\uxllama\build_and_run_uxllama_probe.bat, tests\uxmath\build_and_run_uxmath_probe.bat, tests\uxmathcore\build_and_run_uxmathcore_probe.bat, tests\uxmatrix\build_and_run_uxmatrix_probe.bat, tests\uxnn2\build_and_run_uxnn2_probe.bat, tests\uxnn3\build_and_run_uxnn3_probe.bat, tests\uxnn\build_and_run_uxnn_probe.bat, tests\uxonnx2\build_and_run_uxonnx2_probe.bat, tests\uxonnx\build_and_run_uxonnx_probe.bat, tests\uxstats2\build_and_run_uxstats2_probe.bat, tests\uxstats\build_and_run_uxstats_probe.bat, tests\uxtensor\build_and_run_uxtensor_probe.bat.

### `compiler/scripts/run_stage4_apply_full_safe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--apply
--move-root-src-duplicate
--move-tests-to-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_stage4_source_artifact_audit.py.

### `compiler/scripts/run_stage4_apply_move_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--apply
--move-tests-to-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_stage4_source_artifact_audit.py.

### `compiler/scripts/run_stage4_audit.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_stage4_source_artifact_audit.py.

### `compiler/scripts/run_step1_surface_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\audit\uxb_build_keyword_layer_matrix.py, tools\audit\uxb_keyword_layer_gate.py.

### `compiler/scripts/run_step1_surface_matrix.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\audit\uxb_build_keyword_layer_matrix.py.

### `compiler/scripts/run_step2_ast_contract_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\audit\uxb_ast_contract_build_matrix.py, tools\audit\uxb_ast_contract_collect_contract_nodes.py, tools\audit\uxb_ast_contract_collect_handlers.py, tools\audit\uxb_ast_contract_collect_parser_nodes.py, tools\audit\uxb_ast_contract_fake_status_scan.py, tools\audit\uxb_ast_contract_gate.py.

### `compiler/scripts/run_step2_ast_contract_matrix.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\audit\uxb_ast_contract_build_matrix.py.

### `compiler/scripts/run_step2_ast_json_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--ast-contract-check
--ast-contract-json-out
--ast-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe.

### `compiler/scripts/run_step2_mir_lowering_cli_audit.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_language_surface_full_matrix.bat, uxb\tools\uxb_step2_mir_lowering_cli_audit.py.

### `compiler/scripts/run_step3_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: compiler\scripts\run_step3_semantic_type_layout_gate.bat.

### `compiler/scripts/run_step3_project_runner.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--alias-layer
--alias-spec
--no-alias-layer
--project
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: run_step3_project_runner.bat, uxb\tools\uxb_differential_project_runner.py.

### `compiler/scripts/run_step3_semantic_type_layout_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--layout-json-out
--no-exe
--semantic-json-out
--target
--type-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: run_step3_semantic_type_layout_gate.bat, uxbasic.exe.

### `compiler/scripts/run_step4_type_class_ffi_audit.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_workspace_clean_guard.bat, uxb\tools\uxb_step4_type_class_ffi_audit.py.

### `compiler/scripts/run_step5_final_close.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_step5_fp_completion_audit.bat, uxb\compiler\scripts\run_workspace_clean_guard.bat, uxb\tools\uxb_codegen_regression_guard.py.

### `compiler/scripts/run_step5_fp_completion_audit.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--current
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_workspace_clean_guard.bat, uxb\tools\uxb_codegen_regression_guard.py, uxb\tools\uxb_step5_fp_completion_audit.py.

### `compiler/scripts/run_step6_release_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--max-tests
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_expected_runner.py, uxb\tools\uxb_layer_gate.py, uxb\tools\uxb_prior_step_gap_audit.py, uxb\tools\uxb_release_gate.py, uxb\tools\uxb_test_matrix_linker.py.

### `compiler/scripts/run_step7_final_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--dry-run
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\compiler\scripts\run_step5_final_close.bat, uxb\compiler\scripts\run_step6_release_gate.bat, uxb\compiler\scripts\run_workspace_clean_guard.bat, uxb\tools\uxb_final_gap_audit.py, uxb\tools\uxb_final_merge.py, uxb\tools\uxb_ide_command_contract.py, uxb\tools\uxb_step7_gate_compose.py, uxb\tools\uxb_vscode_contract_audit.py.

### `compiler/scripts/run_surface_suite.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--root
--strict
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\control\uxb_expected_actual_compare.py, uxb\tools\control\uxb_run_layer_tests.py, uxb\tools\control\uxb_surface_test_generator.py.

### `compiler/scripts/run_uxaimath_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\tests\uxaimath\build_and_run_uxaimath_probe.bat.

### `compiler/scripts/run_uxb_ast_alias_overlay.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--console-mode
--execmem
--interpreter-backend
--out
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_uxb_ast_alias_overlay.bat, uxb\bin\uxb.exe, uxb\tools\uxb_alias_overlay_preprocessor.py.

### `compiler/scripts/run_uxb_mir_alias_overlay.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--console-mode
--execmem
--interpreter-backend
--mir-verify
--out
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, run_uxb_mir_alias_overlay.bat, uxb\bin\uxb.exe, uxb\tools\uxb_alias_overlay_preprocessor.py.

### `compiler/scripts/run_uxcollections_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--build-x64
--build-x64-out
--codegen-source
--console-mode
--execmem
--interpreter-backend
--mir-verify
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \uxcollections_x64.exe, bin\uxb.exe, tests\uxcollections\build_and_run_uxcollections_probe.bat.

### `compiler/scripts/run_uxdataframe_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--build-x64
--build-x64-out
--codegen-source
--console-mode
--execmem
--interpreter-backend
--mir-verify
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \uxdataframe_x64.exe, bin\uxb.exe, powershell.exe, runtime_ext\uxdataframe\build_uxdataframe_dll.bat, runtime_ext\uxdataframe\fetch_uxdataframe_duckdb_deps.ps1, tests\uxdataframe\build_and_run_uxdataframe_probe.bat.

### `compiler/scripts/run_uxdataset_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\tests\uxdataset\build_and_run_uxdataset_probe.bat.

### `compiler/scripts/run_uxgraph_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxgraph\build_and_run_uxgraph_probe.bat.

### `compiler/scripts/run_uxllama_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--debug
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxllama\build_and_run_uxllama_probe.bat.

### `compiler/scripts/run_uxmath_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxmath\build_and_run_uxmath_probe.bat.

### `compiler/scripts/run_uxmathcore_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\tests\uxmathcore\build_and_run_uxmathcore_probe.bat.

### `compiler/scripts/run_uxmatrix_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxmatrix\build_and_run_uxmatrix_probe.bat.

### `compiler/scripts/run_uxnn2_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxnn2\build_and_run_uxnn2_probe.bat.

### `compiler/scripts/run_uxnn3_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxnn3\build_and_run_uxnn3_probe.bat.

### `compiler/scripts/run_uxnn_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxnn\build_and_run_uxnn_probe.bat.

### `compiler/scripts/run_uxonnx2_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxonnx2\build_and_run_uxonnx2_probe.bat.

### `compiler/scripts/run_uxonnx_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\runtime_ext\uxonnx\fetch_uxonnx_deps.bat, uxb\tests\uxonnx\build_and_run_uxonnx_probe.bat.

### `compiler/scripts/run_uxstats2_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\tests\uxstats2\build_and_run_uxstats2_probe.bat.

### `compiler/scripts/run_uxstats_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--execmem
--interpreter-backend
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\tests\uxstats\build_and_run_uxstats_probe.bat.

### `compiler/scripts/run_uxtensor_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_compiler_64.bat, uxb\bin\uxb.exe, uxb\build\uxb_main_64.exe, uxb\tests\uxtensor\build_and_run_uxtensor_probe.bat.

### `compiler/scripts/run_wasm_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--dummy-import-func
--emit-wasm
--emit-wat
--manifest-out
--wasm-out
--wasm-report-json-out
--wat-out
--wat2wasm
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, tools\wabt\bin\wasm-interp.exe, tools\wabt\bin\wasm-validate.exe, tools\wabt\bin\wat2wasm.exe.

### `compiler/scripts/run_webgpu_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--mir-json
--mode
--no-node-check
--out-dir
--uxb-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\uxb_browser_build_pro.py.

### `compiler/scripts/run_workspace_clean_guard.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: uxb\tools\uxb_workspace_clean_guard.py.

### `install_vscode_extension_local.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0vscode-extension\scripts\install_local.ps1, powershell.exe.

### `LOCAL_PATCH_AGENT.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \tools\uxb_local_patch_agent.py.

### `run_adim36_full_surface_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--max-tests
--root
--uxb-exe
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\build_64.bat, bin\uxb.exe, dp0bin\uxb.exe, dp0tools\control\uxb_adim36_full_surface_runner.py, run_adim36_full_surface_tests.bat, tools\control\uxb_adim36_full_surface_runner.py.

### `run_all_source_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
%~1
%~2
--exe
--fail-on-any
--limit
--mode
--paths
--quick
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\build_64.bat, bin\uxb.exe, dp0tools\tests\uxb_discover_and_run_all_sources.py, run_all_source_tests.bat.

### `run_all_yama_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--exe
--suite
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, dp0tools\tests\uxb_all_yama_tests.py.

### `run_final_ffi_quickjs_release.cmd`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \compiler\scripts\run_final_ffi_quickjs_release_gate.ps1, pwsh.exe.

### `run_final_ffi_quickjs_release_no_package.cmd`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \compiler\scripts\run_final_ffi_quickjs_release_gate.ps1, pwsh.exe.

### `run_post_quickjs_ffi_gate.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\run_post_quickjs_ffi_gate.ps1.

### `run_runtime_toolchain_doctor.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0tools\tests\uxb_runtime_toolchain_doctor.py.

### `run_uxb_ast.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--alias-layer
--console-mode
--interpreter-backend
--no-alias-layer
--out
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0bin\uxb.exe, run_uxb_ast.bat, uxb\tools\uxb_alias_overlay_preprocessor.py.

### `run_uxb_derin_analiz.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0uxb_derin_analiz.py.

### `RUN_UXB_ECOSYSTEM_DOCTOR.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0tools\library_tools\uxb_ecosystem_doctor.py.

### `run_uxb_mir.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--alias-layer
--exe
--help
--no-alias-layer
--out
--out-root
--run-id
--source
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\build_64.bat, bin\uxb.exe, run_uxb_mir.bat, tools\uxb_alias_overlay_preprocessor.py.

### `run_uxbrarp.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: run_uxbrarp.bat, tools\tools\uxbrarp.py, tools\uxbrarp.py, uxbrarp.py.

### `RUN_UXCLAZZ_UXBDLL_WINDOWS_TESTS.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$UxbExe = ""
[switch]$SkipUxclzBuild
[switch]$SkipDllBuild
[switch]$SkipHostTests
[switch]$Yes
```
Rutinler: Confirm-Step.
Çağrı/yol başvuruları: .\build\uxscalar_module_smoke_x64\program.exe, .\runtime_ext\uxclz\build_uxclz.bat, .\tools\tests\verify_uxclazz_uxbdll_patch.py, .\tools\uxbdll\uxbdll.py, .\tools\uxclazz\uxclazz.py, bin\uxb.exe, compiler\uxb.exe, uxb.exe.

### `run_uxjsruntime_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\build_uxjsruntime.ps1, powershell.exe.

### `run_uxpython_smoke.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0compiler\scripts\run_library_uxpython_smoke.ps1, powershell.exe.

### `run_uxwasmrt_gate.cmd`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0run_uxwasmrt_gate.ps1, powershell.exe, pwsh.exe.

### `run_uxwasmrt_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ''
[switch]$SkipCompilerBuild
[switch]$SkipUxbasicSmoke
[switch]$SkipCompilerGeneratedE2E
[switch]$SkipBrowserSmoke
```
Rutinler: Invoke-NativeStep, Write-FailureReport.
Çağrı/yol başvuruları: .\build_64.bat, .\tests\libraries\uxwasmrt\test_uxwasmrt.py, .\tools\tests\verify_uxwasmrt_patch.py, bin\uxb.exe, cmd.exe, node.exe, run_generated.py, runtime_ext\uxwasmrt\build_uxwasmrt.ps1, runtime_ext\uxwasmrt\fetch_wasm_deps.ps1, tools\wabt\bin\wasm-validate.exe, tools\wabt\bin\wat2wasm.exe.

### `run_yama6_interpreter_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--root
--uxb
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, tools\tests\run_yama6_interpreter_tests.py.

### `run_yama6_native_x64_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--root
--uxb
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, tools\tests\run_yama6_native_x64_tests.py.

### `run_yama6_runtime_abi_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\tests\check_yama6_runtime_dll.py.

### `run_yama7_libuv_backend_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--expect-backend
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: native\uxb_runtime\build_runtime_dll_libuv.bat, tools\tests\check_yama6_runtime_dll.py.

### `run_yama8_tbb_backend_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--expect-backend
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: native\uxb_runtime\build_runtime_dll_tbb.bat, tools\tests\check_yama6_runtime_dll.py.

### `tests/abi_model/run_abi_model_tests.ps1`

S-079 tur ABI (SIZEOF, F80 yuk 10 / adim 16): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\abi_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/array_bounds/run_array_bounds_tests.ps1`

S-101 LBOUND/UBOUND: her test AST, canonical-MIR, native x64 (bld), legacy AST-x64 ve JS (jsw + node) motorlarinda calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir. expected/<ad>.engines.txt: yalniz o motorlar ("AST MIR x64 AST-x64 JS"). expected/<ad>.contains.txt: "MOTOR=alt dize" - o motorun sonucu birebir degil, bu dizeyi ICERMELI (net red iletileri). WASM/WAT: derleme zamani sinirli diziler sabite katlanir (wasm_model paketi); calisma zamani sinirli dizi net reddedilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\array_bounds"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/array_params/run_array_param_tests.ps1`

S-068 dizi parametreleri (arr AS T[]) + dizi argumani dogrulamasi: her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\array_params"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/basicCodeTests/run_basiccodetest_matrix.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$CompilerPath = ".\build\uxbasic_ffi_gui.exe"
[string]$SourceGlob = "*.bas"
[string]$OutRoot = "tests\basicCodeTests\out_matrix"
[switch]$RunNativeExe
[switch]$IncludeExternalDllProbes
[switch]$IncludeInteractive
```
Rutinler: Resolve-CompilerPath, Invoke-Step, Test-ExternalProbe, Test-InteractiveProbe, Test-NativeRunSafe.
Çağrı/yol başvuruları: .\build\uxbasic_ffi_gui.exe, .\uxbasic.exe, program.exe.

### `tests/check_yama2_task_ast_json.py`

Yama-2 task AST denetleyicisi. Bir veya birden fazla ast.json dosyasini birlikte okur. EVENT/PIPE/THREAD/PARALEL node turlerinin tumunu ayni tek dosyada aramaz; run_yama2_task_tests.bat tarafindan uretilen tum AST dosyalarini birlikte denetler.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: walk, load_nodes, norm, main.
Çağrı/yol başvuruları: run_yama2_task_tests.bat, tools/tests/check_yama2_task_ast_json.py.

### `tests/cli_flags/run_cli_flag_tests.ps1`

CLI bayrak/fiil testleri (Mete'nin CLI denetim programinin ilk parcasi): her durum uxb'yi verilen argumanlarla calistirir; cikis kodu ve (birlesik stdout+stderr icinde) beklenen metin denetlenir. Sonsuz donguler zaman asimiyla kesilir. Kendi build klasorlerini gecici bir --out-root'a yonlendir (sarmalayici .cmd zaten yapiyorsa ekleme)

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\cli_flags"
[switch]$OnlyResponse
```
Rutinler: Invoke-Uxb.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.cmd.

### `tests/cli_mir_semantic/run_cli_mir_semantic_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_tests.py.

### `tests/cli_mir_semantic/run_tests.py`

S-024: typed MIR verification must include the semantic gate on every CLI alias.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
```
Rutinler: main.
Çağrı/yol başvuruları: yok.

### `tests/cli_mir_semantic/run_web_report_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_web_reports.py.

### `tests/cli_mir_semantic/run_web_reports.py`

S-027: verify emission evidence separately from actual JS/WASM execution.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
```
Rutinler: main, run.
Çağrı/yol başvuruları: tools/wabt/bin/wasm-validate.exe, tools/wabt/bin/wat2wasm.exe.

### `tests/compiler_consolidation/run_consolidation_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
[string]$TestRoot='.\tests\compiler_consolidation'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_consolidation_tests.py, run_diagnostic_contract_tests.py, run_matrix_export_tests.py.

### `tests/compiler_consolidation/run_consolidation_tests.py`

Run real compiler/native processes, compare exact output and preserve JSON evidence.

```text
ap.add_argument('--compiler', default=str(ROOT / 'bin' / 'uxb.exe'))
ap.add_argument('--report', required=True)
ap.add_argument('--runtime-dir')
artifacts.add_argument('--temp-builds', dest='temp_builds', action='store_true', default=True, help='Default: remove compiler/program artifacts after preserving JSON evidence and hashes.')
artifacts.add_argument('--keep-builds', dest='temp_builds', action='store_false', help='Keep diagnostic binaries under build/test_outputs, never in reports.')
ap.add_argument('--only', nargs='*', default=list(EXPECTED) + list(EXPECTED_ERROR))
ap.add_argument('--engines', nargs='*')
```
Rutinler: norm, invoke, build_probe, main.
Çağrı/yol başvuruları: /msys64/ucrt64/bin/gcc.exe, program.exe, uxb.exe, wat2wasm.exe.

### `tests/compiler_consolidation/run_diagnostic_contract_tests.py`

Exercise diagnostic CLI output, requested logs and controlled I/O failures.

```text
parser.add_argument('--compiler', required=True)
parser.add_argument('--report', required=True)
parser.add_argument('--runtime')
parser.add_argument('--with-iff', action='store_true')
```
Rutinler: json_records, main, invoke.
Çağrı/yol başvuruları: diagnostic_record_probe.exe, fbc64.exe, sys.exe.

### `tests/compiler_consolidation/run_host_package_contract.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory)][string]$Uxb
[string]$Objdump = 'C:/msys64/ucrt64/bin/objdump.exe'
[string]$Report = 'reports/workspace_maintenance/host_package_contract.json'
```
Rutinler: Check.
Çağrı/yol başvuruları: /msys64/ucrt64/bin/objdump.exe, UXB-Common.ps1, build_64.ps1, compiler/scripts/build_c_full_api.ps1, compiler/scripts/build_cbase_libraries.ps1, compiler/scripts/build_uxb_main_64.ps1, tests/libraries/uxgsl/run_uxgsl_smoke_tests.ps1, tests/run_all_model_tests.ps1.

### `tests/compiler_consolidation/run_matrix_export_tests.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
ap.add_argument('--compiler', required=True)
ap.add_argument('--report', required=True)
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/compiler_consolidation/run_runtime_variant_tests.py`

Run each runtime variant in its own process, including real task callbacks.

```text
parser.add_argument('--root')
parser.add_argument('--full')
parser.add_argument('--report')
parser.add_argument('--child')
```
Rutinler: child, main, callback.
Çağrı/yol başvuruları: sys.exe.

### `tests/const_scope/run_const_scope_tests.ps1`

S-140: CONST kapsami. Modul duzeyi, NAMESPACE ve rutin ici sabitler (tamsayi, F64, STRING) ilgili kapsamda gorunur; ayni adli parametre/yerel sabiti golgeler. AST, canonical-MIR, native x64 (bld), legacy AST-x64 ve JS (node) ayni programla, ayni expected/<ad>.txt ile birebir karsilastirilir. expected/<ad>.engines.txt varsa yalniz o motorlar. Bir program sonsuz donguye girerse (eski legacy hatasi: namespace sabitli FOR) kosucu kilitlenmesin: sure asiminda oldurulur.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\const_scope"
```
Rutinler: Norm, Run-Exe.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/coordination_20260913/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0s064_reg4.exe.

### `tests/coordination_20260913/run_native_build_probe.py`

Build and RUN both native routes in fresh, nested paths containing spaces.

```text
parser.add_argument('--cwd', type=Path, default=root)
parser.add_argument('--compiler', type=Path, default=root / 'bin/uxb.exe')
```
Rutinler: run.
Çağrı/yol başvuruları: bin/uxb.exe, probe.exe.

### `tests/coordination_20260913/run_wat_memory_probe.py`

Compile the real FreeBASIC emitter, validate its WASM and execute memory operations.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: run.
Çağrı/yol başvuruları: emit.exe, tools/FreeBASIC-1.10.1-win64/fbc64.exe, tools/wabt/bin/wasm-validate.exe, tools/wabt/bin/wat2wasm.exe.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_both_build/both_compare/ast_exe/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_both_build/both_compare/mir_exe/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s025_both_build/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_both_build/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_both_build/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_both_build/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_inf_both/both_compare/ast_exe/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_inf_both/both_compare/mir_exe/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s025_inf_both/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/coordination_20260913/s025_inf_both/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/coordination_20260913/s025_inf_both/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/coordination_20260913/s025_inf_both/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0program.exe.

### `tests/coordination_20260913/s028_log_probe.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
p.add_argument('--compiler', type=Path, default=root / 'bin/uxb.exe')
p.add_argument('--expect-failure', action='store_true')
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin/uxb.exe, lifecycle.exe, tools/FreeBASIC-1.10.1-win64/fbc64.exe.

### `tests/coordination_20260913/s028_output_probe.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
p.add_argument('--compiler', type=Path, default=root / 'bin/uxb.exe')
```
Rutinler: probe.
Çağrı/yol başvuruları: bin/uxb.exe.

### `tests/coordination_20260913/s040_scope_probe.py`

End-to-end coverage scope regression; preserve fixtures/reports for review.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: run.
Çağrı/yol başvuruları: sys.exe, uxb_full_coverage_analyzer.py.

### `tests/coordination_20260913/s042_extract_and_diff.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/declare_siki/run_declare_siki_tests.ps1`

S-544, Mete 2026-10-28: DECLARE optional, including forward calls. Historical neg_ forward-use fixtures now require actual successful output. Explicit missing definitions and signature mismatches remain errors. Kosucu tests\oop_parity ile ortaktir (ayni biçim); yalniz test koku farklidir.

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\oop_parity\run_oop_parity_tests.ps1, .\bin\uxb.exe.

### `tests/diagnostics/run_const_write_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_parenless_call_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s219_rotate_width_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/diagnostics/run_s443_magic_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s444_js_exception_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s445_dll_type_list_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check, RunReject.
Çağrı/yol başvuruları: .\bin\uxb.exe, s445.exe.

### `tests/diagnostics/run_s446_f32_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s459_mixed_numeric_string_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s464_interpreter_compare_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, CheckCompare.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s480_ast_regression_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s497_field_bitwise_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/diagnostics/run_s498_runtime_diagnostic_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s499_libtype_target_gate_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Alias('Uxb')][string]$Compiler = 'bin/uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin/uxb.exe.

### `tests/diagnostics/run_s500_libtype_diagnostic_consistency_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s502_f32_array_direct_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s503_f32_storage_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s504_f64_compare_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s505_unary_comparison_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/diagnostics/run_s506_float_to_integer_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s508_fix_type_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_s510_mir_f32_rounding_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Norm, Check.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/diagnostics/run_union_overlay_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check.
Çağrı/yol başvuruları: .\bin\uxb.exe, tools\wabt\bin\wat2wasm.exe, union_overlay.exe.

### `tests/dosya_tutamaci/run_dosya_tutamaci_tests.ps1`

S-548 / S-549: FREEFILE ve FILE_HANDLE. Her program AST, MIR, native x64 (bld), eski AST-x64 ve istege bagli JS / WASM'da kosulur (expected\<ad>.engines.txt); cikti expected\<ad>.txt ile birebir ya da expected\<ad>.contains.txt (motor=metin) ile karsilastirilir. Dosya yazan programlar icin HER program kendi gecici calisma dizininde kosar (olusan dosyalar depoyu ve diger kosulari kirletmez, out\ klasorunu paylasan koşucularla da cakismaz); bu yuzden her yol mutlaktir.

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: Norm, Kos, Motor.
Çağrı/yol başvuruları: .\bin\uxb.exe, m.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/ecosystem/run_ecosystem_hardening.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root=''
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: test_ecosystem_hardening.py, tools\library_tools\uxb_library_source_gate.py.

### `tests/ecosystem/test_ecosystem_hardening.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: load, main.
Çağrı/yol başvuruları: spec.loader.exe, sys.exe, tools/library_tools/uxb_ecosystem_doctor.py, tools/library_tools/uxb_library_build.py.

### `tests/enum_tests/basicCodeTests/run_basiccodetest_matrix.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$CompilerPath = ".\build\uxbasic_ffi_gui.exe"
[string]$SourceGlob = "*.bas"
[string]$OutRoot = "tests\basicCodeTests\out_matrix"
[switch]$RunNativeExe
[switch]$IncludeExternalDllProbes
[switch]$IncludeInteractive
```
Rutinler: Resolve-CompilerPath, Invoke-Step, Test-ExternalProbe, Test-InteractiveProbe, Test-NativeRunSafe.
Çağrı/yol başvuruları: .\build\uxbasic_ffi_gui.exe, .\uxbasic.exe, program.exe.

### `tests/enum_tests/fp_runtime/build_and_run_bigfp_runtime_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \bigfp_runtime_probe.exe, \msys64\ucrt64\bin\gcc.exe, uxb\runtime_ext\bigfp\build_bigfp_dll.bat.

### `tests/enum_tests/fp_runtime/build_and_run_fp_runtime_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \fp_runtime_probe.exe, \msys64\ucrt64\bin\gcc.exe, uxb\runtime_ext\build_fp_runtime_all.bat.

### `tests/enum_tests/trace/trace_smoke_compile.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--hook-trace
--layer-timing-json-out
--session-live-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, build\uxb_main_64.exe, compiler\scripts\build_uxb_main_64.bat.

### `tests/enum_tests/uxaimath/build_and_run_uxaimath_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxaimath_dll_probe.exe, uxb\runtime_ext\uxaimath\build_uxaimath_dll.bat, uxb\runtime_ext\uxaimath\build_uxaimath_fallback_dll.bat.

### `tests/enum_tests/uxcollections/build_and_run_uxcollections_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--cflags
--libs
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \msys64\ucrt64\bin\pkg-config.exe, \uxcollections_probe.exe, uxb\runtime_ext\uxcollections\build_uxcollections_dll.bat.

### `tests/enum_tests/uxdataframe/build_and_run_uxdataframe_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxdataframe_probe.exe, uxb\runtime_ext\uxdataframe\build_uxdataframe_dll.bat.

### `tests/enum_tests/uxdataset/build_and_run_uxdataset_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxdataset_probe.exe, uxb\runtime_ext\uxdataset\build_uxdataset_dll.bat.

### `tests/enum_tests/uxgraph/build_and_run_uxgraph_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxgraph_dll_probe.exe, uxb\runtime_ext\uxgraph\build_uxgraph_dll.bat.

### `tests/enum_tests/uxllama/build_and_run_uxllama_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxllama_dll_probe.exe, uxb\runtime_ext\uxllama\build_uxllama_dll.bat.

### `tests/enum_tests/uxmath/build_and_run_uxmath_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmath_dll_probe.exe, uxb\runtime_ext\uxmath\build_uxmath_dll.bat.

### `tests/enum_tests/uxmathcore/build_and_run_uxmathcore_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmathcore_probe.exe, uxb\runtime_ext\uxmathcore\build_uxmathcore_dll.bat.

### `tests/enum_tests/uxmatrix/build_and_run_uxmatrix_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmatrix_probe.exe, uxb\runtime_ext\uxmatrix\build_uxmatrix_dll.bat, uxb\runtime_ext\uxmatrix\build_uxmatrix_fallback_dll.bat.

### `tests/enum_tests/uxnn/build_and_run_uxnn_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxnn_dll_probe.exe, uxb\runtime_ext\uxnn\build_uxnn_dll.bat, uxb\runtime_ext\uxnn\build_uxnn_fallback_dll.bat.

### `tests/enum_tests/uxnn2/build_and_run_uxnn2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, uxb\dist\runtime_ext\uxnn2_dll_probe.exe, uxb\runtime_ext\uxnn2\build_uxnn2_dll.bat.

### `tests/enum_tests/uxnn3/build_and_run_uxnn3_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxnn3_dll_probe.exe, uxb\runtime_ext\uxnn3\build_uxnn3_dll.bat.

### `tests/enum_tests/uxonnx/build_and_run_uxonnx_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxonnx_probe.exe, uxb\runtime_ext\uxonnx\build_uxonnx_dll.bat.

### `tests/enum_tests/uxonnx2/build_and_run_uxonnx2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, uxb\dist\runtime_ext\uxonnx2_probe.exe, uxb\runtime_ext\uxonnx2\build_uxonnx2_dll.bat, uxb\runtime_ext\uxonnx2\fetch_uxonnx2_deps.bat.

### `tests/enum_tests/uxstats/build_and_run_uxstats_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxstats_dll_probe.exe, uxb\runtime_ext\uxstats\build_uxstats_dll.bat.

### `tests/enum_tests/uxstats2/build_and_run_uxstats2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxstats2_dll_probe.exe, uxb\runtime_ext\uxstats2\build_uxstats2_dll.bat.

### `tests/enum_tests/uxtensor/build_and_run_uxtensor_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxtensor_probe.exe, uxb\runtime_ext\uxtensor\build_uxtensor_dll.bat.

### `tests/exceptions_cross/run_exceptions_cross_tests.ps1`

S-160: THROW/ASSERT istisnasi rutin sinirini gecer (cagirandaki TRY yakalar; TRY disinda program durur; gorevde gorev hatasi). Kosucu tests/task_model ile ayni; ek: expected/<ad>.absent.txt satirlari hicbir motorun ciktisinda gecmemeli. expected/_engines.txt  : motor basina durum, "MOTOR=run" veya "MOTOR=reject" (S-030 faz durumu; tek yerde tutulur). run    -> cikti expected/<ad>.txt ile birebir ayni olmali (ya da <ad>.contains.txt'deki o motor satirini icermeli). reject -> motor TEMIZ reddetmeli: sonuc "ERROR:" icermeli ve "Execution completed successfully" icermemeli (sessiz yanlis sonuc yasak). Red metni kasten sabitlenmez; acik red iletileri Faz 1B/2'de eklenince _engines.txt "MOTOR=reje

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\exceptions_cross"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe, eng.exe.

### `tests/float_text/run_float_text_tests.ps1`

S-142b: ondalik sayi metni her motorda ayni kural: tipin izin verdigi hane sayisi (F64 16, F32 7), ilave sifir yok, us en az iki haneli ("1e+20"), inf/nan yazimi. AST, canonical-MIR, native x64 (bld), legacy AST-x64 ve JS (node) ayni programla, ayni expected/<ad>.txt ile birebir karsilastirilir. expected/<ad>.engines.txt varsa yalniz o motorlar.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\float_text"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/fp_runtime/build_and_run_bigfp_runtime_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \bigfp_runtime_probe.exe, \msys64\ucrt64\bin\gcc.exe, uxb\runtime_ext\bigfp\build_bigfp_dll.bat.

### `tests/fp_runtime/build_and_run_fp_runtime_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \fp_runtime_probe.exe, \msys64\ucrt64\bin\gcc.exe, uxb\runtime_ext\build_fp_runtime_all.bat.

### `tests/iterators/run_iterator_tests.ps1`

S-038 iterator sozlesmesi (FOR EACH / DO EACH: LIST, SET, DICT, dizi): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\iterators"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/knowledge_pipeline/test_hybrid_contract.py`

Failure and context-budget contracts; no model quality is inferred here.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: test_definition_location_uses_body_not_forward_declaration, test_behavior_question_keeps_normal_answer_route, test_instructions_survive_large_evidence, test_backend_path_beats_parse_state_hint, test_chat_failure_and_empty_answer_are_not_success.
Çağrı/yol başvuruları: yok.

### `tests/knowledge_pipeline/test_index_resume.py`

Fault-injection tests for index durability, using an isolated in-memory store.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: __init__, get, upsert, delete, test_failure_preserves_old_vectors_and_manifest, test_budget_resume_embeds_each_new_chunk_only_once, scenario.
Çağrı/yol başvuruları: yok.

### `tests/knowledge_pipeline/test_symbol_query.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: test_camel_case_symbol_precedes_slot_expansion.
Çağrı/yol başvuruları: yok.

### `tests/kv_kapanis/run_kv_kapanis_tests.ps1`

Kilavuz V2 kayitlarinin (SORUN_TAKIP S-numaralari) kapanis testleri. Dosya adi onekleri kaydi gosterir (s623_..., s569_...). Her program AST, MIR, native x64 (bld), eski AST-x64, JS ve WASM'da kosulur; expected\<ad>.engines.txt motor listesini daraltir. expected\<ad>.txt           : birebir beklenen cikti (INFO/WARN satirlari atilir) expected\<ad>.contains.txt  : "MOTOR=metin" satirlari -> cikti metni icermeli (birebir yerine) expected\<ad>.rc.txt        : "MOTOR=kod" satirlari -> programin cikis kodu (yorumlayicilar: uxb run cikisi; native: exe cikisi) Her program kendi gecici calisma dizininde kosar (dosya acan programlar depoyu kirletmez); her yol mutlaktir. Native yollar icin yalitilmis 

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$Filtre = ""
```
Rutinler: Norm, Kos, Motor, Harita.
Çağrı/yol başvuruları: .\bin\uxb.exe, m.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/language_guards/run_language_guard_tests.ps1`

Dil korumalari (rezerve adlar vb.) -- derleme zamani hatalari: her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir. INFO satirlari ve AST'nin FFI ilke uyarilari (stderr, REPORT_ONLY) sonuca dahil degil

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\language_guards"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/libraries/abi10/build_abi10_test_dll.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: build_abi10_test_dll.ps1, powershell.exe.

### `tests/libraries/abi10/build_abi10_test_dll.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = ""
[string]$Gcc = ""
```
Rutinler: Resolve-Tool.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, gcc.exe, x86_64-w64-mingw32-gcc.exe.

### `tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
parser.add_argument('--root', required=True)
```
Rutinler: require_pe32_plus, main, invoke.
Çağrı/yol başvuruları: yok.

### `tests/libraries/run_library_smoke_parallel.py`

Run the existing isolated library suites with bounded independent workers.

```text
parser.add_argument('--compiler', required=True)
parser.add_argument('--report', required=True)
parser.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
```
Rutinler: run_case.
Çağrı/yol başvuruları: _smoke_tests.ps1.

### `tests/libraries/uxgsl/build_all.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0build_program.bat, dp0link_program.bat.

### `tests/libraries/uxgsl/build_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\build_import.bat, dp0interop\toolchain.env.bat.

### `tests/libraries/uxgsl/interop/build_import.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0toolchain.env.bat.

### `tests/libraries/uxgsl/interop/link_command.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop_program.exe, dp0toolchain.env.bat.

### `tests/libraries/uxgsl/interop/toolchain.env.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: Files\CodeBlocks\MinGW\bin\gcc.exe, Files\CodeBlocks\MinGW\bin\nasm.exe.

### `tests/libraries/uxgsl/link_program.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0interop\toolchain.env.bat, dp0uxgsl_basic_root_bisection_smoke.exe.

### `tests/libraries/uxgsl/run_uxgsl_smoke_tests.ps1`

uxgsl (GNU Scientific Library koprusu) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) calistirilir. Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. CODEPTR kullanan (geri cagirma) testlerde yorumlayicilar (AST/MIR) gercek kod adresi veremez -> NET "requires native x64" hatasi beklenir (S-076); native ve legacy PASS verir. Onkosul: bin\uxgsl.dll (+ libgsl-28.dll, libgslcblas-0.dll); derleme bunlari PE import tablosundan bulup cikti klasorune kopyalar.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\libraries\uxgsl"
[string[]]$Only = @()
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ../../turkce_ad/run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/libraries/uxjsruntime/test_generated_js_e2e.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
parser.add_argument('--root', required=True)
```
Rutinler: main.
Çağrı/yol başvuruları: uxb.exe.

### `tests/libraries/uxjsruntime/test_uxjsrt.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--dll', default='bin/uxjsrt.dll')
```
Rutinler: configure, error, check, main.
Çağrı/yol başvuruları: yok.

### `tests/libraries/uxlogic_codex1/test_load_recovery.py`

Execute a freshly built DLL; reject incomplete Lua and recover with real Lua.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: /msys64/ucrt64/bin/gcc.exe.

### `tests/libraries/uxpython/uxpython_fixture.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: add, greet, describe.
Çağrı/yol başvuruları: yok.

### `tests/libraries/uxraylib/run_uxraylib_smoke_tests.ps1`

uxraylib (raylib/raygui koprusu, CPU-tarafi Image API'si) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) calistirilir. Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. CODEPTR kullanan (geri cagirma) testlerde yorumlayicilar (AST/MIR) gercek kod adresi veremez -> NET "requires native x64" hatasi beklenir (S-076); native ve legacy PASS verir. Onkosul: bin\uxraylib.dll (+ libraylib.dll, glfw3.dll); runtime_ext\uxraylib\build_wrappers.bat uretir; derleme bagimliliklari PE import tablosundan bulup cikti klasorune kopyalar. Testler PENCERE ACMAZ.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\libraries\uxraylib"
[int]$TimeoutSec = 1200
[string[]]$Only = @()
```
Rutinler: Norm, RunTimed.
Çağrı/yol başvuruları: ..\..\support\controlled_process.ps1, .\bin\uxb.exe, runtime_ext\uxraylib\build_wrappers.bat.

### `tests/libraries/uxsdl3/run_uxsdl3_smoke_tests.ps1`

uxsdl3 (SDL3 sarmalayicisi) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) calistirilir. Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. Testler PENCERE/HOPARLOR ACMAZ: SDL'in dummy video/ses suruculeri programin icinde ipucu (SDL_VIDEO_DRIVER/SDL_AUDIO_DRIVER) ile secilir. Yazilan gecici dosyalar out\ altindadir ve test sonunda silinir. Onkosul: bin\uxsdl3.dll + bin\SDL3.dll (runtime_ext\uxraylib\build_wrappers.bat uretir; native derleme bagimliliklari PE import tablosundan kopyalar). Her calistirma zaman asimina bagli: takilan bir motor TIMEOUT olarak raporlanir, koşucuyu kilitlemez.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\libraries\uxsdl3"
[int]$TimeoutSec = 240
[string[]]$Only = @()
```
Rutinler: Norm, RunTimed.
Çağrı/yol başvuruları: ..\..\support\controlled_process.ps1, .\bin\uxb.exe, runtime_ext\uxraylib\build_wrappers.bat.

### `tests/libraries/uxwasmrt/test_uxwasmrt.py`

!/usr/bin/env python3

```text
ap.add_argument('--root', default='.')
ap.add_argument('--json-out', default='')
```
Rutinler: fail, configure, err, main.
Çağrı/yol başvuruları: yok.

### `tests/libraries/uxwasmrt/verify_distribution.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--json-out', default='')
```
Rutinler: run, configure, last_error, main.
Çağrı/yol başvuruları: .\\tests\\libraries\\uxwasmrt\\test_uxwasmrt.py, node.exe, sys.exe, uxb.exe, wasm-validate.exe, wat2wasm.exe.

### `tests/library_surface_gaps/run_library_surface_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = (Join-Path $PSScriptRoot '..\..\bin\uxb.exe')
[string]$ReportRoot = (Join-Path $PSScriptRoot '..\..\reports\library_surface_gaps')
[string[]]$Libraries = @()
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\..\bin\uxb.exe.

### `tests/library_type_contract/run_library_type_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Alias('Uxb')][string]$Compiler = 'bin/uxb.exe'
[string]$ReportPath = 'reports/library_type_contract/results.json'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin/uxb.exe, tools/FreeBASIC-1.10.1-win64/fbc64.exe.

### `tests/memory_model/run_memory_model_tests.ps1`

S-069/S-071 bellek modeli regresyonu: her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\memory_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/memoryref_model/run_memoryref_model_tests.ps1`

S-056 MemoryRef (dizi isaretcisi sinir/omur denetimi): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\memoryref_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/mir_full_json_v2/run_mir_full_json_v2_smoke.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
[string]$Uxb = ""
[switch]$SkipBuild
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, build_64.bat, tests\mir_full_json_v2\verify_mir_full_json_v2.py, uxb.exe.

### `tests/mir_full_json_v2/verify_mir_full_json_v2.py`

Static patch gate and runtime schema validator for uxb-mir-full-json-2.

```text
parser.add_argument('--root', type=Path, default=Path.cwd())
parser.add_argument('--json', type=Path)
parser.add_argument('--uxb', type=Path)
parser.add_argument('--source', type=Path)
parser.add_argument('--out', type=Path)
```
Rutinler: fail, assert_type, static_gate, validate_source, validate_runtime_json, run_compiler, main.
Çağrı/yol başvuruları: yok.

### `tests/native/ffi_contract/test_uxffi_contract.py`

!/usr/bin/env python3

```text
ap.add_argument('--root', default='.')
```
Rutinler: main, call.
Çağrı/yol başvuruları: yok.

### `tests/native/ffi_contract/test_uxffi_pointer_classify.py`

S-653: uxffi.dll ayirimi -- gercek adres (VARPTR, heap) ile 32 bitlik tutamac belirteci.  Belirtecler 32 bitliktir (I32/U32 degiskene sigsin diye) ve 0x40000000..0x7FFFFFFF bandini kullanir; ayni bantta gercek kullanici adresleri de bulunabilir. Eski kural "banttaki her deger belirectir" idi ve gercek bir adresi "stale or invalid pointer handle token" diye reddederdi. Yeni kural: CANLI belirtec -> belirtec; canli degil ve adres bellekte ayrilmissa -> gercek isaretci; ne canli ne ayrilmis ama eskiden dagitilmis bir yuvaya uyuyorsa -> bayat.  Kullanim: python test_uxffi_pointer_classify.py --dll <uxffi.dll yolu>   (varsayilan: <kok>\bin\uxffi.dll)

```text
ap.add_argument('--root', default='.')
ap.add_argument('--dll', default=None)
```
Rutinler: main, call.
Çağrı/yol başvuruları: test_uxffi_pointer_classify.py.

### `tests/native_nul/check_native_span.py`

Validate the real length-bearing memory/C ABI and persistent text ownership.

```text
parser.add_argument('--dll', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--null-slot-probe', action='store_true', help='Internal child: a null destination must raise a runtime error')
```
Rutinler: api, check.
Çağrı/yol başvuruları: sys.exe.

### `tests/native_nul/run_native_nul_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/native_runtime/task_v2/run_task_v2_tests.ps1`

S-030 Faz 2A adim 1: gorev ABI v2 calisma zamaninin DLL'siz stres testi. uxb_runtime_task_v2.cpp + task_v2_stress.cpp dogrudan derlenir (DLL derleme bayraklariyla ayni: -Wall -Wextra -Werror). Her kip ayri surectir; beklenen cikis kodu ve stdout/stderr alt dizesi denetlenir. Zamanlamaya bagli hatalari yakalamak icin her kip $Repeat kez, farkli isci sayilariyla (1, 2, AUTO) calistirilir. DLL derleme listesinin aynisi (native/uxb_runtime/build_runtime_dll.ps1, std arka ucu) + test kaynagi.

```text
[string]$Gxx = "C:\msys64\ucrt64\bin\g++.exe"
[int]$Repeat = 3
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: native/uxb_runtime/build_runtime_dll.ps1, task_v2_stress.exe.

### `tests/numeric_model/run_numeric_model_tests.ps1`

S-077/S-078 sayisal model regresyonu (U64/I64/dar tamsayi): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\numeric_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/oop_class_arrays/run_oop_class_array_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/oop_codex1/run_matrix.py`

Run expected-output checks against one isolated compiler, including real EXEs.

```text
parser.add_argument('--compiler', type=Path, default=ROOT / 'bin/uxb_codex1_oop.exe')
parser.add_argument('--cases', default=','.join(CASES))
parser.add_argument('--modes', default='AST,MIR,JS,x64_MIR,x64_AST')
parser.add_argument('--label', default='fresh')
```
Rutinler: norm, invoke, main.
Çağrı/yol başvuruları: bin/uxb_codex1_oop.exe, program.exe.

### `tests/oop_multidim/run_oop_multidim_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/oop_parity/run_oop_parity_tests.ps1`

S-037 OOP esitligi (sinif/kalitim/sanal dagitim/SUPER/arayuz/erisim): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir. 2026-10-16: JS ve WASM de istege bagli motorlardir (varsayilan yine AST, MIR, x64, AST-x64): bir testin expected\<ad>.engines.txt dosyasina "JS" / "WASM" yazilirsa o test web hedefinde de koşar ve ayni beklentiyle karsilastirilir (JS: uxb jsw -> node; WASM: uxb wat --emit-wasm -> wat2wasm -> node run_wasm.js).

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\oop_parity"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\tools\wabt\bin\wat2wasm.exe.

### `tests/oop_redim/run_oop_redim_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/oop_remaining/run_oop_remaining_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/operators_codex2/run.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Compiler = 'bin/uxb_codex2_operators.exe'
[switch]$Native
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin/uxb_codex2_operators.exe, powershell.exe, tools/x64_compare/run_with_timeout.ps1.

### `tests/output_isolation/run_output_isolation_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_tests.py.

### `tests/output_isolation/run_tests.py`

S-028: real execution and output ownership from unrelated empty working directories.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--quick', action='store_true')
```
Rutinler: norm, main, execute_case, run.
Çağrı/yol başvuruları: tools/wabt/bin/wat2wasm.exe.

### `tests/preprocessor_effects/run_effects.py`

Preprocessor directive effects: every directive that used to be "recorded only" (S-672) must change something observable.  Each case writes a program (plus helper files) into a private scratch directory, runs the compiler on it and checks the effect: text on the terminal, the expanded source, the preprocess-result JSON, or files the compiler wrote below the output root. A directive without an effect cannot pass here. Cases are grouped by the stage the effect happens in:   P  preprocessing time (`lex` verb): diagnostics, source rewriting, templates, sections, path aliases, limits   E  package output time (`jsw --emit-browser`): assets, manifest, shell, JSON/Markdown/WAT files, export tables

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--only', default='', help='run only cases whose name contains this text')
```
Rutinler: fnv1a, case, rel_matches, run_case, main.
Çağrı/yol başvuruları: wat2wasm.exe.

### `tests/preprocessor_effects/run_effects_tests.ps1`

S-672: every preprocessor directive must have an observable effect (see ai_koordinasyon\ONISLEMCI_ETKI_MATRISI_20261025.md).

```text
[string]$Uxb = '.\bin\uxb.exe'
[string]$Only = ''
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_effects.py.

### `tests/preprocessor_unified/measure_mir.py`

Serial alternating baseline/candidate measurements with raw timing evidence.

```text
parser.add_argument('--baseline', required=True)
parser.add_argument('--candidate', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--repeat', type=int, default=3)
parser.add_argument('--no-trace', action='store_true')
parser.add_argument('--only', choices=['straight_240', 'loop_100', 'loop_10000'])
```
Rutinler: main.
Çağrı/yol başvuruları: yok.

### `tests/preprocessor_unified/run_contract.py`

Actual preprocessing effects, removed selectors, and inactive block isolation.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--orphan-all', action='store_true', help='Verify every standalone block terminator is rejected')
```
Rutinler: main, add.
Çağrı/yol başvuruları: yok.

### `tests/preprocessor_unified/run_unified_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, \.exe, run_contract.py.

### `tests/print_zones/run_print_zone_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
[string]$TestRoot=$PSScriptRoot
[string[]]$Only=@()
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/program_end/run_program_end_tests.ps1`

S-156: END semantigi -- dort motorlu karsilastirma task_model kosucusuyla ayni (expected\_engines.txt, teste ozel expected\<ad>.engines.txt). Ayrica kosucu yazmamak icin onu bu klasorle cagirir.

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\task_model\run_task_model_tests.ps1, .\bin\uxb.exe.

### `tests/routine_scope/run_routine_scope_tests.ps1`

S-167 (BYREF takma ad) + S-168 (rutin yereli/parametresi globali golgeler): dort motorlu karsilastirma task_model kosucusuyla ayni (expected\_engines.txt, teste ozel expected\<ad>.engines.txt).

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\task_model\run_task_model_tests.ps1, .\bin\uxb.exe.

### `tests/run_all_model_tests.ps1`

Yalnız belirli paketleri koşmak için: -Only oop_parity,iterators Selected packages must expose their existing -Only case filter. Hızlı tur: yalnız AST + canonical-MIR yerine tüm dört motor değil, paketin kendi koşucusu ne yapıyorsa o. Varsayilan: her uxb cagrisinin urettigi build\<zaman> klasoru (S-117: ~1,7 MB, FFI'li programlarda +53 MB DLL) gecici bir --out-root altina yonlendirilir ve koşu bitince silinir. Klasorleri build\ altinda tutmak icin: S-072 (ilk parça): dil davranış paketlerinin TEK koşucusu. Her paket kendi klasöründeki run_*.ps1 ile çalışır (AST, canonical-MIR, native x64, legacy AST-x64; beklenen çıktı expected/<ad>.txt, hata metni expected/<ad>.contains.txt, motor süzgeci e

```text
[string]$Uxb = ".\bin\uxb.exe"
[string[]]$Only = @()
[string[]]$Cases = @()
[string]$ReportPath = ".\test_results\model_suite_summary.md"
[switch]$KeepBuildFolders
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, tests\abi_model\run_abi_model_tests.ps1, tests\array_bounds\run_array_bounds_tests.ps1, tests\array_params\run_array_param_tests.ps1, tests\cli_flags\run_cli_flag_tests.ps1, tests\cli_mir_semantic\run_cli_mir_semantic_tests.ps1, tests\cli_mir_semantic\run_web_report_tests.ps1, tests\compiler_consolidation\run_consolidation_tests.ps1, tests\const_scope\run_const_scope_tests.ps1, tests\declare_siki\run_declare_siki_tests.ps1, tests\diagnostics\run_const_write_tests.ps1, tests\diagnostics\run_parenless_call_tests.ps1, tests\diagnostics\run_s219_rotate_width_tests.ps1, tests\diagnostics\run_s443_magic_tests.ps1, tests\diagnostics\run_s444_js_exception_tests.ps1, tests\diagnostics\run_s445_dll_type_list_tests.ps1, tests\diagnostics\run_s446_f32_tests.ps1, tests\diagnostics\run_s459_mixed_numeric_string_tests.ps1, tests\diagnostics\run_s464_interpreter_compare_tests.ps1, tests\diagnostics\run_s480_ast_regression_tests.ps1, tests\diagnostics\run_s499_libtype_target_gate_tests.ps1, tests\diagnostics\run_s500_libtype_diagnostic_consistency_tests.ps1, tests\diagnostics\run_s502_f32_array_direct_tests.ps1, tests\diagnostics\run_s503_f32_storage_tests.ps1, tests\diagnostics\run_s505_unary_comparison_tests.ps1, tests\diagnostics\run_s506_float_to_integer_tests.ps1, tests\diagnostics\run_s508_fix_type_tests.ps1, tests\diagnostics\run_s510_mir_f32_rounding_tests.ps1, tests\diagnostics\run_union_overlay_tests.ps1, tests\dosya_tutamaci\run_dosya_tutamaci_tests.ps1, tests\exceptions_cross\run_exceptions_cross_tests.ps1, tests\float_text\run_float_text_tests.ps1, tests\iterators\run_iterator_tests.ps1, tests\kv_kapanis\run_kv_kapanis_tests.ps1, tests\language_guards\run_language_guard_tests.ps1, tests\libraries\uxgsl\run_uxgsl_smoke_tests.ps1, tests\libraries\uxraylib\run_uxraylib_smoke_tests.ps1, tests\libraries\uxsdl3\run_uxsdl3_smoke_tests.ps1, tests\library_type_contract\run_library_type_tests.ps1, tests\memory_model\run_memory_model_tests.ps1, tests\memoryref_model\run_memoryref_model_tests.ps1, tests\native_nul\run_native_nul_tests.ps1, tests\numeric_model\run_numeric_model_tests.ps1, tests\oop_class_arrays\run_oop_class_array_tests.ps1, tests\oop_multidim\run_oop_multidim_tests.ps1, tests\oop_parity\run_oop_parity_tests.ps1, tests\oop_redim\run_oop_redim_tests.ps1, tests\oop_remaining\run_oop_remaining_tests.ps1, tests\output_isolation\run_output_isolation_tests.ps1, tests\preprocessor_effects\run_effects_tests.ps1, tests\preprocessor_unified\run_unified_tests.ps1, tests\print_zones\run_print_zone_tests.ps1, tests\program_end\run_program_end_tests.ps1, tests\routine_scope\run_routine_scope_tests.ps1, tests\sadd_model\run_sadd_model_tests.ps1, tests\string_lifetime\run_string_lifetime_tests.ps1, tests\task_legacy_v2\run_task_legacy_v2_tests.ps1, tests\task_model\run_task_model_tests.ps1, tests\task_native\run_task_native_tests.ps1, tests\task_native\run_task_nul_tests.ps1, tests\task_provider_completion\run_aggregate_assign_tests.ps1, tests\task_provider_completion\run_argument_sync_tests.ps1, tests\task_provider_completion\run_loader_and_incdec_tests.ps1, tests\task_provider_completion\run_lvalue_sync_tests.ps1, tests\task_provider_completion\run_scalar_sync_tests.ps1, tests\task_sync\run_task_sync_tests.ps1, tests\turkce_ad\run_turkce_ad_tests.ps1, tests\typed_task_routines\run_typed_task_tests.ps1, tests\wasm_model\run_wasm_model_tests.ps1, tests\wasm_types\run_wasm_types_tests.ps1, tests\x86_emeklilik\run_x86_emeklilik_tests.ps1, uxb_wrap.cmd.

### `tests/sadd_model/run_sadd_model_tests.ps1`

S-076 SADD (string verisinin gercek adresi): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64'te calistirilir; ciktilar expected/<ad>.txt ile birebir karsilastirilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\sadd_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/string_lifetime/run_string_lifetime_tests.ps1`

S-157: STRING degiskeni / dizi elemani / TYPE ve CLASS alani / yerel donus metni, kendisinden sonraki metin islemlerinde ezilmemeli. Dort motorlu karsilastirma task_model kosucusuyla ayni.

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\task_model\run_task_model_tests.ps1, .\bin\uxb.exe.

### `tests/struct_union_uxcapi/build_testlib.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \ucrt64\bin\gcc.exe, \ucrt64\bin\x86_64-w64-mingw32-gcc.exe.

### `tests/struct_union_uxcapi/run_struct_union_uxcapi_smoke.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$BuildCompiler
[switch]$SkipRuntimeSmoke
[string]$Uxb = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, build_64.bat, build_testlib.bat, compiler\uxb.exe, runtime_ext\uxcapi\build_uxcapi_dll.bat, uxb.exe, validate_mir_records.py, verify_patch.py.

### `tests/struct_union_uxcapi/validate_mir_records.py`

!/usr/bin/env python3

```text
positional: sys.argv[1]
```
Rutinler: require, fields.
Çağrı/yol başvuruları: yok.

### `tests/struct_union_uxcapi/verify_patch.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', type=Path, required=True)
```
Rutinler: main.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261028/s288/check_registry_coverage.py`

S-288: Ensure builtin call names newly added to runtime/type rules cannot bypass routine-name gate.

```text
positional: sys.argv[1]
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261028/span_interval_reference_test.py`

S056/S094 unsigned interval model smoke tests. Runs on Python as a reference for the intended interval predicate. Does not compile or execute FreeBASIC/uXBasic.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: classify, test_cases.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261028/tur4/s111_many_bounds_generator.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261029/package10/tests/tur10/verify_source_contract.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261029/package11/tests/tur10/verify_source_contract.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261029/package11/tests/tur11/verify_embedded_parity.py`

Recover embedded FreeBASIC JS string literal projection and verify byte parity.

```text
positional: sys.argv[1]
positional: sys.argv[2]
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/submitted_20261029/package13/tests/tur10/verify_source_contract.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tests/support/controlled_process.ps1`

Shared library-test process boundary: isolated working directory, exit code, bounded execution, and complete redirected output. No workspace cleanup. The all-model runner can supply its own temporary batch wrapper.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: Invoke-UxbControlledProcess, Remove-UxbOwnedTemporaryDirectory.
Çağrı/yol başvuruları: yok.

### `tests/support/run_six_engine_parity.py`

Real executions, exact oracle, exit codes and hashes for six compiler engines.  Each compiler invocation gets a fresh directory. No rejected feature, missing artifact or stale output is counted as a successful positive-language probe. Outputs are kept as evidence; the runner deletes no workspace files.

```text
parser.add_argument('--compiler', required=True, type=Path)
parser.add_argument('--suite', required=True, type=Path)
parser.add_argument('--out', required=True, type=Path)
parser.add_argument('--timeout', type=int, default=90)
parser.add_argument('--engines', nargs='+', choices=ENGINES, default=ENGINES)
parser.add_argument('--only', nargs='*')
```
Rutinler: digest, normalized, run, main.
Çağrı/yol başvuruları: program.exe, tools/wabt/bin/wat2wasm.exe.

### `tests/surface_gaps/run_surface_gap_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = (Join-Path $PSScriptRoot '..\..\bin\uxb.exe')
[string]$ReportRoot = (Join-Path $PSScriptRoot '..\..\reports\surface_gaps')
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\..\bin\uxb.exe.

### `tests/task_legacy_v2/run_task_legacy_v2_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_model/run_task_model_tests.ps1`

S-030 TASK/SPAWN/TASKGROUP modeli: her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64 motorlarinda calistirilir. expected/_engines.txt  : motor basina durum, "MOTOR=run" veya "MOTOR=reject" (S-030 faz durumu; tek yerde tutulur). run    -> cikti expected/<ad>.txt ile birebir ayni olmali (ya da <ad>.contains.txt'deki o motor satirini icermeli). reject -> motor TEMIZ reddetmeli: sonuc "ERROR:" icermeli ve "Execution completed successfully" icermemeli (sessiz yanlis sonuc yasak). Red metni kasten sabitlenmez; acik red iletileri Faz 1B/2'de eklenince _engines.txt "MOTOR=reject:<metin>" bicimiyle o metni zorunlu kilabilir. expected/<ad>.contains.txt : "MOTOR=alt dize" ya da "ALL=alt d

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\task_model"
```
Rutinler: Norm, Invoke-UxbWithInput.
Çağrı/yol başvuruları: .\bin\uxb.exe, eng.exe.

### `tests/task_native/run_task_native_tests.ps1`

S-030 Faz 2A: YALNIZ native x64'te anlamli gercek eszamanlilik testleri (AST/MIR senkron referansta bu programlar ya sonsuza kadar doner -- iptal testi -- ya da zamanlama anlamini tasimaz). Her program bir kez derlenir, sonra isci sayisi 1, 2 ve AUTO (UXB_TASK_WORKERS) ile $Repeat kez calistirilir; zamanlamaya bagli hatalar tekrarla yakalanir. Zaman asimi = takilma = FAIL. expected/<ad>.txt: birebir cikti. native_print_lines ozel denetim: her satir tek parca.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\task_native"
[int]$Repeat = 3
[int]$TimeoutSec = 60
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe, base.exe.

### `tests/task_native/run_task_nul_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_provider_completion/run_aggregate_assign_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_provider_completion/run_argument_sync_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_provider_completion/run_ffi_contract.py`

Exercise native FFI return types, ten arguments and STRPTR after task adapter changes.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
```
Rutinler: main.
Çağrı/yol başvuruları: /msys64/ucrt64/bin/gcc.exe, sys.exe, tests/turkce_ad/run_tests.py.

### `tests/task_provider_completion/run_loader_and_incdec_tests.ps1`

Publish one combined count for INCDEC and native loader acceptance.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe, run_loader_contract.py.

### `tests/task_provider_completion/run_loader_contract.py`

Real package execution and fault injection; never modify installed DLLs.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--baseline')
parser.add_argument('--runtime-dir', help='Native runtime package; defaults to UXB_NATIVE_RUNTIME_DIR, then the compiler directory')
parser.add_argument('--output', required=True)
```
Rutinler: digest, run, main, build.
Çağrı/yol başvuruları: cmd.exe, link_program.bat, uxb_loader_probe.exe.

### `tests/task_provider_completion/run_lvalue_sync_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_provider_completion/run_native_proofs.py`

Prove OS-worker execution and bounded two-worker overlap, not just JOIN output.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--repeat', type=int, default=2)
```
Rutinler: normalized, main, run.
Çağrı/yol başvuruları: program.exe.

### `tests/task_provider_completion/run_scalar_sync_tests.ps1`

The aggregate runner reads the first Toplam line. Only publish the

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/task_sync/run_task_sync_tests.ps1`

S-146 Model D (otomatik senkron, LOCK, MUTEX, ATOMIC, UNSAFE): her test AST, canonical-MIR, native x64 (bld) ve legacy AST-x64 motorlarinda calistirilir (koşucu tests/task_model ile ayni). expected/_engines.txt  : motor basina durum, "MOTOR=run" veya "MOTOR=reject" (S-030 faz durumu; tek yerde tutulur). run    -> cikti expected/<ad>.txt ile birebir ayni olmali (ya da <ad>.contains.txt'deki o motor satirini icermeli). reject -> motor TEMIZ reddetmeli: sonuc "ERROR:" icermeli ve "Execution completed successfully" icermemeli (sessiz yanlis sonuc yasak). Red metni kasten sabitlenmez; acik red iletileri Faz 1B/2'de eklenince _engines.txt "MOTOR=reject:<metin>" bicimiyle o metni zorunlu kilabilir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\task_sync"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe, eng.exe.

### `tests/timer_tanimi/run_timer_tanimi_tests.ps1`

S-624: TIMER = yerel gece yarisindan beri gecen saniye (F64, kesirli), altı yolun hepsinde AYNI tanim. Her program AST, MIR, native x64 (bld), eski AST-x64, JS ve WASM'da kosulur (expected\<ad>.engines.txt ile daraltilir); cikti expected\<ad>.txt ile birebir karsilastirilir. Programlar deterministiktir: TIMER'in kendisini degil aralik/kesir/fark ozelliklerini yazdirir (-1 = dogru). Native yollar __uxb_rt_timer_f64 isteyen bir uxb_runtime.dll ister: UXB_NATIVE_RUNTIME_DIR ortam degiskeni (yalitilmis calisma ani dizini) oldugu gibi derleyiciye aktarilir. Her program kendi gecici calisma dizininde kosar (out\ klasorunu paylasan koşucularla cakismaz); her yol mutlaktir.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$Filtre = ""
```
Rutinler: Norm, Kos, Motor.
Çağrı/yol başvuruları: .\bin\uxb.exe, m.exe, tools\wabt\bin\wat2wasm.exe.

### `tests/trace/trace_smoke_compile.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--debug
--hook-trace
--layer-timing-json-out
--session-live-json-out
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, build\uxb_main_64.exe, compiler\scripts\build_uxb_main_64.bat.

### `tests/turkce_ad/run_tests.py`

Run real programs on six engines; retain commands, exits and raw results.

```text
parser.add_argument('--uxb', required=True)
parser.add_argument('--output')
parser.add_argument('--test-root', default=str(HERE))
parser.add_argument('--only', nargs='*')
parser.add_argument('--engines', nargs='*', choices=ENGINES)
parser.add_argument('--jobs', type=int, default=1, choices=range(1, 9))
parser.add_argument('--timeout', type=int, default=90, help='Per-process time limit in seconds; use a larger budget for loaded interpreter runs')
parser.add_argument('--resume', action='store_true')
parser.add_argument('--native-runtime-dir', help='Stage an isolated candidate DLL next to each generated native executable')
artifacts.add_argument('--temp-builds', dest='temp_builds', action='store_true', default=True, help='Default: remove all compiler/program artifacts after recording raw results and hashes')
artifacts.add_argument('--keep-builds', dest='temp_builds', action='store_false', help='Retain diagnostic artifacts under build/test_outputs; never deploy binaries into reports')
parser.add_argument('--resume-sha256', help='Recorded compiler hash for recovering a run predating identity files')
```
Rutinler: norm, raw_stdout, main, run, run_case, partial.
Çağrı/yol başvuruları: program.exe, tools/wabt/bin/wat2wasm.exe.

### `tests/turkce_ad/run_turkce_ad_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, run_tests.py.

### `tests/typed_task_routines/run_typed_task_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\typed_task_routines"
[string]$ExpectedRoot = ""
[string]$ReportRoot = ""
[switch]$SkipAst
[switch]$SkipMir
[switch]$EmitMirX64
[switch]$UpdateExpected
```
Rutinler: Add-Result, Get-NormalizedText, Get-NormalizedFile, Format-Mismatch, Invoke-Uxb, Test-PositiveBackend.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tests/uxaimath/build_and_run_uxaimath_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxaimath_dll_probe.exe, uxb\runtime_ext\uxaimath\build_uxaimath_dll.bat, uxb\runtime_ext\uxaimath\build_uxaimath_fallback_dll.bat.

### `tests/uxbasic_hamle1_chain_patch/uxbasic_hamle1_chain_patch/tools/tests/run_hamle1_chain_ast.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--compiler
--source-root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \tools\tests\test_hamle1_chain_ast.py, path\to\uxbasic.exe, tools\tests\run_hamle1_chain_ast.bat.

### `tests/uxbasic_hamle1_chain_patch/uxbasic_hamle1_chain_patch/tools/tests/run_hamle1_chain_ast.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Compiler = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\tests\test_hamle1_chain_ast.py.

### `tests/uxbasic_hamle1_chain_patch/uxbasic_hamle1_chain_patch/tools/tests/test_hamle1_chain_ast.py`

HAMLE-1 zincirli nesne/metot parser testi.  Kullanım 1 - sadece yama kaynak kontrolü:     python tools/tests/test_hamle1_chain_ast.py --source-root .  Kullanım 2 - derleyici ile parse-only AST JSON üretip kontrol:     python tools/tests/test_hamle1_chain_ast.py --source-root . --compiler build/uxbasic.exe  Beklenen parser sözleşmesi:     obj.child.method()      -> CALL_EXPR value=obj.child.method, left=FIELD_EXPR(obj.child)     factory().method()      -> CALL_EXPR value=factory.method,   left=CALL_EXPR(factory)     obj.method().next()     -> CALL_EXPR value=obj.method.next,  left=CALL_EXPR(obj.method)     a.b.c()                 -> CALL_EXPR value=a.b.c,            left=FIELD_EXPR(a.b)     other.x.y()             -> CALL_EXPR value=other.x.y,        left=FIELD_EXPR(other.x)

```text
ap.add_argument('--source-root', default='.', help='uXBasic kaynak kökü veya yama paket kökü')
ap.add_argument('--compiler', default='', help='uxbasic.exe yolu; verilmezse sadece statik kaynak kontrolü yapılır')
ap.add_argument('--ast-json', default='', help='önceden üretilmiş AST JSON dosyasını doğrula')
```
Rutinler: fail, ok, read_text, static_source_checks, walk, find_call, assert_kind_value, validate_ast_json, run_compiler_parse_only, main.
Çağrı/yol başvuruları: build/uxbasic.exe, tools/tests/test_hamle1_chain_ast.py, uxbasic.exe.

### `tests/uxbasic_hamle2_runtime_chain_patch/tools/tests/run_hamle2_runtime_chain_patch.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--root
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0test_hamle2_runtime_chain_patch.py.

### `tests/uxbasic_hamle2_runtime_chain_patch/tools/tests/run_hamle2_runtime_chain_patch.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: test_hamle2_runtime_chain_patch.py.

### `tests/uxbasic_hamle2_runtime_chain_patch/tools/tests/test_hamle2_runtime_chain_patch.py`

Hamle-2 runtime zincir yama kontrolu.  Kullanim:   python tools/tests/test_hamle2_runtime_chain_patch.py --root .  Bu test derleyici calistirmaz; kaynakta Hamle-2 sozlesmesinin yerlestigini kontrol eder.

```text
ap.add_argument('--root', default='.')
```
Rutinler: main.
Çağrı/yol başvuruları: tools/tests/test_hamle2_runtime_chain_patch.py.

### `tests/uxbasic_hamle3_mir_x64_chain_patch/uxbasic_hamle3_mir_x64_chain_patch/tools/tests/run_hamle3_mir_x64_chain_patch.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\tests\test_hamle3_mir_x64_chain_patch.py.

### `tests/uxbasic_hamle3_mir_x64_chain_patch/uxbasic_hamle3_mir_x64_chain_patch/tools/tests/run_hamle3_mir_x64_chain_patch.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Compiler = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools/tests/test_hamle3_mir_x64_chain_patch.py.

### `tests/uxbasic_hamle3_mir_x64_chain_patch/uxbasic_hamle3_mir_x64_chain_patch/tools/tests/test_hamle3_mir_x64_chain_patch.py`

Hamle-3 statik yama kontrolü. Derleyici verilirse sadece komut örneği gösterir; asıl kontrol kaynak dosya sözleşmesidir.

```text
ap.add_argument('--compiler', default='', help='İsteğe bağlı uxbasic derleyici yolu')
```
Rutinler: must_contain, main.
Çağrı/yol başvuruları: yok.

### `tests/uxbasic_hamle4_chain_tests/uxbasic_hamle4_chain_tests/tools/tests/hamle4_chain_runner.py`

Hamle-4 uXBasic zincirli nesne/metot testi.  Bu runner iki modda calisir: 1) Kaynak sozlesme testi: Hamle 1-2-3 yama izlerini kaynakta arar. 2) Derleyici/exe testi: uxb/uxbasic exe verilirse AST, runtime, MIR ve x64 ciktilarini uretip kontrol eder.  Kullanim:     python tools/tests/hamle4_chain_runner.py --root .     python tools/tests/hamle4_chain_runner.py --root . --uxb .\bin\uxb.exe     python tools/tests/hamle4_chain_runner.py --root . --uxb .\bin\uxb.exe --require-compiler

```text
parser.add_argument('--root', default='.', help='uXBasic kaynak kok klasoru')
parser.add_argument('--uxb', default=None, help='uxb/uxbasic executable yolu')
parser.add_argument('--require-compiler', action='store_true', help='Derleyici bulunamazsa SKIP degil FAIL ver')
parser.add_argument('--out', default='reports/hamle4_chain', help='Cikti klasoru')
```
Rutinler: read_text, normalize_lines, find_compiler, run_cmd, contract_tests, recursive_json_text, require_patterns, compiler_ast_test, compiler_runtime_ok_test, compiler_runtime_error_test, compiler_recursion_test, compiler_mir_test, compiler_x64_test, compiler_tests, print_results, main.
Çağrı/yol başvuruları: .\\bin\\uxb.exe, bin/uxb.exe, tools/tests/hamle4_chain_runner.py, uxb.exe, uxbasic.exe.

### `tests/uxbasic_hamle4_chain_tests/uxbasic_hamle4_chain_tests/tools/tests/run_hamle4_chain_tests.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
--require-compiler
--root
--uxb
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \yol\uxb.exe, tools\tests\hamle4_chain_runner.py, tools\tests\run_hamle4_chain_tests.bat.

### `tests/uxbasic_hamle4_chain_tests/uxbasic_hamle4_chain_tests/tools/tests/run_hamle4_chain_tests.ps1`

Hamle-4 zincirli nesne/metot regresyon testi Ornek: .\tools\tests\run_hamle4_chain_tests.ps1 .\tools\tests\run_hamle4_chain_tests.ps1 -UxbExe .\bin\uxb.exe -RequireCompiler

```text
[string]$UxbExe = ""
[string]$Root = (Get-Location).Path
[switch]$RequireCompiler
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\tools\tests\run_hamle4_chain_tests.ps1, tools\tests\hamle4_chain_runner.py.

### `tests/uxclazz_codex1/test_generated_names.py`

User-visible generator contract regressions; independent of compiler binaries.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: rejects, test_case_insensitive_field_duplicate, test_trait_accessor_collides_with_field_accessor, test_readonly_still_conflicts_with_trait_getter, test_duplicate_traits, test_duplicate_classes, test_unknown_derive_is_not_silently_ignored, test_valid_composition_and_readonly_contract, test_repository_sample_remains_valid.
Çağrı/yol başvuruları: spec.loader.exe, tools/uxclazz/uxclazz.py.

### `tests/uxclz/run_uxclz_host_parity.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = ".\bin\uxb.exe"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, uxclz_ast.exe, uxclz_mir.exe.

### `tests/uxcollections/build_and_run_uxcollections_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
--cflags
--libs
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \msys64\ucrt64\bin\pkg-config.exe, \uxcollections_probe.exe, uxb\runtime_ext\uxcollections\build_uxcollections_dll.bat.

### `tests/uxdataframe/build_and_run_uxdataframe_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxdataframe_probe.exe, uxb\runtime_ext\uxdataframe\build_uxdataframe_dll.bat.

### `tests/uxdataset/build_and_run_uxdataset_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxdataset_probe.exe, uxb\runtime_ext\uxdataset\build_uxdataset_dll.bat.

### `tests/uxgraph/build_and_run_uxgraph_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxgraph_dll_probe.exe, uxb\runtime_ext\uxgraph\build_uxgraph_dll.bat, uxb\runtime_ext\uxgraph\build_uxgraph_fallback_dll.bat.

### `tests/uxllama/build_and_run_uxllama_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxllama_dll_probe.exe, uxb\runtime_ext\uxllama\build_uxllama_dll.bat.

### `tests/uxmath/build_and_run_uxmath_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmath_dll_probe.exe, uxb\runtime_ext\uxmath\build_uxmath_dll.bat.

### `tests/uxmathcore/build_and_run_uxmathcore_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmathcore_probe.exe, uxb\runtime_ext\uxmathcore\build_uxmathcore_dll.bat.

### `tests/uxmatrix/build_and_run_uxmatrix_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxmatrix_probe.exe, uxb\runtime_ext\uxmatrix\build_uxmatrix_dll.bat, uxb\runtime_ext\uxmatrix\build_uxmatrix_fallback_dll.bat.

### `tests/uxmatrix/uxmatrix_complete_probe.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: matrix, remember, values, multiply, transpose, assert_close, assert_matrix_close.
Çağrı/yol başvuruları: yok.

### `tests/uxnn/build_and_run_uxnn_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxnn_dll_probe.exe, uxb\runtime_ext\uxnn\build_uxnn_dll.bat, uxb\runtime_ext\uxnn\build_uxnn_fallback_dll.bat.

### `tests/uxnn2/build_and_run_uxnn2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, uxb\dist\runtime_ext\uxnn2_dll_probe.exe, uxb\runtime_ext\uxnn2\build_uxnn2_dll.bat.

### `tests/uxnn3/build_and_run_uxnn3_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxnn3_dll_probe.exe, uxb\runtime_ext\uxnn3\build_uxnn3_dll.bat.

### `tests/uxonnx/build_and_run_uxonnx_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxonnx_probe.exe, uxb\runtime_ext\uxonnx\build_uxonnx_dll.bat.

### `tests/uxonnx2/build_and_run_uxonnx2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, uxb\dist\runtime_ext\uxonnx2_probe.exe, uxb\runtime_ext\uxonnx2\build_uxonnx2_dll.bat, uxb\runtime_ext\uxonnx2\fetch_uxonnx2_deps.bat.

### `tests/uxstats/build_and_run_uxstats_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxstats_dll_probe.exe, uxb\runtime_ext\uxstats\build_uxstats_dll.bat.

### `tests/uxstats2/build_and_run_uxstats2_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxstats2_dll_probe.exe, uxb\runtime_ext\uxstats2\build_uxstats2_dll.bat.

### `tests/uxtensor/build_and_run_uxtensor_probe.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \uxtensor_probe.exe, uxb\runtime_ext\uxtensor\build_uxtensor_dll.bat.

### `tests/wasm_model/run_wasm_model_tests.ps1`

WASM/WAT ve JS davranis testleri (S-102: WASM/JS ciktisini GERCEKTEN calistiran guvenilir kosucu). Her program: AST yorumlayici (dil referansi), WASM (uxb wat --emit-wasm -> wat2wasm -> node run_wasm.js) ve JS (uxb jsw -> node p.js) ile calistirilir; ikisi de expected/<ad>.txt ile birebir eslesmeli. run_wasm.js ve ux_wasm_runtime.js her derlemede derleyici tarafindan TAZE uretilir (dist\wasm\ altindaki eski kopyalar kullanilmaz). expected\<ad>.contains.txt: "MOTOR=alt dize" -- o motorun sonucu birebir degil, bu dizeyi ICERMELI (net red iletileri)

```text
[string]$Uxb = ".\bin\uxb.exe"
[string]$TestRoot = ".\tests\wasm_model"
```
Rutinler: Norm.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\tools\wabt\bin\wat2wasm.exe.

### `tests/wasm_types/check_wasm_core.py`

Execute emitted WASM with host text operations disabled (console stays bound).

```text
parser.add_argument('--results', required=True)
parser.add_argument('--output', required=True)
```
Rutinler: main.
Çağrı/yol başvuruları: yok.

### `tests/wasm_types/run_wasm_types_tests.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb='.\bin\uxb.exe'
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: ..\turkce_ad\run_tests.py, .\bin\uxb.exe, \.exe.

### `tests/x86_emeklilik/run_x86_emeklilik_tests.ps1`

S-666 (x86 emeklilik, Asama 3): x86 adi hangi yoldan verilirse verilsin ayni acik emekli iletisi doner. 1) CLI: `x86` fiili, --emit-x86, --target-x86, --target x86|win32|windows32|i386|i686 -> CLI_TARGET_RETIRED (tum fiillerde). Eskiden yalniz `x86` fiili reddediliyor, `run --target-x86` sessizce calisiyor, `bld --target x86` sessizce x64 EXE uretiyordu. 2) Satir ici makine kodu: INLINE("x86"|"x86_32"|"i386"|"win32",...) -> bld hattinda "x86 (32-bit) INLINE blocks are retired". 3) Interop arac zinciri: UXB_TARGET_ARCH=x86... ve INLINE politikasindaki ARCH=x86 -> "retired 32-bit (x86) target". 4) (Asama 4) Arac betikleri: uxb_switchboard.ps1 -Mode build-compiler-x86 / -NativeArch x86 ve Resol

```text
[string]$Uxb = '.\bin\uxb.exe'
```
Rutinler: Check, Run, RunPwsh, CheckCliRetired, CheckBldText.
Çağrı/yol başvuruları: .\bin\uxb.exe, _retired\x86\build_32.bat, build_32.bat, fbc32.exe, main_32.exe, main_64.exe, run_ffi_conv3_native_lanes.ps1, tool_py\tools\control\uxb_switchboard.ps1, tool_py\tools\control\workspace_root_helpers.ps1, tools\run_ffi_conv3_native_lanes.ps1, uxb_switchboard.ps1.

### `tools/analyze_surface_example_gaps.py`

Compare lexer/preprocessor surfaces with existing executable examples.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: lexer_keywords, preprocess_commands, source_files, main.
Çağrı/yol başvuruları: yok.

### `tools/archive_freebasic_c_sources.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string[]]$EntryPoint = @("src\wrappers\uxb_main_wrapper.bas")
[string]$ArchiveRoot = "build\freebasic_c_sources"
[string]$Fbc = "tools\FreeBASIC-1.10.1-win64\fbc64.exe"
[switch]$ForceRegenerate
```
Rutinler: Get-RelativePathCompat.
Çağrı/yol başvuruları: tools\FreeBASIC-1.10.1-win64\fbc64.exe.

### `tools/audit/uxb_ast_contract_audit.py`

Step 2 AST contract audit for uXBasic.  Bu araç sadece denetim/rapor üretir. Ana compiler davranışı FreeBASIC kod tabanındadır.

```text
positional: sys.argv[1:]
```
Rutinler: root, text, rel, collect_contract_nodes, nearest_function, collect_parser_nodes, group_for, kind_for, layer_status, mir_lowering_status, mir_verify_status, wasm_status, final_decision, build_matrix, write_csv, write_markdown, write_ast_docs, write_outputs, gate, main.
Çağrı/yol başvuruları: tools/uxb_js_transpiler_wasm_backend.py.

### `tools/audit/uxb_ast_contract_build_matrix.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_ast_contract_collect_contract_nodes.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_ast_contract_collect_handlers.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_ast_contract_collect_parser_nodes.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_ast_contract_fake_status_scan.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_ast_contract_gate.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/audit/uxb_step1_surface_core.py`

Step 1 surface matrix builder and gates for uXBasic.

```text
positional: sys.argv[1:]
```
Rutinler: find_project_root, read_text, iter_layer_files, extract_lexer_keywords, classify_keyword_group, classify_keyword_kind, example_for_name, rel, layer_texts, name_patterns, has_evidence, evidence_file, keyword_rows, operator_rows, extension_rows, library_rows, base_row, apply_layer_statuses, mark_compile_time, execution_present, first_source, infer_ast_node, infer_mir_opcode, library_example, build_surface_rows, write_csv, read_csv, write_matrix_markdown, write_docs, extension_doc, write_library_matrix, wasm_doc, write_reports, write_fake_status_scan, build_all, validate_rows, scan_disallowed, write_gate_report, run_gate, main.
Çağrı/yol başvuruları: tools/uxb_js_transpiler_wasm_backend.py.

### `tools/benchmark_selected_execs.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[int]$Iterations = 30
[string]$OutCsv = "reports/perf_selected_execs.csv"
```
Rutinler: Get-P95, Run-One.
Çağrı/yol başvuruları: tests/run_class_method_dispatch_exec_ast_64.exe, tests/run_collection_engine_exec_64.exe, tests/run_percent_preprocess_exec_64.exe.

### `tools/claude/uxb_build.ps1`

uXBasic derleyicisini (FreeBASIC) bin\uxb_<Name>.exe olarak derler. .\tools\claude\uxb_build.ps1 -Name claude1_f2g Hedef exe o anda calisiyorsa (baska bir test/oturum kullaniyor) DERLEMEZ: 2026-09-27'de ayni exe'ye iki derleme ayni anda yazdi. Cikti: "rc=<kod>" + ilk 15 hata satiri. bin\uxb.exe (Codex'in ana derleyicisi) -Name ile hedeflenemez. Kaynak kok (src/wrappers iceren). Bos = bu deponun canli agaci. Ozel calisma kopyasindan derlemek icin (Codex'in canli agac hash dogrulamasini bozmamak icin): -SourceRoot <kopya>. Cikti HEP bu deponun bin\ klasorune yazilir.

```text
[Parameter(Mandatory = $true)][ValidatePattern('^[A-Za-z0-9_]+$')][string]$Name
[string]$SourceRoot = ''
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\tools\claude\uxb_build.ps1, Name.exe, bin\uxb.exe, fbc64.exe.

### `tools/claude/uxb_regression.ps1`

Model test paketlerini (tests\run_all_model_tests.ps1) koşar; sonucu build\claude_reports\ altina yazar ve yalniz ozet + dusen kontrolleri basar. .\tools\claude\uxb_regression.ps1 -Uxb .\bin\uxb_claude1_f2f.exe [-Only task_sync,routine_scope] Uzun surer (tam kosu ~1 saat): arka planda baslatilmasi onerilir. Dusen bir testin bu degisiklikten mi yoksa onceden mi geldigini ayirmak icin: .\tools\claude\uxb_run3.ps1 -File <test> -Uxb <eski exe> ile karsilastir.

```text
[string]$Uxb = '.\bin\uxb.exe'
[string[]]$Only = @()
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\bin\uxb_claude1_f2f.exe, .\tests\run_all_model_tests.ps1, .\tools\claude\uxb_regression.ps1, .\tools\claude\uxb_run3.ps1, tests\run_all_model_tests.ps1.

### `tools/claude/uxb_run3.ps1`

Bir uXBasic programini AST, canonical-MIR ve native x64 (bld) motorlarinda calistirir, ciktilari tek satirda yan yana verir. -Legacy ile eski AST-x64 motoru da eklenir. .\tools\claude\uxb_run3.ps1 -File build\deneme.bas -Uxb .\bin\uxb_claude1_f2f.exe [-NativeRepeat 3] [-Workers 2] [-Legacy] Satirlar " | " ile birlestirilir; INFO/WARN satirlari atilir. Native derleme klasoru %TEMP% altinda acilir ve silinir.

```text
[Parameter(Mandatory = $true)][string]$File
[string]$Uxb = '.\bin\uxb.exe'
[int]$NativeRepeat = 1
[string]$Workers = ''
[switch]$Legacy
```
Rutinler: Clean.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\bin\uxb_claude1_f2f.exe, .\tools\claude\uxb_run3.ps1, program.exe.

### `tools/control/apply_adim44_remaining_gaps.py`

Idempotently repair the ADIM36/44 negative-test fail-close runner.  The historical copy of this tool was truncated. This implementation either verifies that the active runner already contains the ADIM44 contract or copies the complete fixed runner retained beside it.

```text
ap.add_argument('--repo', default='.')
ap.add_argument('--patch-root', default='patch_files')
```
Rutinler: find_root, main.
Çağrı/yol başvuruları: tool_py/tools/control/adim36_full_surface_runner_FIXED.py, tool_py/tools/control/uxb_adim36_full_surface_runner.py, tools/control/adim36_full_surface_runner_FIXED.py, tools/control/uxb_adim36_full_surface_runner.py.

### `tools/control/uxb_surface_lifecycle_matrix.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--strict', action='store_true')
```
Rutinler: load_core, ensure_dir, write_csv, status_to_route, runtime_route, compile_time_route, lifecycle_route, matrix_row, find_blockers, target_backend_blockers, test_plan, gate_markdown, main.
Çağrı/yol başvuruları: spec.loader.exe, uxb_step1_surface_core.py.

### `tools/diagnostics/verify_final_ffi_quickjs_release.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
ap.add_argument('--root', required=True)
ap.add_argument('--json-out')
```
Rutinler: main, emit, add, read.
Çağrı/yol başvuruları: compiler/scripts/run_final_ffi_quickjs_release_gate.ps1, runtime_ext/uxffi/build_uxffi_dll.bat, tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py, tests/libraries/uxjsruntime/test_generated_js_e2e.py, tools/release/package_uxbasic_distribution_final.ps1.

### `tools/diagnostics/verify_post_quickjs_patch.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
parser.add_argument('--root', required=True)
parser.add_argument('--json-out')
```
Rutinler: main, check.
Çağrı/yol başvuruları: Move-StaleNestedTrees.ps1, runtime_ext/uxffi/build_uxffi_dll.bat, tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py, tests/libraries/uxjsruntime/test_generated_js_e2e.py.

### `tools/docs/audit_pck_documents.py`

Inventory PCK documents and flag legacy claims without rewriting archives.

```text
parser.add_argument('--root', default='.')
parser.add_argument('--output', default='reports/pck_document_audit_20260727.json')
```
Rutinler: sha256, main.
Çağrı/yol başvuruları: yok.

### `tools/docs/generate_cli_reference_table.py`

Generate the complete CLI reference table from the canonical registry export.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: clean.
Çağrı/yol başvuruları: .\bin\uxb.exe.

### `tools/extract_matrix_psrt_nonok.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$InputPath = "reports/uxbasic_operasyonel_eksiklik_matrisi.md"
[string]$OutputCsv = "reports/matrix_psrt_nonok_inventory.csv"
[switch]$Summary
```
Rutinler: Resolve-RepoPath, Normalize-Token, Split-MarkdownRow, Test-SeparatorRow, Get-SectionFamily, Get-HeaderMap, Get-Cell, Normalize-Status, Get-Severity, Get-TrackedStatus.
Çağrı/yol başvuruları: yok.

### `tools/forensic_matrix_full_scan.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: Get-Tokens, Get-FeatureProbePatterns.
Çağrı/yol başvuruları: yok.

### `tools/generate_missing_library_surface_tests.py`

Generate parser/semantic examples only for library APIs absent from tests.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: dummy_for, declarations, main.
Çağrı/yol başvuruları: yok.

### `tools/gsl/generate_gsl_export_catalog.py`

Build and verify a complete installed-GSL export catalog for UXGSL.  The catalog is generated from the exact PE DLLs staged by MSYS2, rather than from a hand-maintained list. It therefore covers every callable GSL/CBlas export in the installed binary, including APIs which require callbacks or aggregate ABI descriptors and are invoked through uxcapi.

```text
parser.add_argument('--objdump', required=True, type=Path)
parser.add_argument('--gsl-dll', required=True, type=Path)
parser.add_argument('--cblas-dll', required=True, type=Path)
parser.add_argument('--out', required=True, type=Path)
parser.add_argument('--verify', action='store_true')
```
Rutinler: exports_from_objdump, group_for, verify_loaded_exports, main.
Çağrı/yol başvuruları: yok.

### `tools/gsl/generate_gsl_header_bindings.py`

Generate auditable UXGSL metadata and checked scalar wrappers from GSL headers.  This deliberately avoids pretending that every C declaration is equally safe. It inventories every public GSL declaration, then generates wrappers only when the header proves a scalar function has a matching ``*_e`` result API.  Those wrappers preserve the UXGSL status contract instead of bypassing GSL errors.

```text
parser.add_argument('--headers', required=True, type=Path)
parser.add_argument('--export-catalog', required=True, type=Path)
parser.add_argument('--metadata-out', required=True, type=Path)
parser.add_argument('--c-include-out', required=True, type=Path)
parser.add_argument('--basic-include-out', required=True, type=Path)
parser.add_argument('--basic-module-dir', required=True, type=Path)
parser.add_argument('--module-header-dir', required=True, type=Path)
parser.add_argument('--header-include-out', required=True, type=Path)
```
Rutinler: squash, strip_source, top_level_statements, split_top_level, normalize_type, parse_argument, canonical_type, scalar_kind, basic_suffix, basic_case_tag, c_arguments, c_call_arguments, basic_arguments, parse_headers, export_names, checked_scalar_wrappers, emit_c_include, basic_function_lines, emit_basic_modules, emit_basic_include, emit_header_include, main.
Çağrı/yol başvuruları: tools/gsl/generate_gsl_header_bindings.py.

### `tools/js_runtime/generate_js_runtime_fbs.py`

!/usr/bin/env python3

```text
ap.add_argument('--root', default='.')
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools/js_runtime/generate_js_runtime_fbs.py.

### `tools/kitap/arac_dogrula.py`

Kılavuzdaki ARAÇ örneklerini (betikler) çalıştırır ve '#=' ile yazılmış beklenen çıktıyla karşılaştırır.  Örnek dosya: tools/kitap/kilavuz_v2/arac_ornekleri/<grup>/<ad>.py (ya da .ps1, .js)     # KONU: ...      # KOMUTLAR: ...      # ACIKLAMA: ...     #= beklenen çıktının 1. satırı  (.py/.ps1 için '#=', .js için '//=') Betik proje kökünden çalıştırılır; derleyici yolu UXB_EXE ortam değişkeniyle verilir. Sonuç: docs/kitaplar/_ortak/arac_sonuclari.json Kullanım: python tools/kitap/arac_dogrula.py [--uxb bin\uxb_kilavuz_20261007.exe] [--grup meta] [--ad ast_api_belgesi]

```text
ap.add_argument('--uxb', default=os.path.join(KOK, 'bin', 'uxb_kilavuz_20261007.exe'))
ap.add_argument('--grup')
ap.add_argument('--ad')
ap.add_argument('--sonuc', default=SONUC)
```
Rutinler: oku, calistir, main.
Çağrı/yol başvuruları: .py/.ps1, bin\\uxb_kilavuz_20261007.exe, sys.exe, tools/kitap/arac_dogrula.py, uxb_kilavuz_20261007.exe.

### `tools/kitap/dil_tanimi_birlestir.py`

uXBasic Dil Tanımı birleştirici.  docs/kitaplar/_ortak/dil_tanimi/alanlar/<alan>/bolum.md bölümlerini sırayla tek belgeye (docs/kitaplar/UXBASIC_DIL_TANIMI.md) birleştirir ve ekleri ogeler.json / sonuc.json / yüzey envanterlerinden MEKANİK olarak üretir (elle yazılmaz, uydurulamaz):    Ek A  Uygunluk tablosu   — her öğe: karar, AST/MIR/x64 durumu, örnek, sorun numaraları   Ek B  Karar bekleyenler  — ÖNERİ ve KARAR GEREKİYOR öğeleri (Mete'nin onayı için)   Ek C  Uyum hataları      — bölümlerin bulduğu sorunlar (SORUN_TAKIP numaraları + yeni bulgular)   Ek D  Kütüphane imza kataloğu — kutuphane_yuzeyi.json'dan 46 kütüphanenin tüm fonksiyon/sub imzaları   Ek E  Kapsam denetimi    — lexer anahtar sözcükleri, yerleşik adlar ve kütüphanelerden belgede                              hiç geçmeyenler (boş değilse belge eksiktir)  Kullanım: python tools/kitap/dil_tanimi_birlestir.py [--denetim-json <yol>] Çıkış kodu: 0 = kapsam tam, 3 = kapsam eksiği var (Ek E dolu), 2 = bölüm/JSON hatası.

```text
ap.add_argument('--denetim-json', help="workflow denetim özetlerinin JSON'u (isteğe bağlı, Ek C'ye eklenir)")
```
Rutinler: oku_json, alan_listesi, bolum_basligi, durum_hucresi, md_kacis, normal_ad, main, geciyor.
Çağrı/yol başvuruları: tools/kitap/dil_tanimi_birlestir.py, tools/kitap/yuzey_tara.py.

### `tools/kitap/dis_danis.py`

Dış yapay zekâ (Kimi / Gemini / ChatGPT) ile belge denetimi.  Bir denetim isteğini (Markdown) ve ek dosyaları (satır numaralı TAM metin) sırayla verilen sağlayıcılara sorar; ilk başarılı cevabı yapılandırılmış JSON olarak kaydeder. Harita doldurucunun istemcisini, kotasını ve anahtar dosyasını kullanır (UxbRAG\UXB_HYBRID_RAG_V4_YORUMLU_JSON\tools\uxb_harita_doldur.py) — günlük sınırlar ortaktır ve aşılmaz. Diskteki hiçbir kaynağı değiştirmez.    python tools/kitap/dis_danis.py --istek istek.md --ek docs/kitaplar/_ortak/dil_tanimi/alanlar/05_ifadeler/bolum.md          --ek src/parser/parser/parser_expr.fbs --saglayici kimi,gemini2,gemini --cikti cevap.json  Çıkış kodu: 0 cevap alındı, 1 hiçbir sağlayıcı cevap vermedi (sebep cikti dosyasında ve ekranda).

```text
ap.add_argument('--istek', required=True, help='Denetim görevini anlatan Markdown dosyası')
ap.add_argument('--ek', action='append', default=[], help='İsteğe eklenecek dosya (birden çok)')
ap.add_argument('--saglayici', default='kimi,gemini2,gemini', help='Sırayla denenecek sağlayıcılar')
ap.add_argument('--cikti', required=True, help='Cevabın yazılacağı JSON dosyası')
ap.add_argument('--max-token', type=int, default=16000)
```
Rutinler: numarali, main.
Çağrı/yol başvuruları: UxbRAG\\UXB_HYBRID_RAG_V4_YORUMLU_JSON\\tools\\uxb_harita_doldur.py, tools/kitap/dis_danis.py.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/kendi_dll.py`

KONU: Kendi C kütüphanenizi derleyip uXBasic'ten çağırmak (üç yerel motorda aynı sonuç) KOMUTLAR: gcc -shared · CALL(DLL) · VARPTR · uxb run · uxb bld ACIKLAMA: C ile küçük bir DLL yazılıp derlenir; uXBasic programı onu CALL(DLL, ...) ile çağırır (tamsayı, ondalıklı, metin ve dizi göstericisi). Aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır. DLL adı yalnız dosya adıdır; DLL, programın çalıştığı klasörde bulunmalıdır. = topla = 5 = harf = 3 = kare = 2.25 = ortalama = 3 = buyuk = 5000000000 = motorlar ayni: evet (AST, MIR, x64)

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, p.exe, uxb.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/uxbdll_ile_dll.py`

KONU: uXBasic kodunu DLL ürününe dönüştürmek (uxbdll aracı) ve o DLL'i uXBasic'ten çağırmak KOMUTLAR: uxb bld --x64-mode MIR · tools/uxbdll/uxbdll.py · CALL(DLL) · INCLUDE · CLASS · DELETE ACIKLAMA: examples/uxbdll/uxoop_module.uxb, iki sınıf (Counter, Dog:Animal) ve dışarıya açılan düz köprü işlevleri içerir. Önce derleyici bu modülü MIR yolundan x64 yapıtlarına (program.asm, obj, bağlama dosyası) derler. Sonra uxbdll aracı, manifestte (uxoop_module.uxdll.json) sayılan işlevleri DLL'e dışa aktarır, bir .def dosyası, bir uXBasic sarmalayıcısı (.bas) ve dışa aktarım denetimi üretir. Son olarak ayrı bir uXBasic programı sarmalayıcıyı INCLUDE eder ve DLL'in içindeki nesneleri (sayaç, köpek) yar

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari, ileri.
Çağrı/yol başvuruları: p.exe, sys.exe, tools/uxbdll/uxbdll.py, uxb.exe, uxbdll.py.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/uxclazz_uretici.py`

KONU: UXClazz kaynak üreticisi: CLAZZ bildiriminden sınıf kodu üretmek KOMUTLAR: tools/uxclazz/uxclazz.py · CLAZZ DATA · DERIVE EQ, HASH, CLONE, TOSTRING · uxb run · uxb bld ACIKLAMA: UXClazz derleyicinin bir parçası değil, derleyiciden önce çalışan bir Python aracıdır: .uxclz dosyasındaki CLAZZ bildirimini okur ve normal uXBasic CLASS koduna (kurucu, Get/Set metotları, Equals, MAGIC HASH/CLONE/TOSTRING) dönüştürür. Bu betik küçük bir CLAZZ DATA bildirimi yazar, aracı çalıştırır, çıktının başına/sonuna bir MAIN ekler ve üretilen sınıfı AST, MIR ve x64 motorlarında çalıştırıp çıktıları karşılaştırır. Üretici bugünkü derleyiciyle iki yerde uyuşmaz: farklı tipli alanlar için yazdığı Set<Alan>(v

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari.
Çağrı/yol başvuruları: p.exe, sys.exe, tools/uxclazz/uxclazz.py, uxb.exe, uxclazz.py.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/wat_el_yazisi_uxwasmrt.py`

KONU: Elle yazılmış WAT modülünü wat2wasm ile derleyip uxwasmrt (wasmtime) üzerinden uXBasic'ten çağırmak KOMUTLAR: wat2wasm · uxwasmrt.WasmOpenFile · WasmCallI32_1 · WasmCallI32_2 · WasmLastError · uxb wat --emit-wasm · uxb run · uxb bld ACIKLAMA: Üç tamsayı işlevi (EBOB, FIB, COLLATZ) WebAssembly metin biçiminde (WAT) elle yazılır, wat2wasm ile ikiliye çevrilir ve uXBasic programı uxwasmrt ile yükleyip çağırır. Aynı algoritmalar uXBasic'te de yazılmıştır; program iki sonucu 1600 + 41 girdide karşılaştırır. İkinci bölüm bir sınırı gösterir: uXBasic'in kendi ürettiği WASM modülü her zaman dört "ux" içe aktarması taşır ve uxwasmrt (yalnız çekirdek i32 modülleri) onu açıkça reddeder (G-WASM-10

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari.
Çağrı/yol başvuruları: istemci.exe, uxb.exe, wat2wasm.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/yerel_http_istemci.py`

KONU: uxhttp ile bir HTTP hizmetini kullanmak: GET, POST+JSON, yönlendirme, zaman aşımı ve yeniden deneme (üç yerel motorda aynı sonuç) KOMUTLAR: uxhttp.Open · SetUrl · SetMethod · AddHeader · SetBody · SetTimeout · FollowRedirects · Perform · Status · ResponseText · ErrorText · uxjson.Parse · uxdatetime.SleepMilliseconds · uxb run · uxb bld ACIKLAMA: Python ile yerel bir HTTP hizmeti açılır (dış ağ gerekmez); uXBasic programı onu uxhttp (libcurl) ile çağırır. HTTP durum kodu (404, 500) ile ağ kodu (Perform'un döndürdüğü libcurl kodu: 0 tamam, 3 geçersiz adres, 28 zaman aşımı) ayrı şeylerdir; program ikisini ayrı denetler. Yanıt gövdesi uxjson ile çözülür. Kararsız bir uç noktaya artan bekle

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari, motor_calistir, log_message, yanit, do_GET, do_POST, __init__, handle_error.
Çağrı/yol başvuruları: istemci.exe, uxb.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/dis/zip_cikar_dogrula.py`

KONU: ZIP arşivini uxarchive ile açıp içeriği SHA-256 ile doğrulamak ve zip-slip saldırısına karşı korumayı sınamak (üç yerel motorda aynı sonuç) KOMUTLAR: python zipfile · uxarchive.EntryCount · ExtractAll · ErrorText · uxfs.ReadAllText · uxfs.DirectoryExists · uxfs.FileExists · uxcrypto.Sha256Text · uxb run · uxb bld ACIKLAMA: Python iki ZIP üretir: düzgün bir arşiv (iç içe klasör ve boş klasör dahil) ve içinde "../kacak.txt" adlı hileli bir giriş bulunan arşiv (zip-slip saldırısı). uXBasic programı uxarchive (libarchive tabanlı) ile ikisini de açar; düzgün arşivde her dosyanın SHA-256 özetini Python'un hesapladığı özetle karşılaştırır, hileli arşivde kütüphanenin girişi reddettiğini ve he

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, sonuc_satirlari, sha.
Çağrı/yol başvuruları: arsiv.exe, uxb.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/hedefler/bes_motor_ayni_program.py`

KONU: Aynı uXBasic programını beş motorda çalıştırıp çıktıları karşılaştırmak: AST, MIR, x64, JS ve WASM KOMUTLAR: uxb run · uxb run --interpreter-backend MIR · uxb bld --build-x64 · uxb jsw --js-out · uxb wat --emit-wasm --wat2wasm · node ACIKLAMA: Tamsayı, döngü, özyineleme ve koşul kullanan küçük bir program (100'e kadar asal sayıların toplamı, Fibonacci, en büyük ortak bölen, Collatz adım sayısı, faktöriyel) beş hedefte çalıştırılır. Program yalnız tamsayı yazdırır, çünkü WASM hedefi henüz metin (G-WASM-8) ve ondalıklı sayı (G-WASM-7) desteklemez. AST ve MIR yorumlayıcı, x64 yerel kod, JS node ile, WASM wat2wasm + node ile çalışır. Beş çıktı satır satır karşılaştırılır; fark varsa hangi 

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir, satirlar.
Çağrı/yol başvuruları: p.exe, uxb.exe, wat2wasm.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/meta/ast_api_belgesi.py`

KONU: Derleyicinin AST raporundan işlev ve sınıf belgesi çıkarmak KOMUTLAR: uxb ast --ast-json-out ACIKLAMA: Derleyici kaynağı çözümler ve AST'yi JSON olarak yazar. Bu betik o JSON'u okuyup işlev, yordam ve sınıf imzalarını listeler; kaynağı kendisi ayrıştırmaz. = FUNCTION Topla(a AS I32, b AS I32) AS I32   [satir 1] = SUB Selam(ad AS STRING)   [satir 5] = CLASS Nokta { x AS I32, y AS I32 }   [satir 9]

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: ast_al, parametreler, donus_tipi.
Çağrı/yol başvuruları: uxb.exe.

### `tools/kitap/kilavuz_v2/arac_ornekleri/meta/test_kosucu_uret.py`

KONU: AST'den sınama işlevlerini bulup sınama koşucusu üretmek (meta üretim) KOMUTLAR: uxb ast --ast-json-out · uxb run --interpreter-backend MIR ACIKLAMA: Adı Test_ ile başlayan ve BOOLEAN döndüren her işlev bulunur; her biri için çağrı yazan bir koşucu üretilir ve MIR yorumlayıcısıyla çalıştırılır. Elle liste tutmak gerekmez. = bulunan sinamalar: Test_Toplama, Test_Carpma, Test_Hatali = Test_Toplama: gecti = Test_Carpma: gecti = Test_Hatali: KALDI = ozet: 2 gecti, 1 kaldi

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: calistir.
Çağrı/yol başvuruları: uxb.exe.

### `tools/kitap/kilavuz_v2/ilerleme_guncelle.py`

ILERLEME.md'deki "Bölümler ve durum" tablosunun Durum sütununu kaynak şablonlardan sayarak yazar.  Sayılan her değer şablondan gelir, elle girilmez:   satır   = şablon dosyasının satır sayısı   örnek   = {{ORNEK:...}} yer tutucusu (aynı örnek iki bölümde geçerse ikisinde de sayılır)   kayıt   = şablonda geçen benzersiz Ek G kaydı (G-ALAN-n)   hedef   = "◇ HEDEF" işaretli yer Kullanım (proje kökünden): python tools\kitap\kilavuz_v2\ilerleme_guncelle.py

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: sayimlar, durum, main.
Çağrı/yol başvuruları: ilerleme_guncelle.py, tablo_denetle.py, tools\\kitap\\kilavuz_v2\\ilerleme_guncelle.py, uret.py.

### `tools/kitap/kilavuz_v2/sorun_takibe_isle.py`

Kılavuz V2 sınır kataloğunu (veri/sinirlar.txt) ai_koordinasyon/SORUN_TAKIP.md'ye işler.  Her katalog kaydı (G-xxx-n) için SORUN_TAKIP'ta AYRI bir S-numaralı kayıt açar; böylece her kusur sırayla ve tek tek düzeltilebilir. Eşleme veri/sorun_eslemesi.txt dosyasında tutulur ('G-CLI-1 = S-205'); eşlemesi olan kayıt yeniden yazılmaz, bu yüzden betik katalog büyüdükçe yeniden çalıştırılabilir (yalnız yeni kayıtlar eklenir).  Yan çıktı: ai_koordinasyon/KILAVUZ_V2_SORUN_DIZINI.md (önerilen düzeltme sırasına göre dizin; her çalıştırmada yeniden yazılır).  Kullanım:   python tools/kitap/kilavuz_v2/sorun_takibe_isle.py --dene      # ne yapılacağını yazar, dosyaya dokunmaz   python tools/kitap/kilavuz_v2/sorun_takibe_isle.py             # yazar

```text
ap.add_argument('--dene', action='store_true', help='dosyaya yazmadan ne yapılacağını göster')
```
Rutinler: katalog_oku, esleme_oku, kisa_baslik, kayit_metni, dizin_metni, capraz_basvuru, main.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261007.exe, bin\\uxb_kilavuz_20261013.exe, bin\\uxb_kilavuz_20261013_1704.exe, bin\\uxb_kilavuz_20261013_2333.exe, bin\\uxb_kilavuz_20261014_0253.exe, tests\\run_all_model_tests.ps1, tools/kitap/kilavuz_v2/sorun_takibe_isle.py.

### `tools/kitap/kilavuz_v2/tablo_denetle.py`

Üretilen kılavuzdaki Markdown tablolarının sütun sayısı tutarlı mı? (kod blokları ve ters tırnak içindeki | sayılmaz)  Kullanım (proje kökünden): python tools/kitap/kilavuz_v2/tablo_denetle.py [kılavuz.md] Çıkış kodu: sorunlu satır yoksa 0, varsa 1.

```text
positional: sys.argv[1]
```
Rutinler: sutun_say.
Çağrı/yol başvuruları: tools/kitap/kilavuz_v2/tablo_denetle.py.

### `tools/kitap/kilavuz_v2/uret.py`

uXBasic Hedeflenen Sistem ve Kullanma Kılavuzu V2 üreticisi.  sablon/*.md dosyalarını sırayla birleştirir; yer tutucuları DOĞRULANMIŞ içerikle doldurur:    {{ORNEK:grup/ad}}                  docs/kitaplar/_ortak/ornekler/<grup>/<ad>.uxb: kod + beklenen çıktı + motor durumu   {{ORNEK:grup/ad|baslik=Metin}}     aynısı, üstte kalın başlıkla   {{ORNEK:grup/ad|durum=gizle}}      motor durum satırını göstermez   {{ORNEK:grup/ad|anlat=evet}}       örnek dosyasındaki ACIKLAMA metnini kodun üstünde alıntı bloğu olarak gösterir (içindeki G-kayıtları "anılmış" sayılır)   {{ORNEKKOD:grup/ad}}               yalnız kod (çıktısız, durumsuz)   {{ARAC:grup/ad|baslik=..}}         tools/kitap/kilavuz_v2/arac_ornekleri altındaki betik (Python/PowerShell/JS) + beklenen çıktı + doğrulama   {{CLI_SECENEKLER}}                 uxb --help kayıt listesinden seçenek tabloları   {{ESLIK_OZETI}}                    örnek sonuçlarından motor eşliği özeti   {{ESLIK_TOPLAM}}                   aynı verinin tek cümlelik toplamı (her motorda geçen / beklentili örnek)   {{SINIRLAR}}                       veri/sinirlar.txt: bilinen sınırlar kataloğu (alan alan tablo + tür özeti)   {{SINIRLAR:ALAN}}                  yalnız bir alanın tablosu (örn. CLI, JS)   {{ONISLEMCI}}                      veri/onislemci.txt: 125 önişlemci yönergesinin dizini (kaynaktaki listeyle karşılaştırılır)   {{ONISLEMCI:Grup adı}}             yalnız bir grubun tablosu   {{KUTUPHANELER}}                   include/modules/*.uxmh dizini: başlık, ad alanı, işlev sayısı (kaynaktan sayılır), DLL sembol denetimi                                      (veri/dll_denetim.json), el yazması açıklama (veri/kutuphaneler.txt) ve örnek durumu   {{KUTUPHANELER:Kategori}}          yalnız bir kategorinin tablosu   {{SURUM}}                          derleyici dosyası + SHA256 (doğrulamada kullanılan)   {{KARARLAR}}                       her bölümün 'N.k … programlama kararları' maddelerini bölüm bölüm toplar (K<bölüm>.<sıra> numaralı)   {{KARARLAR:OZET}}                  yalnız özet tablo: bölüm başına karar sayısı   {{ANAHTAR_SOZCUKLER}}              Ek A: lexer_keyword_table.fbs'den gruplu sözcük tablosu + 18.09 tasarım karşılaştırması + bağlamsal sözcükler   {{YERLESIK_ISLEVLER}}              Ek B: veri/yerlesik_islevler.csv (uxb sem --type-infer-report-csv-out) + veri/islev_aciklamalari.txt   {{ONISLEMCI_DIZINI}}               Ek C: önişlemci yönergelerinin alfabetik dizini (söz dizimi, durum)   {{CALLDLL_YOGUN}}                  libsx modüllerinde `CALL(DLL, …)` kullanan modül sayısı ve en yoğun altı modül (kaynaktan sayılır)  Sonuç dosyaları (ornek_dogrula.py --web çıktıları) SONUC_DOSYALARI sırasıyla birleştirilir; sonrakiler öncekini ezer. Referans verilen bir örnek bulunamazsa ya da AST/MIR/x64'te beklenen çıktıyı vermiyorsa üretim UYARI yazar; --sert verilirse çıkış kodu 1 olur (sahte "çalışıyor" yazılmasın).

```text
ap.add_argument('--sert', action='store_true', help='uyarı varsa çıkış kodu 1')
ap.add_argument('--yardim', default=os.path.join(VERI, 'cli_help.txt'))
ap.add_argument('--cikti', default=CIKTI)
```
Rutinler: sonuclari_yukle, ornek_oku, sinif, durum_satiri, ornek_yer_tutucu, arac_yer_tutucu, cli_aciklamalari, cli_secenekleri, esdegerlik_ozeti, esdegerlik_toplami, sinirlari_oku, sorun_eslemesi_oku, sorun_durumlari_oku, sinirlar_tablosu, sinir_tutarliligi, onislemci_oku, onislemci_kaynak_listesi, onislemci_tutarliligi, onislemci_tablosu, kutuphaneler_oku, kutuphane_tara, calldll_yogun, kutuphane_oneki, kutuphane_ornekleri, kutuphane_dll_hucresi, kutuphaneler_tablosu, surum_bilgisi, kararlari_topla, kararlar_ozeti, kararlar_metni, anahtar_sozcukler_tablosu, yerlesik_islevler_tablosu, onislemci_dizini, isle, main, takip_hucresi, degistir.
Çağrı/yol başvuruları: bin\uxb_kilavuz_20261013_1704.exe, build_all.bat, ornek_dogrula.py, sorun_takibe_isle.py, tools/kitap/kilavuz_v2/yoklama/dll_sembol_denetimi.py, tools\\kitap\\arac_dogrula.py, uret.py, uxb_kilavuz_20261014_0253.exe.

### `tools/kitap/kilavuz_v2/yoklama/cli_secenek_tarama.py`

uxb komut satırı seçeneklerini TEK TEK ölçer ve özetler (Kılavuz V2, Bölüm 2.8 / Ek G'nin ölçüm kaynağı).  Neden: yardım metni ve kayıt defteri her seçeneğin ne yaptığını söyler; bu betik gerçekten ne yaptığını ölçer. Yeni bir derleyici ikilisi çıktığında aynı ölçüm tekrarlanır ve hangi G-CLI kayıtlarının kapandığı görülür.    A) Dosya çıktılı seçenekler (değer alan `…-out`): her seçenek TEK BAŞINA, her fiille (lex par ast sem hir mir run runmir x64 bld jsw jswb wat wasm),      ayrı klasörde. Ölçülen: dosya oluştu mu, boş mu, geçerli JSON mu, `schema`/`status` var mı, çıkış kodu, ilk ERROR.   B) Bayraklar (değer almayan): altı fiilde bayraksız tabana göre çıkış kodu / stdout / üretilen dosya kümesi farkı.   Ek: aynı içeriği yazan seçenek grupları (normalize edilmiş karma), yalnız sayaç/iskelet yazanlar.  Kullanım (proje kökünden):   python tools\kitap\kilavuz_v2\yoklama\cli_secenek_tarama.py --uxb bin\uxb_kilavuz_20261007.exe --cikti %TEMP%\cli_tarama   seçenekler: --mod AB (varsayılan), --is 4 (paralel işçi), --sinir N (yalnız ilk N seçenek; denemek için) Çıktı: <cikti>\cli_tarama_raporu.json ve konsola özet. Dikkat: ~1300 koşu yapar (4 işçiyle yaklaşık 4-6 dakika).

```text
ap.add_argument('--uxb', default=os.path.join(KOK, 'bin', 'uxb.exe'))
ap.add_argument('--cikti', default=os.path.join(os.environ.get('TEMP', '.'), 'cli_tarama'))
ap.add_argument('--mod', default='AB')
ap.add_argument('--is', dest='isci', type=int, default=4)
ap.add_argument('--sinir', type=int, default=0)
ap.add_argument('--sakla', action='store_true', help='koşu klasörlerini silme (varsayılan: her ölçümden sonra sil; tam saklama ≈ 1 GB tutar)')
```
Rutinler: fiiller, kayit_oku, uzanti, norm, main, __init__, bitir, cal, hazirla, incele, dosya_isi, dosya_kumesi, bayrak_isi.
Çağrı/yol başvuruları: ana.exe, bin\\uxb_kilavuz_20261007.exe, cikti/ana.exe, tools\\kitap\\kilavuz_v2\\yoklama\\cli_secenek_tarama.py, uxb.exe, wat2wasm.exe.

### `tools/kitap/kilavuz_v2/yoklama/dll_sembol_denetimi.py`

libsx sarmalayıcılarındaki CALL(DLL, "x.dll", "sembol", ...) çağrılarının, bin klasöründeki DLL'lerde gerçekten dışa aktarıldığını denetler ve sonucu veri/dll_denetim.json dosyasına yazar (kılavuz üreticisi bu dosyayı okur).  Kullanım (proje kökünden):  python tools\kitap\kilavuz_v2\yoklama\dll_sembol_denetimi.py Not: DLL'ler bu süreçte yüklenir; yüklenemeyen DLL ("yuklenemedi") ayrıca raporlanır.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\\kitap\\kilavuz_v2\\yoklama\\dll_sembol_denetimi.py.

### `tools/kitap/kilavuz_v2/yoklama/fark_sinifla.py`

İki vaka_kos görüntüsünü karşılaştırır ve değişen hücreleri sınıflar:   BOZULDU  : eski rc=0, yeni rc!=0 (çalışırken hata)   DUZELDI  : eski rc!=0, yeni rc=0   CIKTI    : ikisi de rc=0, çıktı farklı   ILETI    : ikisi de hata, ileti/kod farklı Kullanım: fark_sinifla.py eski.json yeni.json [sinif ...] [--motor AST]

```text
positional: sys.argv[sys.argv.index('--motor') + 1]
positional: sys.argv[1:]
```
Rutinler: ok, sinif.
Çağrı/yol başvuruları: fark_sinifla.py.

### `tools/kitap/kilavuz_v2/yoklama/gerileme_sondalari.py`

Kılavuz V2 sırasında bulunan kusurları (SORUN_TAKIP S-480 … S-508) küçük programlarla yoklar; yeni bir derleme için ilk bakış.  Her sonda doğru davranışı bilir; her yol (AST, MIR, MIR-x64, AST-x64, JS, WASM) için sonuç şu simgelerden biridir:   ✔  beklenen çıktıyı verdi   ◌  açıkça reddetti (çıkış kodu sıfırdan farklı ve bir ERROR satırı var) — sessiz yanlış değildir   ✖  yanlış çıktı verdi (sessiz hata) ya da iletisiz çöktü   ·  bu yol için beklenti tanımlı değil Yol başına beklenti 'ok' (tam çıktı), 'ret' (açık ret de kabul) ya da yok. Çıkış: sorun varsa 1.  Kullanım (proje kökünden):   python tools\kitap\kilavuz_v2\yoklama\gerileme_sondalari.py --uxb bin\uxb_kilavuz_20261013_2052.exe [--sadece S-504] [--is 3]

```text
ap.add_argument('--uxb', required=True)
ap.add_argument('--sadece')
ap.add_argument('--is', type=int, default=3, dest='isci')
ap.add_argument('--ayrinti', action='store_true')
```
Rutinler: sonda, sonuc_simge, calistir, tani_dosyasi_sondalari, main.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261013_2052.exe, tools\\kitap\\kilavuz_v2\\yoklama\\gerileme_sondalari.py.

### `tools/kitap/kilavuz_v2/yoklama/goster.py`

vaka_kos anlık görüntüsünü vaka başına motor sütunlarıyla özetler:  goster.py dosya.json [süz]

```text
positional: sys.argv[2]
positional: sys.argv[1]
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: goster.py.

### `tools/kitap/kilavuz_v2/yoklama/iddia_beklenen.py`

vaka_kos anlık görüntüsündeki iddia vakalarını, iddia.json dosyalarındaki 'beklenen' değerlerle karşılaştırır. Kullanım: iddia_beklenen.py goruntu.json [--ayrinti]

```text
positional: sys.argv[1]
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: iddia_beklenen.py.

### `tools/kitap/kilavuz_v2/yoklama/kararlilik.py`

Bir programı aynı motorda N kez koşturur ve sonuç dağılımını yazar (aralıklı takılma / yarış denetimi).  Neden: Kılavuz V2 örneklerinden `20_esz/mutex` ve `53_kv_gorev/paralel_asal_sayim` MIR yorumlayıcıda bazen doğru çıktıyı yazıp sonlanmıyor (60 sn zaman aşımı); bu tek koşuda görünmez. Bu betik sonucu `ok` (beklenen çıktı + çıkış 0), `takildi` (zaman aşımı) ve `yanlis` diye sayar.  Kullanım (proje kökünden; makine boşken):   python tools\kitap\kilavuz_v2\yoklama\kararlilik.py --uxb bin\uxb_kilavuz_20261007.exe --dosya docs\kitaplar\_ortak\ornekler\20_esz\mutex.uxb --motor MIR --kez 10 [--sure 90]

```text
ap.add_argument('--uxb', required=True)
ap.add_argument('--dosya', required=True)
ap.add_argument('--motor', default='MIR', choices=['AST', 'MIR'])
ap.add_argument('--kez', type=int, default=10)
ap.add_argument('--sure', type=int, default=90)
```
Rutinler: beklenen, main.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261007.exe, tools\\kitap\\kilavuz_v2\\yoklama\\kararlilik.py.

### `tools/kitap/kilavuz_v2/yoklama/memref_dolu_yoklama.py`

K-06 / S-582 yoklaması: MemoryRef tablosu (4096 yuva) dolunca bayat-işaretçi koruması sessizce kapanıyor mu?  N ayrı dizi (DIM a0(3) AS I32 ... a{N-1}) tanımlar, sonuncunun adresini alır, dizi REDIM edilir ve eski işaretçiyle PEEKD okunur. Beklenen: «MemoryRef: stale pointer» hatası. N > 4096'da MIR hatasız `11` yazar (koruma kapalı). Kullanım (depo kökünden):   python tools/kitap/kilavuz_v2/yoklama/memref_dolu_yoklama.py [ikili] [N ...] Varsayılan ikili bin/uxb_kilavuz_20261014_0253.exe, varsayılan N: 10 4000 4200 5000 (AST ve MIR; 4000+ dizi için birkaç dakika sürer). Geçici dosyalar sistem geçici klasörüne yazılır.

```text
positional: sys.argv[1]
positional: sys.argv[1:]
positional: sys.argv[1]
```
Rutinler: kur.
Çağrı/yol başvuruları: bin/uxb_kilavuz_20261014_0253.exe, tools/kitap/kilavuz_v2/yoklama/memref_dolu_yoklama.py, uxb_kilavuz_20261014_0253.exe.

### `tools/kitap/kilavuz_v2/yoklama/ornek_astx64.py`

Kılavuz örneklerini ESKİ AST-x64 yoluyla (`uxb bld --build-x64 --x64-mode AST`) derleyip çalıştırır ve sonucu `ornek_dogrula.py`'nin kullandığı sınıflarla (GECTI / ACIK_RET / FARKLI / HATA / BEKLENTI_YOK) yazar.  Neden: 2026-10-11 kararıyla altı yol (AST, MIR, MIR-x64, AST-x64, JS, WAT/WASM) aynı dil davranışını vermelidir; ama ornek_dogrula.py'nin "x64" sütunu yalnız MIR-x64'tür. Bu betik AST-x64 sütununu ayrıca ölçer; böylece sessiz yanlış sonuç (G-KTIP-7, G-TIP-16) gibi yola özgü kusurlar kitapta gizli kalmaz.  Kullanım (proje kökünden):   python tools\kitap\kilavuz_v2\yoklama\ornek_astx64.py --uxb bin\uxb_kilavuz_20261013_1704.exe --sonuc astx64.json [--is 4] [--desen _kv_] Çıktı: sonuç JSON'u (örnek başına durum/çıktı/rc) ve konsola durum sayıları.

```text
ap.add_argument('--uxb', required=True)
ap.add_argument('--sonuc', required=True)
ap.add_argument('--is', type=int, default=4, dest='isci')
ap.add_argument('--desen', help='grup adı bu düzenli ifadeyle eşleşen klasörler (örn. _kv_)')
ap.add_argument('--kok', default=od.ORNEK)
```
Rutinler: astx64, main.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261013_1704.exe, ornek_dogrula.py, program.exe, tools\\kitap\\kilavuz_v2\\yoklama\\ornek_astx64.py.

### `tools/kitap/kilavuz_v2/yoklama/ornek_fark.py`

Kılavuz örneklerinin iki derleyici sürümündeki sonucunu karşılaştırır.    eski: ornek_sonuclari_web_20261007.json + ornek_sonuclari_kv.json (uret.py'nin kullandığı birleşim; sonrakiler öncekini ezer)   yeni: ornek_dogrula.py --web --sonuc <json> ile yeni ikiliyle alınmış tam sonuç dosyası  Kullanım: python tools/kitap/kilavuz_v2/yoklama/ornek_fark.py <yeni.json> [--sadece-kitap] [--ayrinti]   --sadece-kitap : yalnız şablonlarda {{ORNEK:...}} ile anılan örnekler Çıktı: motor ve durum başına değişim sayısı, ardından değişen örnekler (örnek, motor, eski durum -> yeni durum, yeni çıktı).

```text
positional: sys.argv[1:]
```
Rutinler: yukle, birlestir, kitaptaki_ornekler, main.
Çağrı/yol başvuruları: ornek_dogrula.py, tools/kitap/kilavuz_v2/yoklama/ornek_fark.py, uret.py.

### `tools/kitap/kilavuz_v2/yoklama/tarif_dene.ps1`

Kılavuz V2, Bölüm 2.7.2 "Sık kullanılan tarifler" tablosundaki her komutu verilen derleyiciyle çalıştırır ve [ad] kod=<çıkış> <süre> <üretilen dosya boyutları> | <ilk üç çıktı satırı> biçiminde özetler. İki derleme karşılaştırılırken süre alanı yok sayılmalıdır. Kullanım (proje kökünden): pwsh -File tools\kitap\kilavuz_v2\yoklama\tarif_dene.ps1 -Uxb bin\uxb_kilavuz_20261013_2224.exe

```text
[string]$Uxb = 'bin\uxb.exe'
[string]$Cikti = (Join-Path $env:TEMP 'uxb_tarif_dene')
```
Rutinler: T.
Çağrı/yol başvuruları: bin\uxb.exe, bin\uxb_kilavuz_20261013_2224.exe, k.exe, k_ast.exe, k_w4.exe, tools\kitap\kilavuz_v2\yoklama\tarif_dene.ps1, tools\wabt\bin\wat2wasm.exe.

### `tools/kitap/kilavuz_v2/yoklama/vaka_kos.py`

Kılavuz V2 vaka külliyatını bir uxb ikilisiyle dört motorda (AST, MIR, x64, JS) koşturur ve anlık görüntü (JSON) yazar; iki anlık görüntüyü karşılaştırarak bir derleyici sürümünden ötekine neyin değiştiğini gösterir.  Külliyat: tools/kitap/kilavuz_v2/yoklama/vaka/  (kılavuzdaki her anlatım iddiasının ve sınır kaydının küçük programları)   *.coklu.txt   '=====' ile ayrılmış programlar; her parçanın ilk satırı başlıktır   *.satir.txt   satır başına bir vaka:  ad | kurulum (\n ile) | PRINT edilecek ifade(ler)   *.pp.txt      önişlemci vakaları:  '=== ad' başlığı + kaynak satırları (ayrıca genişletilmiş kaynak da kaydedilir)   *.iddia.json  iddia listesi: {ad, once, ifade | kod, beklenen, yoksay}  (beklenen burada yalnız bilgi; karşılaştırma görüntüler arasındadır)  Kullanım (proje kökünden):   python tools\kitap\kilavuz_v2\yoklama\vaka_kos.py kos  --uxb bin\uxb_kilavuz_20261013.exe --cikti %TEMP%\vaka_yeni.json [--is 6] [--sadece desen]   python tools\kitap\kilavuz_v2\yoklama\vaka_kos.py fark eski.json yeni.json [--tam] Not: 1837 vaka (2026-10-13) x 4 motor; 6 işçiyle ve makine boşken ikili başına yaklaşık 100 dakika sürer (başka iş çalışırken daha uzun); alt küme için --sadece desen (anahtar 'dosya::ad' içinde geçen metin) kullanın. Eski AST-x64 yolu (`bld --build-x64 --x64-mode AST`) varsayılan motor listesinde yoktur; `--motor x64a` ile yalnız onu koşturabilirsiniz (örn. iddia vakaları için: --motor x64a --sadece .iddia.json). Rakam, adres ve geçici dosya yarışı gürültüsü vardır (x64'te çöp değer yazdıran vakalar, ZAMAN_ASIMI): fark çıktısında tek başına şaşırtıcı hücreyi yeniden koşturup doğrulayın.

```text
k.add_argument('--uxb', required=True)
k.add_argument('--cikti', required=True)
k.add_argument('--is', dest='isci', type=int, default=6)
k.add_argument('--sadece', default=None)
k.add_argument('--klasor', default=None, help='vaka klasörü (varsayılan: bu betiğin yanındaki vaka/)')
k.add_argument('--motor', default=','.join(MOTORLAR))
f.add_argument('eski')
f.add_argument('yeni')
f.add_argument('--tam', action='store_true')
```
Rutinler: kodlari_oku, norm, calis, motor_kos, vaka_kos, kos, fark, main, ekle.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261013.exe, p.exe, pa.exe, tools\\kitap\\kilavuz_v2\\yoklama\\vaka_kos.py, wat2wasm.exe.

### `tools/kitap/kilavuz_v2/yoklama/yol_matrisi.py`

Küçük programları ALTI yolda (AST, MIR, MIR-x64, AST-x64, JS, WASM) koşturur ve yan yana yazar.  Neden: 2026-10-11 kararıyla altı yol aynı dil davranışını vermelidir; ornek_dogrula.py ve vaka_kos.py varsayılan olarak AST-x64'ü ve WASM'ı vaka düzeyinde ölçmez. Bu betik bir vaka dosyasındaki (.coklu.txt biçimi: ilk satır ad, sonra kod, `=====` ayırıcı) ya da tek bir .uxb dosyasındaki programlar için altı yolun çıktısını tek tabloda verir; WASM yolu yalnız tamsayı yazdıran programlarda anlamlıdır (G-WASM-7, G-WASM-8).  Kullanım (proje kökünden):   python tools\kitap\kilavuz_v2\yoklama\yol_matrisi.py --uxb bin\uxb_kilavuz_20261013_1704.exe --vaka tools\kitap\kilavuz_v2\yoklama\vaka\ktip_dene2.coklu.txt [--is 3] [--json cikti.json]   python tools\kitap\kilavuz_v2\yoklama\yol_matrisi.py --uxb bin\<x>.exe --dosya program.uxb Tabloda her yol icin ilk 3 cikti satiri gorunur; daha uzun ciktilar icin `--satir 12 --genislik 300`.

```text
ap.add_argument('--uxb', required=True)
ap.add_argument('--vaka')
ap.add_argument('--dosya')
ap.add_argument('--is', type=int, default=3, dest='isci')
ap.add_argument('--json')
ap.add_argument('--satir', type=int, default=3, help='her yol icin tabloda gosterilecek cikti satiri (varsayilan 3; JSON en az 6 tutar)')
ap.add_argument('--genislik', type=int, default=150, help='tablodaki ozet satirinin en fazla karakteri')
```
Rutinler: calis, exe_calistir, kos, vakalari_oku, main.
Çağrı/yol başvuruları: bin\\uxb_kilavuz_20261013_1704.exe, ornek_dogrula.py, p.exe, tools\\kitap\\kilavuz_v2\\yoklama\\yol_matrisi.py, vaka_kos.py, wat2wasm.exe.

### `tools/kitap/kural_belgesi_uret.py`

uXBasic programlama kuralları belgesini üretir: docs/kitaplar/UXBASIC_PROGRAMLAMA_KURALLARI.md  Amaç: yerel kodlayıcı model (uxcoder / qwen2.5-coder) ve insanlar için, dilin KURALLARINI ve her yapının çalışan yazımını tek yerde vermek. Belge uydurma içermez: her {{ORNEK:grup/ad}} yer tutucusu, örneğin AST, MIR ve native x64'te GEÇTİĞİ kayıtlı sonuçlardan (ornek_sonuclari*.json) doğrulanmışsa kod + çıktı ile, doğrulanmamışsa "DOĞRULANMADI + motor durumları" ile doldurulur.  Kullanım: python tools/kitap/kural_belgesi_uret.py            (önce ornek_dogrula.py ile sonuçlar güncel olmalı) Girdi:  docs/kitaplar/_ortak/ornekler/**.uxb ve ornek_sonuclari_20261007.json + ornek_sonuclari_22.json (son çalıştırmalar) Çıktı:  docs/kitaplar/UXBASIC_PROGRAMLAMA_KURALLARI.md  +  docs/kitaplar/_ortak/kural_dogrulama_ozeti.json

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: sonuclari_oku, ornek, sinirlar, main.
Çağrı/yol başvuruları: ornek_dogrula.py, tools/kitap/kural_belgesi_uret.py.

### `tools/kitap/ornek_dogrula.py`

Kitap örneklerini AST, MIR ve native x64 motorlarında çalıştırıp beklenen çıktıyla karşılaştırır.  Örnek dosya biçimi (docs/kitaplar/_ortak/ornekler/<grup>/<ad>.uxb):     ' KONU: IF / ELSEIF / ELSE     ' KOMUTLAR: IF THEN ELSEIF ELSE END     ' ACIKLAMA: tek satırlık açıklama (isteğe bağlı)     '= beklenen çıktının 1. satırı     '= beklenen çıktının 2. satırı     ...program... Beklenen satırlar birebir karşılaştırılır (sağdaki boşluklar ve INFO/WARN satırları yok sayılır).  Sonuç: docs/kitaplar/_ortak/ornek_sonuclari.json  (her örnek için motor -> GECTI/FARKLI/HATA + çıktı) Kullanım: python tools/kitap/ornek_dogrula.py [--uxb bin\uxb_openclaw_S087.exe] [--grup akis] [--ad if_elseif] [--is 3]           [--kok <örnek klasörü>] [--sonuc <sonuç.json>]   (paralel işlerde her iş kendi --kok/--sonuc'unu verir) Yorumlayıcılar ve native derleme geçici bir klasörde çalışır; proje köküne build\<tarih> klasörü açılmaz.

```text
ap.add_argument('--uxb', default=os.path.join(KOK, 'bin', 'uxb_openclaw_S087.exe'))
ap.add_argument('--grup')
ap.add_argument('--ad')
ap.add_argument('--is', type=int, default=3, dest='isci')
ap.add_argument('--web', action='store_true', help='JS (jsw+node) ve WASM (wat+wat2wasm+node) hedeflerini de çalıştır')
ap.add_argument('--desen', help='grup adı bu düzenli ifadeyle eşleşen klasörleri çalıştır (örn. _kv_)')
ap.add_argument('--kok', default=ORNEK, help='örneklerin aranacağı klasör (alt klasörler dahil)')
ap.add_argument('--sonuc', default=SONUC, help='sonuç JSON dosyası (paralel çalışan her iş kendi dosyasını kullanmalı)')
```
Rutinler: oku, temizle, calistir, kisalt, karar, web_dogrula, dogrula, main, oku.
Çağrı/yol başvuruları: bin\\uxb_openclaw_S087.exe, build_all.bat, program.exe, tools/kitap/ornek_dogrula.py, uxb_openclaw_S087.exe, wat2wasm.exe.

### `tools/kitap/yuzey_tara.py`

uXBasic dil yüzeyi tarayıcısı (kitaplar için ortak "gerçek kaynak").  `uxb mtx` matrisleri eksik/tek dosya ürettiği için yüzey DOĞRUDAN kaynaktan çıkarılır: her katmandaki `Case "AD", ...` satırları ve `x = "AD"` karşılaştırmaları toplanır; bir adın hangi katmanda (lexer, parser, AST yorumlayıcı, MIR yorumlayıcı, native x64, legacy x64, JS, WASM) geçtiği tabloya dökülür. "Geçiyor" = o katmanın kaynağında adla eşleşen bir dal var (davranışın doğru olduğu ayrıca testle doğrulanır).  Çıktı: docs/kitaplar/_ortak/dil_yuzeyi.json, dil_yuzeyi.md, dil_yuzeyi.tsv Kullanım: python tools/kitap/yuzey_tara.py

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: katman_bul, dosyalar, satir_adlari, lexer_anahtar, uxb_kullanim, main, kutuphaneler, kutuphane_raporu, tablo.
Çağrı/yol başvuruları: tools/kitap/yuzey_tara.py, uxb_run3.ps1.

### `tools/library_codegen/inventory_dll_and_wrappers.py`

Inventory shipped DLLs and uXBasic wrapper signatures.

```text
parser.add_argument('--root', default='.')
parser.add_argument('--objdump', default='C:\\msys64\\ucrt64\\bin\\objdump.exe')
```
Rutinler: purpose, sha256, exports, wrapper_api, main.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\objdump.exe.

### `tools/library_codegen/mir_record_binding_generator.py`

Generate uXBasic uxcapi aggregate descriptor builders from MIR Full JSON v2.

```text
parser.add_argument('mir_json', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--namespace', default='uxcabi_records')
```
Rutinler: ident, extent_product, render, main.
Çağrı/yol başvuruları: yok.

### `tools/library_tools/gen_uxraylib_3d_cpu_test.py`

uxraylib pencere gerektirmeyen 3B geometri duman testi uretici (S-052, raylib Models/3D dilimi 2).  Beklenen degerler, raylib'in KENDI islevlerini (libraylib) DOGRUDAN cagiran bir C referans programindan gelir; test sarmalayicinin yuva/tutamac/kayit mekanigini sinar. Cikti: tests/libraries/uxraylib/uxraylib_3d_cpu_smoke.uxb (dort motorda ayni sonucu vermek zorundadir). Kullanim: python tools/library_tools/gen_uxraylib_3d_cpu_test.py --root .

```text
ap.add_argument('--root', default='.')
```
Rutinler: main.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, ref.exe, tools/library_tools/gen_uxraylib_3d_cpu_test.py.

### `tools/library_tools/gen_uxraylib_math.py`

uxraylib raymath sarmalayici uretici (S-052, raylib Models/3D dilimi 1: CPU-tarafi matematik).  raymath.h'nin `RMAPI` islevlerini okur ve iki dosya uretir:   runtime_ext/uxraylib/uxraylib_math.inc      C (uxraylib_adapter.c icinden #include edilir)   libsx/uxraylib/uxraylib_math.bas            uXBasic `NAMESPACE uxraylib` sarmalayicilari  Sozlesme (uXBasic CALL(DLL) yalniz sayi/isaretci tasir, yapi degil):   * float/double        -> F64 (C tarafinda float'a daralir; raylib float kullanir)   * int                 -> I32   * Vector2/3/4, Quaternion -> bilesenlere acilir: v1x, v1y[, v1z[, v1w]] (F64)   * Matrix              -> I32 MATRIS TUTAMACI (0 = gecersiz). Matris ureten her islev YENI bir tutamac doner;                            isi biten tutamac MatrixRelease ile birakilir.   * Vector/Quaternion sonucu -> islev bir SUB'dur; sonuc "kayit"ta (register 0) durur: ResX/ResY/ResZ/ResW.     Birden cok sonuc ureten islevler kayit 1 ve 2'yi de doldurur (ResGet(kayit, bilesen)).   * 10 argumani asan islevler (Vector3CubicHermite/Barycenter, QuaternionCubicHermiteSpline) "yuva" varyanti ile     sunulur: VectorSlotSet(yuva, x, y, z, w) ile girdiler yuvalara yazilir, islev yuva numaralariyla cagrilir.  Kullanim: python tools/library_tools/gen_uxraylib_math.py --root . [--raymath C:\msys64\ucrt64\include\raymath.h]

```text
ap.add_argument('--root', default='.')
ap.add_argument('--raymath', default=HEADER_DEFAULT)
```
Rutinler: snake, parse_params, flatten, main.
Çağrı/yol başvuruları: tools/library_tools/gen_uxraylib_math.py.

### `tools/library_tools/gen_uxraylib_math_test.py`

uxraylib raymath duman testi uretici (S-052).  Beklenen degerler UXBASIC/ADAPTER kullanmadan, raymath.h'yi DOGRUDAN cagiran kucuk bir C programindan gelir (gcc ile derlenip calistirilir): boylece test, sarmalayicinin argüman siralamasi / bilesen eslemesi / kayit-tutamac mekanigini sinar, matematigin kendisini degil. Uretilen dosya tests/libraries/uxraylib/uxraylib_math_smoke.uxb'dir ve dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) ayni sonucu vermek zorundadir.  Kullanim: python tools/library_tools/gen_uxraylib_math_test.py --root .

```text
ap.add_argument('--root', default='.')
```
Rutinler: cfloat, main, vec_asserts.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, ref.exe, tools/library_tools/gen_uxraylib_math_test.py.

### `tools/library_tools/gen_uxraylib_wrappers.ps1`

uxraylib sarmalayici uretici (S-052): el ile yazilmis `.inc` C dosyalarindaki `UX_EXPORT` islevlerinden, henuz sarmalanmamis olanlar icin `CALL(DLL, ...)` sarmalayicilari uretir (uxsdl3 ureticisinin uxraylib uyarlamasi). raymath sarmalayicilari ayri uretilir (gen_uxraylib_math.py). Kullanim: pwsh tools\library_tools\gen_uxraylib_wrappers.ps1 -CFile runtime_ext\uxraylib\uxraylib_3d_cpu.inc -BasFiles libsx\uxraylib\uxraylib.bas,libsx\uxraylib\uxraylib_math.bas -OutFile <yeni.bas> Adlandirma: uxraylib_check_collision_spheres -> CheckCollisionSpheres. DIKKAT: ToUpperInvariant (tr-TR ToUpper i -> İ yapar). Parametre adlari uXBasic anahtar sozcuklerine (S-128) carpiyorsa paramRename ile degistiril

```text
[string]$CFile
[string[]]$BasFiles
[string]$OutFile
```
Rutinler: PascalName, MapType.
Çağrı/yol başvuruları: gen_uxraylib_math.py, tools\library_tools\gen_uxraylib_wrappers.ps1.

### `tools/library_tools/gen_uxsdl3_wrappers.ps1`

uxsdl3 sarmalayici uretici (S-052): runtime_ext\uxraylib\uxsdl3_adapter.c icindeki `UX_EXPORT` islevlerinden, libsx\uxsdl3\uxsdl3.bas dosyasinda HENUZ SARILMAMIS olanlar icin `CALL(DLL, ...)` sarmalayicilari uretir (yeni islev eklenince: uret, cikti dosyasini uxsdl3.bas'a ekle, sonra `python tools\library_tools\uxb_library_abi.py --root .` ile imzalari C ile karsilastir). Kullanim: pwsh tools\library_tools\gen_uxsdl3_wrappers.ps1 -CFile <adapter.c> -BasFile <uxsdl3.bas> -OutFile <yeni_sarmalayicilar.bas> Adlandirma: uxsdl3_get_window_title -> GetWindowTitle (ns/ms/id/bmp... buyuk harfli); paramRename/overrides tablolari sabit adlari yonetir. DIKKAT: buyuk harfe cevirmede ToUpperInvariant() k

```text
[string]$CFile
[string]$BasFile
[string]$OutFile
```
Rutinler: PascalName, MapType.
Çağrı/yol başvuruları: tools\library_tools\gen_uxsdl3_wrappers.ps1, tools\library_tools\uxb_library_abi.py.

### `tools/library_tools/uxb_c_full_bindgen.py`

Generate complete raw uXBasic bindings from a public C header surface.  The generator does not hand-pick convenience methods.  It scans every public FunctionDecl matching the library manifest, verifies the actual PE DLL export table, emits one uXBasic routine per C function, and emits C shims for public static-inline functions.  Private symbols and function-like preprocessor macros are outside the DLL function surface.  Variadic functions are represented by their original name plus a final uxcapi Args handle.

```text
parser.add_argument('--root', required=True)
parser.add_argument('--manifest', required=True)
parser.add_argument('--clang', required=True)
parser.add_argument('--objdump', required=True)
parser.add_argument('--include-root', required=True)
parser.add_argument('--dll', required=True)
parser.add_argument('--profile', choices=['stable', 'experimental'], default='stable')
parser.add_argument('--target', default='x86_64-w64-windows-gnu')
parser.add_argument('--report-dir', required=True)
parser.add_argument('--allow-no-exports', action='store_true')
```
Rutinler: run, walk, matches_any, sanitize_identifier, clean_type, format_define, is_const_char_pointer, is_wchar_pointer, map_c_type, extract_return_type, parse_exports, enum_value, parse_simple_macros, clang_ast, build_typedef_map, resolve_typedef, safe_type_name, find_owned_record_id, build_record_map, lookup_record, function_from_node, default_value, emit_failure, emit_indirect_return_function, emit_function, c_parameter_declaration, c_shim_parameter, indirect_types, emit_inline_shim, emit_u64_zero_arg_call, field_memory_methods, emit_type_helpers, emit_module, main, make_info.
Çağrı/yol başvuruları: yok.

### `tools/library_tools/uxb_ecosystem_doctor.py`

Cross-check the canonical uXBasic compiler/library ecosystem.  The doctor is intentionally cross-platform. It verifies metadata, wrappers, source layout and tool contracts without pretending to replace Windows builds.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--strict-source', action='store_true')
ap.add_argument('--report-dir', default='reports/libraries/ecosystem_doctor')
```
Rutinler: resolve_root, load_build_tool, main, add.
Çağrı/yol başvuruları: BUILD_UXB_LIBRARY_SYSTEM.bat, BUILD_UXB_LIBRARY_SYSTEM.ps1, RUN_UXB_ECOSYSTEM_DOCTOR.bat, build_64.bat, build_64.ps1, build_libraries.bat, build_libraries.ps1, spec.loader.exe, sys.exe, tools/library_tools/uxb_library_abi.py, tools/library_tools/uxb_library_build.py, tools/maintenance/archive_freebasic_c_output.py.

### `tools/library_tools/uxb_library_abi.py`

uXBasic native library ABI auditor and wrapper normalizer.  The tool is intentionally dependency-free. It treats runtime_ext C headers/sources as the ABI source of truth and validates every CALL(DLL) in libsx wrappers.

```text
parser.add_argument('--root', default='.', help='uxb directory or its parent')
parser.add_argument('--fix', action='store_true', help='rewrite wrappers to canonical ABI syntax')
parser.add_argument('--report-dir', default='reports/libraries/abi')
parser.add_argument('--allowlist', default='build/manual/config/ffi_allowlist.txt', help='write the runtime FFI allowlist after a clean ABI audit')
```
Rutinler: strip_c_comments, strip_c_abi_macros, split_top_level, normalize_c_decl, collect_c_prototypes, fb_type_to_c, collect_freebasic_prototypes, c_type_to_uxb, parse_wrapper_constants, parse_declared_types, find_call_span, parse_existing_call, infer_runtime_args, canonical_call, normalize_wrappers, resolve_root, write_ffi_allowlist, main.
Çağrı/yol başvuruları: yok.

### `tools/library_tools/uxb_library_build.py`

Build, verify, stage and deploy the canonical uXBasic Windows x64 DLL set.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--set', choices=['minimal', 'core', 'all'], default='core')
ap.add_argument('--library', action='append', default=[], help='build only named library; repeatable')
ap.add_argument('--audit-only', action='store_true')
ap.add_argument('--deploy-only', action='store_true')
ap.add_argument('--fetch-deps', action='store_true')
ap.add_argument('--clean', action='store_true')
ap.add_argument('--strict-all', action='store_true')
ap.add_argument('--strict-runtime', action='store_true', help='require x64 bin/uxb.exe and x64 DLLs')
ap.add_argument('--build-compiler', action='store_true')
```
Rutinler: resolve_root, sha256, pe_machine, run_logged, run_bat, run_script, build_compiler_x64, copy_if_different, build_output_candidates, find_expected_dll, remove_stale_build_outputs, select_libraries, stage_all, write_runtime_manifest, main.
Çağrı/yol başvuruları: bin/uxb.exe, cmd.exe, compiler/scripts/build_uxb_main_64.ps1, powershell.exe, powershell.exe/pwsh.exe, pwsh.exe, pwsh.exe/powershell.exe, sys.exe, tools/library_tools/uxb_library_abi.py, tools/library_tools/uxb_library_export_audit.py, tools/library_tools/uxb_library_source_gate.py.

### `tools/library_tools/uxb_library_export_audit.py`

Audit built uXBasic DLL architecture and exports without third-party Python packages.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--report-dir', default='reports/libraries/exports')
ap.add_argument('--require-all', action='store_true')
ap.add_argument('--require-x64', action='store_true')
ap.add_argument('--require-required', action='store_true', help='require manifest libraries marked required')
ap.add_argument('--only-dll', action='append', default=[], help='audit only this DLL name; repeatable')
```
Rutinler: u16, u32, rva_to_offset, parse_pe, resolve_root, wrapper_exports, find_dll, main.
Çağrı/yol başvuruları: yok.

### `tools/library_tools/uxb_library_layout_doctor.py`

!/usr/bin/env python3

```text
ap.add_argument('--root', default='.')
ap.add_argument('--strict', action='store_true')
```
Rutinler: resolve_root, main, add.
Çağrı/yol başvuruları: bin/uxb.exe.

### `tools/library_tools/uxb_library_source_gate.py`

Static integrity gate for the uXBasic canonical library/ABI10 patch.  This gate is intentionally dependency-free. It does not replace a FreeBASIC or Windows runtime build; it catches missing files, stale patch anchors, malformed JSON, broken include forwarders and common source-regression errors before the Windows build is attempted.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--report-dir', default='reports/libraries/source_gate')
```
Rutinler: resolve_root, sha256, main, add.
Çağrı/yol başvuruları: BUILD_UXB_LIBRARY_SYSTEM.bat, BUILD_UXB_LIBRARY_SYSTEM.ps1, RUN_UXB_ECOSYSTEM_DOCTOR.bat, \\msys64\\ucrt64\\bin\\gcc.exe, bin\\uxb.exe, build_64.bat, build_64.ps1, compiler/scripts/build_libraries.ps1, compiler/scripts/build_uxb_library_system.ps1, compiler/scripts/build_uxb_main_64.bat, compiler/scripts/build_uxb_main_64.ps1, compiler/scripts/resolve_uxb_toolchain.ps1, compiler/scripts/run_library_abi10_smoke.ps1, fbc64.exe, native/uxb_runtime/build_runtime_dll.bat, native/uxb_runtime/build_runtime_dll.ps1, runtime_ext/uxffi/build_uxffi_dll.bat, runtime_ext/uxffi/fetch_uxffi_deps_msys2.bat, tests/ecosystem/run_ecosystem_hardening.ps1, tests/ecosystem/test_ecosystem_hardening.py, tools/library_tools/uxb_ecosystem_doctor.py, tools/library_tools/uxb_library_abi.py, tools/library_tools/uxb_library_build.py, tools/library_tools/uxb_library_export_audit.py, tools/library_tools/uxb_library_layout_doctor.py, tools/tests/check_yama6_runtime_dll.py, tools/tests/run_yama6_interpreter_tests.py, tools\\wabt\\bin\\wat2wasm.exe.

### `tools/maintenance/Apply-CodexCompositePatch.ps1`

The v131 finalization package owns the overlapping executor/MIR/uxffi files. Take only the newer source-front-end and x64 contract work from the 28.07

```text
[Parameter(Mandatory = $true)]
    [string]$StageRoot
[string]$TargetRoot = (Get-Location).Path
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: runtime_ext\uxffi\fetch_uxffi_deps_msys2.bat, runtime_ext\uxjsruntime\build_uxjsrt.bat, runtime_ext\uxjsruntime\build_uxjsrt.ps1, runtime_ext\uxjsruntime\fetch_quickjs.ps1, tests\native\ffi_contract\test_uxffi_contract.py, tools\js_runtime\generate_js_runtime_fbs.py, tools\tests\run_ffi_contract_fix.ps1, tools\tests\verify_deep_fix_patch.py, tools\tests\verify_ffi_contract_patch.py.

### `tools/maintenance/Apply-FinalReleaseSelective.ps1`

Only missing release infrastructure and stale v120 test tools are selected. Working FFI sources are intentionally not overwritten.

```text
[Parameter(Mandatory = $true)]
    [string]$PackageRoot
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: compiler\scripts\run_final_ffi_quickjs_release_gate.ps1, run_final_ffi_quickjs_release.cmd, run_final_ffi_quickjs_release_no_package.cmd, tools\diagnostics\verify_final_ffi_quickjs_release.py, tools\release\package_uxbasic_distribution_final.ps1, tools\tests\run_ffi_contract_fix.ps1, tools\tests\verify_ffi_contract_patch.py.

### `tools/maintenance/archive_freebasic_c_output.py`

Move generated FreeBASIC C outputs out of canonical source directories.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--apply', action='store_true')
```
Rutinler: main.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/capture_uxb_fault.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Executable = ''
[string[]]$Arguments = @()
[string]$WorkingDirectory = ''
[string]$OutputDirectory = ''
[ValidateRange(1,7200)][int]$TimeoutSeconds = 120
```
Rutinler: Read-MemorySnapshot.
Çağrı/yol başvuruları: bin/uxb.exe, cc1.exe, fbc64.exe, nasm.exe, program.exe.

### `tools/maintenance/generate_diagnostic_schema.py`

Embed the checked-in diagnostic JSON Schema for standalone compiler builds.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: main.
Çağrı/yol başvuruları: tools/maintenance/generate_diagnostic_schema.py.

### `tools/maintenance/Move-StaleNestedTrees.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root=(Resolve-Path (Join-Path $PSScriptRoot "..\.."))
[switch]$Apply
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/Recover-MissingAuditTools.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
[string]$RagRoot = ''
[string]$X86Source = ''
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: tools\audit\uxb_ast_contract_audit.py, tools\audit\uxb_ast_contract_build_matrix.py, tools\audit\uxb_ast_contract_collect_contract_nodes.py, tools\audit\uxb_ast_contract_collect_handlers.py, tools\audit\uxb_ast_contract_collect_parser_nodes.py, tools\audit\uxb_ast_contract_fake_status_scan.py, tools\audit\uxb_ast_contract_gate.py, tools\audit\uxb_step1_surface_core.py, tools\control\uxb_surface_lifecycle_matrix.py, tools\release\uxb_release_gate.py, tools\tests\uxb_all_yama_tests.py, tools\tests\uxb_discover_and_run_all_sources.py.

### `tools/maintenance/Restore-CodexCompositePatch.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory = $true)]
    [string]$BackupRoot
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/Restore-CodexPatchSet.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$CompositeBackup = 'build\patch_backup_composite_20260726_222346'
[string]$PostQuickJsBackup = 'build\patch_backup_post_quickjs_ffi_20260726_222222'
[string]$NestedTreeQuarantine = 'build\quarantine_nested_20260726_222416'
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
```
Rutinler: Resolve-UnderRoot.
Çağrı/yol başvuruları: Restore-CodexCompositePatch.ps1.

### `tools/maintenance/uxb_acceptance_inventory.py`

Source-derived registration inventory. Registration never implies acceptance.

```text
parser.add_argument('--output', default='reports/acceptance_inventory')
parser.add_argument('--tools', action='store_true', help='Inventory script sources and update the existing tool guide; do not execute tools.')
parser.add_argument('--guide', default='docs/SON_DAGITIM_DERLEME_VE_TEST_REHBERI_20260729_TR.md')
```
Rutinler: tool_catalog, read, add, case_function.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/uxb_cloud_notebook.py`

Produce the portable Colab/Kaggle QLoRA notebook; no local GPU fiction.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: md, code.
Çağrı/yol başvuruları: sys.exe.

### `tools/maintenance/uxb_cloud_training.py`

Build a traceable cloud training package from current, grouped source data.

```text
p.add_argument('--compiler', type=Path, required=True)
```
Rutinler: sha, dump, build, admit, precheck, find, union.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/uxb_context_index.py`

Offline, hash-deduplicated document search; uses only Python's standard library.

```text
find.add_argument('query')
find.add_argument('--limit', type=int, default=6)
find.add_argument('--chars', type=int, default=6000)
```
Rutinler: connect, paths, build, search, flush.
Çağrı/yol başvuruları: db.exe.

### `tools/maintenance/uxb_coordination_inventory.py`

Mechanical coordination inventory; recorded status is not semantic acceptance.

```text
p.add_argument('--output', default=str(ROOT / 'reports/coordination_status'))
```
Rutinler: sid, main.
Çağrı/yol başvuruları: yok.

### `tools/maintenance/uxb_dead_code_scan.py`

uxb_dead_code_scan.py -- FreeBASIC kaynak agacinda "tohum" dosyadan baslayarak yalniz olu koda bagli dosyalari bulur.  Amac : Bir dosya cagrilmiyorsa (tohum), ona bagli olup BASKA HICBIR canli kod tarafindan kullanilmayan dosyalari kanitla        (sembol duzeyinde cagri grafi, sabit noktaya kadar). Tasima/silme karari icin DOGRULAMA aracidir; dosyaya yazmaz. Girdi: --seed src/backend/backend_pipeline.fbs  (birden fazla verilebilir)   --root <depo koku, varsayilan cwd> Cikti: stdout raporu (olu dosya kumesi, her dosya icin kanit, canli kalanlar ve nedenleri, include eden dosyalar,        betik/belge adlari). --json yol verilirse ayni bilgi JSON. Yontem: FreeBASIC buyuk/kucuk harf duyarsiz. Yorum ve metin sabitleri atilir. Ad -> tanimlayan dosya ve her ad icin        kullanan dosyalar cikarilir. Bir dosya, tanimladigi HER adin kullanicilari (Declare satirlari haric) olu kume ya da        kendisi icindeyse olu sayilir. Yalniz tohumun bagimliliklari (include ettigi ya da adini kullandigi dosyalar)        aday olur; boylece ilgisiz yetim dosyalar karismaz. Sinir : Ad temelli (bir ad baska anlamda baska dosyada gecerse "canli" sayilir: muhafazakar). Ust duzey calisan deyimler        "uyari" olarak listelenir; elle bakilmali. Makro ile uretilen adlar ve dinamik ad olusturma bulunamaz. Ornek : python tools/maintenance/uxb_dead_code_scan.py --seed src/backend/backend_pipeline.fbs --skip uxbasic_hamle3 Secenekler: --seed DOSYA (zorunlu, tekrarlanir)  --root KOK  --src KLASOR (src)  --also KLASOR... (tests compiler tools; canli kullanici        sayilan ek klasorler)  --skip PARCA (yolunda parca gecen dosyalari atlar; arsiv yama klasorleri icin)  --json YOL Cikis kodu: 1 = olu kumenin bir adi olu kume disindan kullaniliyor (tasima guvenli degil), 0 = temiz.

```text
ap.add_argument('--seed', action='append', required=True, help='tohum dosya (kokten goreli); tekrar edilebilir')
ap.add_argument('--root', default=os.getcwd())
ap.add_argument('--src', default='src', help='ana kaynak klasoru (varsayilan src)')
ap.add_argument('--also', nargs='*', default=['tests', 'compiler', 'tools'], help='canli kullanici sayilan ek klasorler')
ap.add_argument('--json', help='sonucu JSON olarak yaz')
ap.add_argument('--skip', action='append', default=[], help='yolunda bu parca gecen dosyalari atla (arsiv yama klasorleri); tekrar edilebilir')
```
Rutinler: strip_line, walk_sources, parse, main, resolve_inc.
Çağrı/yol başvuruları: tools/maintenance/uxb_dead_code_scan.py, uxb_dead_code_scan.py.

### `tools/maintenance/uxb_knowledge_watch.py`

Local source-map/RAG maintenance. Never launches an AI coding agent.

```text
parser.add_argument('--once', action='store_true')
parser.add_argument('--interval', type=int, default=60)
parser.add_argument('--budget', type=int, default=64)
parser.add_argument('--quiet', type=int, default=120)
```
Rutinler: snapshot, write, command, cycle, main.
Çağrı/yol başvuruları: sys.exe, tools/Moduller/paketleyici31.py, tools/uxb_chroma_index.py.

### `tools/maintenance/uxb_toolchain_probe.py`

Record GCC's required clock symbols and verify a locally isolated C build.  Read-only outside the report directory and disposable scratch. No DLL replacement or package update. pefile is used only for inspection, not by the compiler.

```text
parser.add_argument('--output', required=True)
parser.add_argument('--msys-bin', default='C:/msys64/ucrt64/bin')
```
Rutinler: inspect_pe, main.
Çağrı/yol başvuruları: gcc.exe, probe.exe.

### `tools/maintenance/uxb_wasm_value_runtime.py`

Embed the readable WASM value runtime without changing JavaScript bytes.

```text
parser.add_argument('--check', action='store_true')
```
Rutinler: generate.
Çağrı/yol başvuruları: tools/maintenance/uxb_wasm_value_runtime.py.

### `tools/memory_runtime_snapshot.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string[]]$Executables = @()
[int]$Repeat = 3
[int]$TimeoutSeconds = 30
[int]$SampleIntervalMs = 25
[string]$OutputCsv = "reports/runtime_memory_snapshot.csv"
[switch]$UseAllRunExe
[switch]$FailOnError
```
Rutinler: Resolve-ExecutablePath, Get-ExecutableTargets, Update-Peaks.
Çağrı/yol başvuruları: _64.exe.

### `tools/package_uxwasm_distribution.cmd`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0package_uxwasm_distribution.ps1, powershell.exe, pwsh.exe.

### `tools/package_uxwasm_distribution.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..'))
[string]$OutputDirectory = ''
[switch]$SkipGate
```
Rutinler: Copy-Tree.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\tests\libraries\uxwasmrt\verify_distribution.py, .\tools\wabt\bin\wat2wasm.exe, bin\uxb.exe, run_uxwasmrt_gate.ps1, tests\libraries\uxwasmrt\test_uxwasmrt.py, tests\libraries\uxwasmrt\verify_distribution.py, tools\wabt\bin\wasm-validate.exe, tools\wabt\bin\wat2wasm.exe.

### `tools/pdsx/uxbasic2pdsxS/run_uxbasic_to_pdsx.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory = $true)]
    [string]$Source
[Parameter(Mandatory = $true)]
    [string]$Out
[string]$ProjectName = ""
[string]$Profile = ""
[string]$Uxb = ""
[switch]$StrictDiagnostics
[switch]$StrictCoverage
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, uxb.exe, uxbasic2pdsxS.py.

### `tools/pdsx/uxbasic2pdsxS/tests/test_smoke.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: run_bridge, test_smoke_source_first_comments_and_call_notes, test_structural_fallback_handles_expression_nodes.
Çağrı/yol başvuruları: sys.exe, uxbasic2pdsxS.py.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/__init__.py`

uXBasic AST JSON -> pdsX BASX/project bridge.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/cli.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
p.add_argument('--json-dir', required=True, help="uXBasic'in tüm JSON çıktılarının bulunduğu klasör")
p.add_argument('--ast-json', default='', help='Varsayılan yerine kullanılacak AST JSON dosyası')
p.add_argument('--source', default='', help='Yorumları aynen taşımak için kaynak veya preprocessed uXBasic dosyası')
p.add_argument('--out', required=True, help='Üretilecek pdsX proje klasörü')
p.add_argument('--project-name', default='uxb_generated', help='pdsX proje adı')
p.add_argument('--profile', default='', help='pdsX profile adı; örn. py30_std, py30_thirdparty, ai_pack')
p.add_argument('--profiles-dir', default='profiles/', help='project.prj içine yazılacak profiles yolu')
p.add_argument('--headers-dir', default='hx/', help='project.prj içine yazılacak hx/headers yolu')
p.add_argument('--copy-profiles-from', default='', help='Hazır profiles klasörünü çıktı içine kopyala')
p.add_argument('--copy-hx-from', default='', help='Hazır hx klasörünü çıktı içine kopyala')
p.add_argument('--requirement', action='append', default=[], help='project.prj [requirements] package satırı; birden çok verilebilir')
p.add_argument('--strict-diagnostics', action='store_true', help='lexer/parser diagnostics JSON hata içerirse dur')
p.add_argument('--strict-coverage', action='store_true', help='AST node kapsam raporunda işlenmemiş node varsa hata kodu 30 ile dur')
p.add_argument('--no-profile-line', action='store_true', help='main.basx başına PROFILE satırı yazma')
```
Rutinler: parse_args, main.
Çağrı/yol başvuruları: yok.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/emitter.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: __init__, _register_handlers, convert, node_key, count_all_nodes, mark_handled, mark_tree_handled, emit_node, emit_line, source_exact, emit_source_or, add_call_dll_api_notes_if_needed, emit_program, emit_block, emit_generic, emit_passthrough_stmt, emit_dim_stmt, emit_redim_stmt, emit_const_stmt, emit_assign_stmt, emit_expr_stmt, emit_print_stmt, emit_input_stmt, emit_if_stmt, emit_elseif_part, emit_else_part, emit_select_stmt, emit_case_block, emit_case_else, emit_for_stmt, emit_for_each_stmt, emit_do_stmt, emit_do_each_stmt, emit_exit_stmt, emit_return_stmt, emit_label_stmt, emit_call_stmt, emit_try_stmt, emit_unary_stmt, emit_assert_stmt, emit_incdec_stmt, emit_inline_stmt, emit_type_stmt, emit_type_field, emit_class_stmt, emit_class_field, emit_class_friend_stmt, emit_method_stmt, emit_constructor_stmt, emit_destructor_stmt, emit_operator_stmt, emit_property_stmt, emit_property_accessor_stmt, emit_interface_stmt, emit_interface_method_decl, emit_enum_stmt, emit_sub_stmt, emit_function_stmt, emit_routine, emit_module_stmt, emit_namespace_stmt, emit_main_stmt, emit_named_block, emit_event_like_stmt, emit_passthrough_block, params, reconstruct_statement, expr, is_statement_like, is_expression_like, walk, walk.
Çağrı/yol başvuruları: .hx/.py.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/loader.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: load_json, discover_file, load_ast, load_optional_json, diagnostics_have_errors, extract_profile_from_preprocess_result.
Çağrı/yol başvuruları: yok.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/model.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: index, kind, value, op, line, column, role, type_name, symbol, flags, source_file, children, left, right, child_kind, children_kind, child_role, visible_children, count_node, count_handled, warn, error.
Çağrı/yol başvuruları: yok.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/project_writer.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: write_text, write_project, write_report, write_usage_doc.
Çağrı/yol başvuruları: \\pdsx_wrapper\\pdsx_cli.py.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS/source_model.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: read_text_any, split_basic_inline_comment, is_full_comment_or_blank, empty, from_path, discover, has_line, raw_line, statement_line, mark_emitted, pending_comments_before, remaining_comments, inline_comment.
Çağrı/yol başvuruları: yok.

### `tools/pdsx/uxbasic2pdsxS/uxbasic2pdsxS.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/perf_runtime_benchmark.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string[]]$Executables = @()
[int]$Repeat = 5
[int]$TimeoutSeconds = 30
[string]$OutputCsv = "reports/runtime_perf_benchmark.csv"
[switch]$UseAllRunExe
[switch]$FailOnError
```
Rutinler: Resolve-ExecutablePath, Get-ExecutableTargets, Get-PercentileValue, Convert-ToInvariantNumberString, Get-CompactErrorMessage.
Çağrı/yol başvuruları: _64.exe, row.exe.

### `tools/phase_commit_push.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory = $true)]
    [string]$Message
[switch]$SkipGate
[switch]$SkipPush
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\tools\run_faz_a_gate.ps1.

### `tools/release/package_uxbasic_buildable_source.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
[string]$OutputDirectory = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: BUILD_UXB_LIBRARY_SYSTEM.ps1, RUN_UXCLAZZ_UXBDLL_WINDOWS_TESTS.ps1, \.py, build.bat, build_32.bat, build_64.bat, build_release.bat, tools\FreeBASIC-1.10.1-win64\fbc.exe, tools\release\package_uxbasic_buildable_source.ps1.

### `tools/release/package_uxbasic_distribution_final.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Root
[Parameter(Mandatory=$true)][string]$GateSummary
[string]$OutputDirectory = ''
[switch]$KeepStage
```
Rutinler: Copy-TreeFiltered, Assert-Pe64.
Çağrı/yol başvuruları: \.py, bin\uxb.exe, tools\pdsx\uxbasic2pdsxS\run_uxbasic_to_pdsx.ps1, tools\uxbdll\uxbdll.py, tools\uxclazz\uxclazz.py, uxb.exe, uxb\.exe.

### `tools/release/package_uxbasic_full_pck_outside_dist.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
[string]$OutputRoot = ""
```
Rutinler: Copy-Tree.
Çağrı/yol başvuruları: .\VERIFY_PACKAGE.ps1, VERIFY_PACKAGE.ps1, bin\uxb.exe, uxb.exe.

### `tools/release/uxb_release_gate.py`

Adım 18 release gate.  Aggregates lifecycle matrix, blockers, tests, expected/actual comparison and backend/release artifacts. It does not modify source code.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--strict', action='store_true')
ap.add_argument('--allow-skips', action='store_true')
ap.add_argument('--require-backend-outputs', action='store_true')
```
Rutinler: find_uxb_root, read_csv, read_json, latest_existing, locate_matrix, count_empty_cells, count_status, load_blocker_csvs, make_release_candidate, main.
Çağrı/yol başvuruları: yok.

### `tools/release_mini.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%~1
%~2
--cached
--exclude-standard
--exit-code
--notes
--others
--publish
--quiet
--tags
--title
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \uXbasic_main_32.exe, \uXbasic_main_64.exe, \uXbasic_manifest_smoke.exe, build.bat, build_matrix.bat, tests\run_manifest.exe, tools\release_mini.bat.

### `tools/run_err_codegen_parity_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$OutReport = "reports/err_codegen_parity_gate_report.md"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: t.exe, tests/run_err_backend_hooks_64.exe, tests/run_err_codegen_parity_gate_64.exe, tests/run_err_mir_lowering_64.exe, tests/run_err_semantic_pass_64.exe, tools/FreeBASIC-1.10.1-win64/fbc.exe.

### `tools/run_faz_a_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$SkipBuild
[switch]$SkipStructureGate
[switch]$StrictStructureGate
```
Rutinler: Invoke-Step.
Çağrı/yol başvuruları: .\tools\run_err_codegen_parity_gate.ps1, .\tools\validate_module_quality_gate.ps1, .\tools\validate_reference_integrity.ps1, .\tools\validate_test_naming.ps1, build_64.bat, tests\run_call_dll_x64_runtime_smoke_64.exe, tests\run_call_dll_x64_signature_runtime_smoke_64.exe, tests\run_call_exec_64.exe, tests\run_call_user_exec_ast_64.exe, tests\run_case_is_exec_ast_64.exe, tests\run_class_access_friend_parse_64.exe, tests\run_class_access_override_virtual_exec_ast_64.exe, tests\run_class_ctor_dtor_exec_ast_64.exe, tests\run_class_dtor_scope_exit_exec_ast_64.exe, tests\run_class_inheritance_virtual_exec_ast_64.exe, tests\run_class_method_dispatch_call_expr_exec_ast_64.exe, tests\run_class_method_dispatch_exec_ast_64.exe, tests\run_class_oop_transition_exec_ast_64.exe, tests\run_class_this_me_binding_exec_ast_64.exe, tests\run_cmp_interop_64.exe, tests\run_collection_engine_exec_64.exe, tests\run_collection_types_exec_64.exe, tests\run_console_state_exec_ast_64.exe, tests\run_core_types_exec_ast_64.exe, tests\run_decl_directive_exec_ast_64.exe, tests\run_deftype_setstringsize_exec_64.exe, tests\run_diagnostics_log_64.exe, tests\run_dim_const_test_64.exe, tests\run_dim_redim_exec_ast_64.exe, tests\run_each_exec_64.exe, tests\run_end_exec_ast_64.exe, tests\run_exit_if_byval_parse_exec_64.exe, tests\run_file_io_exec_ast_64.exe, tests\run_file_io_exec_ast_negative_64.exe, tests\run_file_io_runtime_64.exe, tests\run_floating_point_exec_64.exe, tests\run_flow_io_exec_ast_64.exe, tests\run_if_exec_ast_64.exe, tests\run_inline_x64_backend_64.exe, tests\run_input_exec_ast_64.exe, tests\run_jump_exec_ast_64.exe, tests\run_layout_intrinsics_64.exe, tests\run_manifest_64.exe, tests\run_memory_exec_ast_64.exe, tests\run_memory_pointer_semantics_64.exe, tests\run_memory_stride_failfast_64.exe, tests\run_memory_vm_64.exe, tests\run_memory_width_semantics_64.exe, tests\run_namespace_module_main_parse_64.exe, tests\run_percent_preprocess_control_failfast_64.exe, tests\run_percent_preprocess_exec_64.exe, tests\run_percent_preprocess_ifc_exec_64.exe, tests\run_pointer_intrinsic_contract_64.exe, tests\run_print_exec_ast_64.exe, tests\run_print_zone_exec_ast_64.exe, tests\run_return_exec_ast_64.exe, tests\run_runtime_intrinsics_64.exe, tests\run_this_me_semantic_pass_64.exe, tests\run_w1_semantic_pass_64.exe.

### `tools/run_faz_b2_failfast.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$SkipBuild
```
Rutinler: Invoke-Step.
Çağrı/yol başvuruları: .\tools\run_layout_indexed_failfast.ps1, .\tools\run_memory_stride_failfast.ps1, .\tools\run_memory_width_failfast.ps1.

### `tools/run_layout_indexed_failfast.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$SkipBuild
```
Rutinler: Invoke-Step.
Çağrı/yol başvuruları: build_64.bat, tests\run_layout_intrinsics_64.exe.

### `tools/run_memory_stride_failfast.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$SkipBuild
```
Rutinler: Invoke-Step.
Çağrı/yol başvuruları: build_64.bat, tests\run_memory_stride_failfast_64.exe.

### `tools/run_memory_width_failfast.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$SkipBuild
```
Rutinler: Invoke-Step.
Çağrı/yol başvuruları: build_64.bat, tests\run_memory_width_semantics_64.exe.

### `tools/run_recovery_tools.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[ValidateSet("testdisk", "photorec", "qphotorec", "recuva", "wise")]
    [string]$Tool = "qphotorec"
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: /Users/mete/AppData/Local/Microsoft/WinGet/Packages/CGSecurity.TestDisk_Microsoft.Winget.Source_8wekyb3d8bbwe/testdisk-7.3-WIP/photorec_win.exe, /Users/mete/AppData/Local/Microsoft/WinGet/Packages/CGSecurity.TestDisk_Microsoft.Winget.Source_8wekyb3d8bbwe/testdisk-7.3-WIP/qphotorec_win.exe, /Users/mete/AppData/Local/Microsoft/WinGet/Packages/CGSecurity.TestDisk_Microsoft.Winget.Source_8wekyb3d8bbwe/testdisk-7.3-WIP/testdisk_win.exe, Files/Recuva/recuva.exe, Recovery/WiseDataRecovery.exe.

### `tools/runtime_memory_benchmark.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string[]]$Executables = @()
[int]$Repeat = 5
[int]$TimeoutSeconds = 30
[string]$OutputCsv = "reports/runtime_memory_benchmark.csv"
[switch]$UseAllRunExe
[switch]$FailOnError
```
Rutinler: Resolve-ExecutablePath, Get-ExecutableTargets, Get-PercentileValue, Update-Peaks.
Çağrı/yol başvuruları: _64.exe.

### `tools/safety_checkpoint.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$SourceRoot = "C:/Users/mete/Downloads/BasicOyunSource/uXBasic_repo"
[string]$BackupRoot = "C:/Users/mete/Backups"
[int]$KeepSnapshots = 10
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/script_bridges/run_lua.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Script
[string[]]$Arguments
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: lua.exe.

### `tools/script_bridges/run_prolog.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Script
[Parameter(Mandatory=$true)][string]$Goal
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: swipl.exe, swipl\bin\swipl.exe.

### `tools/setup_win64_toolchain.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: \fbc.exe, curl.exe, fbc.exe.

### `tools/tests/check_yama6_runtime_dll.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--expect-backend', default='')
```
Rutinler: configure, last_error, run_behavior_smoke, find_root, main, pipe_callback, check.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\objdump.exe, \msys64\ucrt64\bin\x86_64-w64-mingw32-objdump.exe.

### `tools/tests/run_ffi_contract_fix.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[string]$Uxb = ""
[switch]$BuildUxffi
[switch]$RunX64
```
Rutinler: Resolve-FirstExisting, Invoke-UxbExpectPass, Invoke-UxbExpectFail.
Çağrı/yol başvuruları: \msys64\ucrt64\bin\gcc.exe, \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, bin\uxb.exe, ffi_contract_positive.exe, runtime_ext\uxffi\build_uxffi_dll.bat, tools\tests\verify_ffi_contract_patch.py.

### `tools/tests/run_yama6_interpreter_tests.py`

!/usr/bin/env python3

```text
ap.add_argument('--root', default='.')
ap.add_argument('--uxb', default='bin/uxb.exe')
```
Rutinler: find_root, find_exe, run_one, main.
Çağrı/yol başvuruları: bin/uxb.exe, bin/uxb_x64.exe, bin/uxb_x86.exe, root/uxb.exe, uxb.exe.

### `tools/tests/run_yama6_native_x64_tests.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--uxb', default='bin/uxb.exe')
```
Rutinler: find_root, run_process, wait_for_file, main.
Çağrı/yol başvuruları: bin/uxb.exe, program.exe.

### `tools/tests/uxb_all_yama_tests.py`

uXBasic merkezi test runner. - Tek komutla Yama 1.1, Yama 2, Yama 3, Yama 4, Yama 5 testlerini çalıştırır. - Her testin stdout/stderr çıktısını build/all_tests/logs altına yazar. - JSON özetini build/all_tests/summary.json olarak üretir.

```text
ap.add_argument('--exe', default='bin/uxb.exe')
ap.add_argument('--out-root', default='build')
ap.add_argument('--suite', default='all', choices=['all', 'oop', 'task', 'slot', 'trigger', 'tasktable', 'output'])
```
Rutinler: rel, file_text, run_case, main, add.
Çağrı/yol başvuruları: args.exe, bin/uxb.exe.

### `tools/tests/uxb_discover_and_run_all_sources.py`

uXBasic genel kaynak test koşucusu.  Amaç:   tests/examples altındaki .uxb, .uxbh, .bas kaynaklarını keşfeder,   derleyici katmanlarında çalıştırır ve build/source_tests altında raporlar.  Bu araç sahte PASS üretmez. Negatif test adlarını ayrı değerlendirir.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--exe', default='bin/uxb.exe')
ap.add_argument('--paths', default='tests,examples')
ap.add_argument('--ext', default='.uxb,.uxbh,.bas')
ap.add_argument('--out-root', default='build/source_tests')
ap.add_argument('--mode', choices=['safe', 'ast', 'sem', 'int', 'full'], default='safe')
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--quick', action='store_true', help='Ilk 50 dosyayla hizli kontrol')
ap.add_argument('--timeout', type=int, default=60)
ap.add_argument('--fail-on-any', action='store_true', help='Her fail exit code 1 donsun')
ap.add_argument('--include-headers', action='store_true', help='.uxbh dosyalarini da calistir')
ap.add_argument('--include-enum-tests', action='store_true', help='tests\\enum_tests kopyalarini da calistir')
ap.add_argument('--include-harnesses', action='store_true', help='harness ve probe dosyalarini da calistir')
ap.add_argument('--include-target-gates', action='store_true', help="JS/WASM/X64 hedef-gate testlerini de host runner'a dahil et")
```
Rutinler: find_root, safe_id, read_text, is_probably_header, is_enum_duplicate, is_harness_like, classify_negative, phase_order, host_modes_for_phase, phase_from_output, source_policy, discover, run_one, build_modes, main.
Çağrı/yol başvuruları: args.exe, bin/uxb.exe.

### `tools/tests/verify_all_cli_options.py`

Verify every canonical CLI registry option against help and live parsing.

```text
parser.add_argument('--root', default='.')
parser.add_argument('--uxb', default='bin/uxb.exe')
parser.add_argument('--runtime', action='store_true')
```
Rutinler: main.
Çağrı/yol başvuruları: bin/uxb.exe.

### `tools/tests/verify_deep_fix_patch.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--json-out')
```
Rutinler: main, check.
Çağrı/yol başvuruları: yok.

### `tools/tests/verify_ffi_contract_patch.py`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
ap.add_argument('--root', default='.')
ap.add_argument('--json-out', default='')
```
Rutinler: read, main, emit, add.
Çağrı/yol başvuruları: yok.

### `tools/tests/verify_uxclazz_uxbdll_patch.py`

!/usr/bin/env python3

```text
parser.add_argument('--native', action='store_true', help='compile and run uxclz C++ smoke test')
```
Rutinler: run, main.
Çağrı/yol başvuruları: build_program.bat, cmd.exe, interop/toolchain.env.bat, runtime_ext/uxclz/build_uxclz.bat, sys.exe, tools/uxbdll/uxbdll.py, tools/uxclazz/uxclazz.py.

### `tools/tests/verify_uxjsruntime_patch.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--json-out')
```
Rutinler: check, main.
Çağrı/yol başvuruları: yok.

### `tools/tests/verify_uxwasmrt_patch.py`

!/usr/bin/env python3

```text
parser.add_argument('--root', default='.')
parser.add_argument('--json-out', default='')
```
Rutinler: main, check.
Çağrı/yol başvuruları: run_uxwasmrt_gate.ps1, runtime_ext/uxwasmrt/build_uxwasmrt.ps1, runtime_ext/uxwasmrt/fetch_wasm_deps.ps1, tests/libraries/uxwasmrt/test_uxwasmrt.py, tests/libraries/uxwasmrt/verify_distribution.py, tools/package_uxwasm_distribution.ps1.

### `tools/tools/library_tools/uxb_c_full_bindgen.py`

Generate complete raw uXBasic bindings from a public C header surface.  The generator does not hand-pick convenience methods.  It scans every public FunctionDecl matching the library manifest, verifies the actual PE DLL export table, emits one uXBasic routine per C function, and emits C shims for public static-inline functions.  Private symbols and function-like preprocessor macros are outside the DLL function surface.  Variadic functions are represented by their original name plus a final uxcapi Args handle.

```text
parser.add_argument('--root', required=True)
parser.add_argument('--manifest', required=True)
parser.add_argument('--clang', required=True)
parser.add_argument('--objdump', required=True)
parser.add_argument('--include-root', required=True)
parser.add_argument('--dll', required=True)
parser.add_argument('--profile', choices=['stable', 'experimental'], default='stable')
parser.add_argument('--target', default='x86_64-w64-windows-gnu')
parser.add_argument('--report-dir', required=True)
parser.add_argument('--allow-no-exports', action='store_true')
```
Rutinler: run, walk, matches_any, sanitize_identifier, clean_type, format_define, is_const_char_pointer, is_wchar_pointer, map_c_type, extract_return_type, parse_exports, enum_value, parse_simple_macros, clang_ast, build_typedef_map, resolve_typedef, safe_type_name, find_owned_record_id, build_record_map, lookup_record, function_from_node, default_value, emit_failure, emit_indirect_return_function, emit_function, c_parameter_declaration, c_shim_parameter, indirect_types, emit_inline_shim, emit_u64_zero_arg_call, field_memory_methods, emit_type_helpers, emit_module, main, make_info.
Çağrı/yol başvuruları: yok.

### `tools/uxb_local_patch_agent.py`

Local, API-key-free patch agent for Python, FreeBASIC and C sources.  Dry-run is the default.  The model may propose only a unified diff; this tool validates paths, applies through ``git apply`` and keeps timestamped backups.

```text
parser.add_argument('request', nargs='?', help='istenen degisiklik')
parser.add_argument('--root', default='.')
parser.add_argument('--model', default='qwen2.5:3b')
parser.add_argument('--ollama', default='http://127.0.0.1:11434')
parser.add_argument('--timeout', type=int, default=300)
parser.add_argument('--apply', action='store_true', help='dogrulanmis yamayi uygula')
parser.add_argument('--patch-file', help='Ollama yerine mevcut unified diff dosyasini denetle')
```
Rutinler: run, safe_relative, extract_diff, collect_context, ask_ollama, validate_diff, backup_and_apply, verify_changed_files, main.
Çağrı/yol başvuruları: fbc64.exe, sys.exe.

### `tools/uxbdll/uxbdll.py`

uxbdll: link an existing uXBasic x64 ASM/OBJ build directory as a Win64 DLL.  This tool intentionally does not modify the uXBasic compiler. It consumes the artifacts already emitted by the x64 build pipeline:   program.asm, obj/program.obj, program_link_args.rsp, interop/toolchain.env.bat  It validates exported NASM symbols, writes a GNU/MinGW .def file, generates a CALL(DLL) wrapper, and writes a reproducible build_dll.bat script.

```text
parser.add_argument('--manifest', required=True, type=Path)
parser.add_argument('--force', action='store_true', help='overwrite generated files')
parser.add_argument('--run', action='store_true', help='run generated build_dll.bat on Windows')
parser.add_argument('--verify-only', action='store_true', help='audit an already-built DLL')
parser.add_argument('--version', action='version', version=VERSION)
```
Rutinler: _norm_type, _safe_ident, _bat_quote, _load_json, _resolve, parse_config, scan_globals, promote_existing_labels_to_globals, validate_artifacts, render_def, render_wrapper, render_uxmh, render_build_bat, write_outputs, verify_dll, main.
Çağrı/yol başvuruları: \\build_program.bat, \\interop\\toolchain.env.bat, \msys64\mingw64\bin\objdump.exe, \msys64\ucrt64\bin\objdump.exe, build_dll.bat, build_program.bat, cmd.exe, interop/toolchain.env.bat.

### `tools/uxclazz/uxclazz.py`

UXClazz source generator.  Transforms a deliberately small, line-oriented CLAZZ surface into ordinary uXBasic CLASS/INTERFACE/MAGIC/PROPERTY code. The compiler core is untouched.  Supported MVP surface:   CLAZZ VALUE|DATA|ENTITY|COMPONENT|ACTOR|NATIVE Name [EXTENDS Base]       IMPLEMENTS IOne, ITwo       USES TraitA, TraitB       DERIVE EQ, HASH, CLONE, TOSTRING, JSON       DECORATOR Name[(args)]       [READONLY] FieldName AS Type   END CLAZZ  The generated code is intentionally transparent and auditable.

```text
parser.add_argument('source', type=Path)
parser.add_argument('-o', '--output', required=True, type=Path)
parser.add_argument('--manifest', type=Path)
parser.add_argument('--check', action='store_true', help='parse and report without writing generated source')
parser.add_argument('--version', action='version', version=VERSION)
```
Rutinler: strip_comment, split_names, validate_classes, parse_text, is_string, is_float, backing_name, value_to_string, hash_expr, render_constructor, render_equals, render_hash, render_clone, render_tostring, render_json, render_trait_accessors, render_metadata, render_class, render, manifest, main, reserve.
Çağrı/yol başvuruları: yok.

### `tools/uxotcc_final_release/bootstrap/scripts/bootstrap_windows.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = $env:UXB_EXE
[string]$Gcc = $env:UXB_GCC
[string]$Nasm = "nasm"
```
Rutinler: Resolve-Exe, Invoke-Checked, Assert-SameFile.
Çağrı/yol başvuruları: ..\..\bin\uxb.exe, ..\bin\uxb.exe, .\bin\uxb.exe, .\bootstrap\stages\uxotcc_stage1.exe, .\bootstrap\stages\uxotcc_stage2.exe, .\scripts\build.ps1, bootstrap\stages\uxotcc_stage0.exe, bootstrap\stages\uxotcc_stage1.exe, bootstrap\stages\uxotcc_stage2.exe, build\uxotcc.exe.

### `tools/uxotcc_final_release/bootstrap/scripts/compile_c.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[Parameter(Mandatory=$true)][string]$Source
[string]$Compiler = ".\build\uxotcc.exe"
[string]$OutBase = ".\build\program"
[string]$Nasm = "nasm"
[string]$Gcc = "gcc"
[string]$Wat2Wasm = "wat2wasm"
[switch]$SkipNative
[switch]$SkipWasm
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\build\uxotcc.exe, base.exe.

### `tools/uxotcc_final_release/scripts/build.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Uxb = $env:UXB_EXE
[string]$Source = "examples\fib.c"
[switch]$BootstrapMode
[switch]$SkipUxbBuild
[switch]$SkipNative
[switch]$SkipWasm
[switch]$EnableAsyncValidation
```
Rutinler: Resolve-Uxb, Invoke-Checked.
Çağrı/yol başvuruları: ..\..\bin\uxb.exe, ..\bin\uxb.exe, .\bin\uxb.exe, .\build\program.exe, .\build\uxotcc.exe, \...\bin\uxb.exe, build\program.exe, build\uxotcc.exe, generated.exe, scripts/build.ps1.

### `tools/validate_matrix_psrt_ok.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$MatrixPath = 'reports/uxbasic_operasyonel_eksiklik_matrisi.md'
[string]$AllowListPath
[switch]$Strict
```
Rutinler: Resolve-RepoPath, Normalize-CellText, Normalize-KeyText, Split-MarkdownRow, Is-MarkdownSeparatorRow, Build-AllowKey, Parse-AllowList, Parse-MatrixPsrt.
Çağrı/yol başvuruları: yok.

### `tools/validate_module_quality_gate.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[switch]$Strict
```
Rutinler: Normalize-RelPath, Get-SourceCategory, Is-HeaderLine, Resolve-IncludePath, Visit-Dependency.
Çağrı/yol başvuruları: yok.

### `tools/validate_reference_integrity.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: Add-Issue, Get-RequiredPath.
Çağrı/yol başvuruları: yok.

### `tools/validate_test_naming.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: yok.

### `tools/verify_typed_task_patch.py`

!/usr/bin/env python3

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: check, read.
Çağrı/yol başvuruları: yok.

### `tools/x64_compare/run_with_timeout.ps1`

S-025: timeout-bounded process runner used by the compiler's --x64-mode BOTH real-execution comparison (backend_x64_real_execution_compare.fbs). Runs one built executable with stdin closed (never blocks waiting for input), captures stdout/stderr to files, and kills it if it runs past the timeout instead of hanging the compiler on a user program with an infinite loop.  Exit code: the child process's own exit code, or 124 on timeout (matches the conventional GNU coreutils `timeout` sentinel).

```text
[Parameter(Mandatory = $true)][string]$ExePath
[Parameter(Mandatory = $true)][string]$StdoutPath
[Parameter(Mandatory = $true)][string]$StderrPath
[int]$TimeoutMs = 10000
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: taskkill.exe.

### `uninstall_old_uxbasic_extensions.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0vscode-extension\scripts\remove_old_uxbasic_extensions.ps1, powershell.exe.

### `UXB-Common.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.
```
Rutinler: Get-UxbRunnerRoot, Get-UxbExePath, New-UxbRunId, Get-UxbPeImportedDllNames, Get-UxbRuntimeDllClosure, New-UxbSafeName, Ensure-Dir, Write-TextFileUtf8, Invoke-UxbLogged, Find-Wat2Wasm, New-HeaderDriverIfNeeded, Copy-BrowserFallbackIfNeeded.
Çağrı/yol başvuruları: \msys64\mingw64\bin\wat2wasm.exe, \msys64\ucrt64\bin\wat2wasm.exe, bin\uxb.exe, tools\wabt\bin\wat2wasm.exe, wabt\bin\wat2wasm.exe, wat2wasm.exe.

### `uxb.cmd`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
%~1
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0bin\uxb.exe, dp0build\compilers\codex33\uxb.exe, uxb.cmd.

### `UXB_MIR_STRICT_RUNTIME_TESTS_20260711.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[string]$Uxb = ""
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: bin\uxb.exe, r.exe, uxb.exe.

### `UXB_VISIBLE_TEST_RUNNER_20260711.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
[switch]$SkipCompilerBuild
[switch]$RunReleasePipeline
```
Rutinler: Section, Show-FileIfExists.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\build_64.bat, .\compiler\scripts\run_library_abi10_smoke.ps1, .\reports\libraries\tests\abi10\ast.exe, .\reports\libraries\tests\abi10\mir.exe, .\run_yama6_interpreter_tests.bat, .\run_yama6_runtime_abi_tests.bat, .\run_yama7_libuv_backend_tests.bat, .\run_yama8_tbb_backend_tests.bat, .\tests\libraries\abi10\build_abi10_test_dll.bat, .\tool_py\tools\release_runners_py\run_uxb_release_triple_pipeline.py, .\tools\library_tools\uxb_library_abi.py, .\tools\library_tools\uxb_library_export_audit.py, .\tools\library_tools\uxb_library_layout_doctor.py, .\tools\library_tools\uxb_library_source_gate.py, .\tools\wabt\bin\wat2wasm.exe, \msys64\ucrt64\bin\objdump.exe, \msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe, powershell.exe.

### `uxr_calistir.bat`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
%*
%~1
%~2
--help
--ids
--init
--list
--quick
--reserve
--reverse
--run
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: dp0uxr.py, uxr.py, uxr_calistir.bat.

### `UYGULA_LAST2_BIGINIT_FIX.ps1`

Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.

```text
[string]$Root = "."
```
Rutinler: üst düzey komutlar.
Çağrı/yol başvuruları: .\bin\uxb.exe, .\build_64.bat, xtestx\_runners\run_xtestx_project_packs.py.

<!-- UXB_TOOL_CATALOG_END -->
