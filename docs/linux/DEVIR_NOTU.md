# uXBasiC-Linux: Devir Notu ve Yol Haritasi

Bu belge, Windows odakli uXBasic deposundan Linux calismasini ayirmak icin yazildi. Yeni bir oturum/gelistirici
buradan sifirdan baslamadan devam edebilsin diye, **olculenler** ile **varsayimlar** ayri yazildi.

## 1. Neden bu repo
- Gelistirmede LLM'ler Linux'ta calisir; derleyici yalnizca Windows'ta denenebildigi icin hatalar gec bulunuyor, cok token harcaniyor.
- Hedef: **Linux'ta hizli geri bildirim dongusu** (derle -> calistir -> beklenenle karsilastir) ve Linux kullanicisi icin gercek hedef.
- Karar: **MIR'den C uretimi** (MIR->C transpiler), prototip degil **tam destek**. Wine ile Windows ciktisi alma yolu yeterli bir yan yoldur ama Linux kullanicisi icin cozum degildir.

## 2. Olculen durum (2026-10-10 / 10-29)
- FreeBASIC 1.10.1 Linux x86_64 ile `src/main.bas` derlenir (~17 dk, 23,7 MB C). Gerekenler: `linux/` altindaki kernel32 shim
  (`dlopen`/`dlsym`), `-m main` ile `-c` derleme, `pathfix.so` (LD_PRELOAD, `\` -> `/` yol cevirisi). Ayrintilar `linux/README.md`.
- Linux'ta calisanlar: AST ve MIR yorumlayicilari, JS hatti (`jsw` + node), JSON ciktilari.
  `tests/array_params` 38/38, `array_bounds` 24/24, `iterators` 26/26, `oop_parity` 58/58, `memory_model` 14/14, `language_guards` 38/46
  (6 hata `bin\uxffi.dll` = Windows FFI, 2 hata cikti bosluk farki, incelenmedi).
- WAT hatti: dize iceren programi reddeder ("WAT string linear-memory lowering is not implemented") - Linux'a ozgu degil.
- Wine hatti: `bld` -> `program.asm` -> `nasm -f win64` -> MinGW -> `wine prog.exe` basit programlarda yorumlayici ile ayni sonucu verdi.
  `native/uxb_runtime` DLL'i repoda hazir degil; MinGW ile 9 .cpp'den derlenir.
- Olculen kapsam: MIR yorumlayici ~3850 satir, ~276 `Case`; x64 kodgen ~19 bin satir; `src/runtime/exec` ~189 yerlesik etiketi.

## 3. Bilinen hata (once bunu coz/dogrula)
Fonksiyon-yereli degisken ayni adli ust duzey degiskeni golgelemiyor: `tests/array_params/shadow_local_global.uxb`
- AST yorumlayici: `99 / 5` (dogru). MIR yorumlayici: `99 / 99`. Native x64: cop deger + `99`.
- MIR duzeyinde bir ad cozumleme/kapsam hatasi gibi gorunuyor. **MIR->C bunu miras almasin**: C backend yazilmadan once duzeltilmeli.
- Not: ust dal (`main`) bu notun yazildigi tarihte bazi "routine scope" duzeltmeleri aldi; **bu duzeltmeler hatayi gidermis olabilir, dogrulanmadi**
  (Linux derlemesi bu dalda yeniden yapilmadi).
- `majority_vote`/`majority_none` testlerinde yerel ad bu yuzden `m`.

## 4. MIR -> C: tam destek plani
Bitis olcutu: repodaki tum test seti (`tests/**`, `expected/*`) C backend'de **AST yorumlayici ile ayni cikti**. Her asama bir kapi:

0. **Eslik (parity) altyapisi**: `linux/run_tests.sh`'i genislet: motorlar AST, MIR, **C**; MIR'in AST'ten saptigi her test acik hata sayilir
   (MIR'e guvenme: kaynak dogruluk AST yorumlayici + `expected/`).
1. **Cekirdek**: tamsayi/kayan nokta turleri (I8..I64, U8..U64, F32/F64), aritmetik, karsilastirma (`=`/`==`), mantik/bit islemleri, `IF`/`SELECT`/`FOR`/`DO`/`WHILE`, `GOSUB/GOTO`, `SUB`/`FUNCTION`, kapsam ve golgeleme.
2. **Bellek**: sabit/dinamik/`REDIM` diziler, `LBOUND/UBOUND`, dizi parametreleri, `PEEK/POKE`, `VARPTR`, `SIZEOF/OFFSETOF`, `TYPE`.
3. **Metin**: `STRING` degeri, `MID/LEFT/RIGHT/INSTR/VAL/STR/HEX...`, `PRINT`/`INPUT`, dosya G/C.
4. **Koleksiyonlar**: `LIST`/`DICT`/`SET`, `FOR EACH` (C runtime kutuphanesi; yorumlayicidaki `uxcollections` davranisi referans).
5. **Nesne modeli**: `CLASS`, kalitim, `VIRTUAL`, `INTERFACE`, `NEW/DELETE`, ctor/dtor, ozellikler, erisim denetimi.
6. **Hata/akis**: `TRY/CATCH/THROW`, `ON ...`, `ASSERT`, gorevler/`THREAD`/`PIPE`.
7. **FFI**: Windows DLL yerine `dlopen`/`libffi`; `uxffi` ABI10 Linux surumu. Yerel kutuphaneler (`runtime_ext/*`) `.so`.
8. **Genis sayilar**: `F80/F128/BIG*` (`runtime_ext/bigfp`, `fp80`, `fp128`).
9. **Kutuphaneler**: `libsx/*` ve `include/*.uxmh` Linux'ta derlenir; her biri icin testle dogrulama.

Yontem notlari:
- C cikti, tek dosya + kucuk **C runtime** (`runtime/c/`): `uxb_rt.h/.c`. Sayi, metin, koleksiyon yardimcilari burada.
- `gcc`/`clang` ile derle; ASAN/UBSAN ile CI kosulari.
- "Yorumlayici = calistirilabilir sartname": MIR yorumlayicisinin davranisini (`src/interpreter/mir/*`) okuyup C'ye cevir, sonra AST ile dogrula.
- Uretilen C dosyalarini depoya ekleme; testlerde gecici dizinde uret.

## 5. CLI tasarimi (taslak)
Mevcut `--target` (x64, js, wat, wasm, browser) korunur; isletim sistemi ayri eksen:
- `--host-os auto|linux|win11` (derleyicinin calistigi sistem), `--target-os linux|win11`
- `--emit c|asm|js|wat|wasm|exe|elf` (mevcut `--target` ile cakisanlar eslenir)
- `uxb bld prog.uxb --target-os linux` -> C uret, `cc` ile derle, ELF cikar. `--target-os win11` -> mevcut NASM/Win64 hatti (veya MinGW ile C).
- Windows'a ozgu hatlar (Win64 ABI, PE, `.bat`) `--target-os win11` altinda kalir; Linux'ta secilirse acik hata ver.
Derleyicinin kendisi `\`/`/` yol ayrimini isletim sistemine gore yapmali (`pathfix.so` gecici cozum, kaynakta cozulmeli).

## 6. Siradaki somut adimlar
1. Yeni dalda `main`'i Linux'ta yeniden derle (`linux/build_linux.sh`), `shadow_local_global` hatasi duruyor mu bak.
2. `\` -> `/` yol hatasini kaynakta duzelt (`pathfix` gerekmesin).
3. MIR'in veri yapisini (`src/semantic/mir*.fbs`) ve opcode listesini cikar; `docs/linux/MIR_OPCODE_TABLOSU.md`.
4. Asama 0-1'i yap (parity + cekirdek C emitter) ve `tests/array_params` ile dogrula.

## 7. Kisitlar
- Lisans: `LICENSE.md` (source-available) ve `DESIGN-RIGHTS-RESERVED.md` bu repoda da gecerlidir; degisiklik/dagitim izin kurallarina bagli.
- GitHub etiketleri (`git push --tags`) bu ortamdan proxy tarafindan reddedildi (403); etiketler yeni repoya tasinmadi.
- `docs/SON_DAGITIM_DERLEME_VE_TEST_REHBERI_20260729_TR.md` calisma ortaminda "degismis" gorunebilir: satir sonu (CRLF) normalizasyonu, icerik degil.
