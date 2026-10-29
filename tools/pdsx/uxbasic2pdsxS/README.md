# uxbasic2pdsxS v0.2

`uxbasic2pdsxS`, uXBasic'in `json/` klasörüne yöneltilmiş JSON çıktılarını okuyup pdsX'in beklediği proje düzenini üretir.

## Mimari karar

Bu araç uXBasic içine gömülü backend değildir. Ayrı bir ara bağlayıcıdır:

```text
uXBasic -> json/ast.json + diğer json çıktıları -> uxbasic2pdsxS -> pdsX project/basx -> pdsX -> Python
```

## Sabit hedefler

1. Tüm uXBasic AST node türlerini pdsX BASX karşılığına çevirmek veya güvenli şekilde kaynak satırını aynen korumak.
2. `.hx` üretmemek. `.hx` dosyalarını pdsX kullanıcısı/HXA hazırlar.
3. uXBasic yorumlarını (`REM`, `'`, `#`) BASX dosyasına aynen taşımak.
4. `CALL DLL` ve `CALL API` satırlarını aynen geçirmek; altına çözüm notu olarak `REM` eklemek.
5. Kaynak satırı mevcutsa `source-first` davranmak: pdsX karşılığı zaten varsa komutu bozmadan geçirmek.
6. Kaynak satırı yoksa AST yapısından BASX satırı üretmek.
7. Node kapsam raporu üretmek: `reports/node_coverage.csv`.
8. Kaynak haritası üretmek: `reports/source_map.json`.

## v0.2 ile tamamlanan eksikler

- Gerçek AST ağacındaki bütün düğümler baştan sayılır; sadece çıktı veren statement node'ları değil, expression/helper node'ları da kapsam raporuna girer.
- `handled_counts`, expression içinde tüketilen node'ları da işler.
- `unhandled_counts` ve `unhandled_total` rapora eklendi.
- `source_map.json` üretimi eklendi.
- `REDIM_STMT`, `CLASS_FIELD`, `CLASS_FRIEND_STMT`, `CLASS_PROPERTY_GET_STMT`, `CLASS_PROPERTY_SET_STMT`, `INTERFACE_METHOD_DECL`, `MODE_REF`, `ENUM_BASE_TYPE`, `INPUT_FILE_STMT`, `INPUTF_STMT` için daha iyi fallback eklendi.
- `CALL DLL/API` not sistemi korunur.
- Test sayısı artırıldı.

## Varsayılan JSON klasörü

Kullanımda uXBasic'in bütün JSON çıktılarının aynı klasörde olduğunu varsayar:

```text
build/uxb2pdsx/json/
  ast.json
  tokens.json
  lexer_diagnostics.json
  parser_diagnostics.json
  preprocessed.uxb
  preprocess_result.json
```

Minimum gerekli dosya: `ast.json`.

Yorumları aynen taşımak için `preprocessed.uxb` veya `--source` verilmelidir.

## Kullanım

### En kolay kullanım: doğrudan `.uxb` / `.bas` kaynağından

Bu paket uXBasic dağıtımının içindeyse, PowerShell sarmalayıcısı önce gerçek
`uxb.exe` ile AST JSON üretir, sonra pdsX projesine dönüştürür:

```powershell
.\run_uxbasic_to_pdsx.ps1 `
  -Source .\program.uxb `
  -Out .\build\program_pdsx `
  -Profile py30_thirdparty
```

Farklı bir derleyici kullanmak için `-Uxb C:\...\uxb.exe` verilebilir.
`-StrictDiagnostics` lexer/parser hatalarında, `-StrictCoverage` ise
karşılığı bulunmayan AST düğümünde işlemi hata koduyla durdurur.

### Hazır JSON klasöründen

```bat
python uxbasic2pdsxS.py ^
  --json-dir build\uxb2pdsx\json ^
  --out build\pdsx ^
  --project-name main ^
  --profile py30_thirdparty ^
  --profiles-dir C:\pdsx_wrapper\profiles\ ^
  --headers-dir C:\pdsx_wrapper\hx\
```

Hazır pdsX `hx/` ve `profiles/` klasörlerini çıktı içine kopyalamak istersen:

```bat
python uxbasic2pdsxS.py ^
  --json-dir build\uxb2pdsx\json ^
  --out build\pdsx ^
  --project-name main ^
  --profile py30_thirdparty ^
  --copy-profiles-from C:\pdsx_wrapper\profiles ^
  --copy-hx-from C:\pdsx_wrapper\hx
```

`--profile` verilmezse araç `preprocess_result.json` içindeki `profiles` / `manifest profile` bilgisini okumayı dener.

Parser/lexer hata JSON'ları varsa ve hata durumunda üretimi durdurmak istersen:

```bat
python uxbasic2pdsxS.py ^
  --json-dir build\uxb2pdsx\json ^
  --out build\pdsx ^
  --strict-diagnostics
```

AST kapsam raporunda işlenmemiş node kalırsa hata ile durdurmak istersen:

```bat
python uxbasic2pdsxS.py ^
  --json-dir build\uxb2pdsx\json ^
  --out build\pdsx ^
  --strict-coverage
```

## Çıktı

```text
build/pdsx/
  main.prj
  basx/main.basx
  build/
  hx/
  profiles/
  reports/uxbasic2pdsxS_report.json
  reports/node_coverage.csv
  reports/source_map.json
  docs/UXBASIC2PDSXS_USAGE.md
```

## CALL DLL/API politikası

`CALL(DLL, ...)` ve `CALL(API, ...)` satırları değişmeden geçer. Altına şu tür notlar eklenir:

```basic
REM uxbasic2pdsxS: CALL DLL satırı aynen korundu.
REM uxbasic2pdsxS: pdsX/Python tarafında ctypes, cffi, pywin32, pythonnet veya özel .hx/.py sarmalayıcı ile programcı çözer.
```

## Test

```bat
python -m pytest -q
```

Beklenen sonuç:

```text
2 passed
```

## Sınır

Bu araç `.hx` üretmez, Python kütüphane alias'ı taramaz ve pdsX transpiler'ın yerine geçmez. Görevi sadece uXBasic AST JSON verisinden pdsX BASX/proje düzeni üretmektir.
