# uXBasic Linux calistirma klasoru

uXBasic Windows icin uretilmistir. Bu klasor, derleyiciyi Linux'ta FreeBASIC ile derleyip
**yorumlayicilari (AST, MIR), JS hattini ve JSON ciktilarini** calistirmak icindir. Uretilen x64
(NASM/MinGW) kod ve Windows DLL/FFI Linux'ta calismaz. Asagidaki sonuclar 2026-10-10 tarihinde
FreeBASIC 1.10.1 (Linux x86_64, Ubuntu 24.04, glibc 2.39) ile olculmustur.

## Dosyalar
- `shim/kernel32_shim.c`: Windows `kernel32` cagrilarini Linux'a baglar (derleme/baglama icin).
- `shim/pathfix.c`: `LD_PRELOAD` kutuphanesi; yol argumanlarindaki `\` karakterini `/` yapar.
- `build_linux.sh`: shim'i ve derleyiciyi derler (`FBC_PREFIX` ile fbc dizini verilebilir). ~17 dk surer.
- `run_uxb.sh`: `uxbasic`i pathfix ile calistirir.
- `run_tests.sh`: `run_*_tests.ps1` mantiginin bash karsiligi (AST, MIR, varsa JS).
- `out/`: derleme ciktilari (git'e eklenmez).

## Calisma adimlari
1. FreeBASIC Linux ikilisini indir (apt'te paket yok; GitHub surumleri bu ortamdan 403 verdi):
   SourceForge `FreeBASIC-1.10.1-ubuntu-22.04-x86_64.tar.xz`. Paketten cikar, `FBC_PREFIX` olarak ver.
2. Gelistirme paketleri: `apt-get install libncurses-dev libtinfo-dev libgpm-dev libx11-dev libxext-dev libxpm-dev libxrandr-dev libxrender-dev libgl-dev`, ayrica `gcc`, `ar`, `node` (JS icin).
3. `FBC_PREFIX=/yol/FreeBASIC-1.10.1-ubuntu-22.04-x86_64 linux/build_linux.sh`
4. `gcc -shared -fPIC linux/shim/pathfix.c -o linux/out/libpathfix.so -ldl`
5. `linux/run_uxb.sh run prog.uxb` ; testler: `linux/run_tests.sh tests/array_bounds`
   (calisma dizinine `build/` yazar; depoda degil gecici bir dizinde calistirin).

## Bulgular
**Derleme:** `src/main.bas` ~17 dk'da 23,7 MB C kodu uretir; sonuc 9,4 MB `uxbasic`. Gerekenler:
1. `-lkernel32` ve `-lkernel32.dll`: kaynak yalniz `LoadLibraryA`, `GetProcAddress`, `FreeLibrary`,
   `GetModuleFileNameA` cagirir -> `dlopen`/`dlsym`/`dlclose`/`/proc/self/exe` ile shim'lendi.
2. Baska Windows API'leri baglamada eksik cikti: `CreateFileA`, `CreateFileMappingA`, `MapViewOfFile`,
   `UnmapViewOfFile`, `CloseHandle`, `GetTempPathA`, `GetTempFileNameA`, `IsBadReadPtr`, `IsBadWritePtr`.
   Dosya eslemeleri bilerek **basarisiz** doner (Windows'a ozgu yurutulebilir bellek yolu Linux'ta yok).
3. `-c` ile derlerken `-m main` gerekir; yoksa `undefined reference to main`.

**Calisma zamani:** Derleyici yollari `build\<tarih>\json\...` gibi `\` ile uretir; Linux'ta bu tek parca
klasor adi olur ve `cannot open errors json` hatasi verir. `pathfix.so` (LD_PRELOAD) bunu cozer; kaynak degismedi.
`system()`/`popen()` komut dizeleri cevrilmez; JS hattinda zararsiz `sh: cmd: not found` iletisi cikar.

**Testler (AST + MIR, `.ps1` koşucusunun motor listesine gore; x64/AST-x64 Linux'ta yok):**

| Klasor | Sonuc |
|---|---|
| tests/array_params (inc. majority_vote, majority_none) | 38/38 |
| tests/array_bounds | 24/24 |
| tests/iterators | 26/26 |
| tests/oop_parity | 58/58 |
| tests/memory_model | 14/14 |
| tests/language_guards | 38/46 |

`language_guards` basarisizliklari: 6'si `ABI10 requires bin\uxffi.dll` (Windows FFI DLL'i; Linux'ta beklenen),
2'si `bool_print_float_compare_value` (cikti gorsel olarak ayni; bosluk/satir sonu farki olabilir, incelenmedi).

**Hatlar (majority_vote / majority_none uzerinde):** `run` (AST) ve `--interpreter-backend MIR`, `int`:
beklenen cikti (`2`,`5` / `yok`). `jsw` + `node`: ayni cikti. JSON ciktilari uretilir (89 dosya).
`wat`: dize iceren programda `WAT string linear-memory lowering is not implemented` ile reddeder
(derleyici siniri; Linux'a ozgu degil). Sayisal-yalniz bir programla WAT/WASM denenmedi.
