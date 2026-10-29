# OOP denetimi yoklamaları (2026-10-16 / 2026-10-17)

Mete'nin 2026-10-16 iki belgesini (`docs/tasarim/UXB OPP SISTEMI TASARIM VE TARTISMALARI.md`, `docs/tasarim/uXBasic_OOP_Tam_Sistem_Denetimi_2026-10-16.md`) sınamak için yazılan **küçük programlar** ve düzeltme turunda eklenenler: toplam **170 vaka** (140 + 30). Yorum: kitap bölüm 11.13, `ai_koordinasyon/OOP_DUZELTME_PLANI_20261016.md`, `ai_koordinasyon/DURUM.md` (2026-10-17). Açılan kayıtlar: S-570 … S-599 (G-NESNE-37 … 46, G-JS-15, G-JS-16, G-JS-17, G-WASM-26, G-WASM-27, G-DIL-19, G-TIP-32, G-HIZ-4, G-MODUL-8, G-YORDAM-11, G-YORDAM-12, G-HEDEF-31 … 40); güncellenen eski kayıtlar: S-224, S-234, S-244, S-250, S-360, S-382, S-412, S-431, S-472, S-473, S-483 … S-486, S-544, S-555, S-564.

| Dosya | Vaka | Ne ölçer |
|---|---:|---|
| `iddia_oop1.iddia.json` | 29 | Birinci tur (36 vakadan 7'si çıkarıldı): `DELETE` sonrası okuma, çift `DELETE`, taban tipli `DELETE`, `THIS`/`ME`/`SUPER`, aşırı yükleme, `ABSTRACT/FINAL`, `MIXIN` biçimleri, çoklu kalıtım, `SUPER[Taban]`, tasarım belgesi örnekleri (BankaHesabi, Sekil/Kare, Vektor2D, Ogrenci `PROPERTY` blok biçimi), Türkçe harfli ad, `IS`/`AS`, `CASE IS`, `USING`, `ACTOR`, `DATA_PARALLEL`, `BORROWED`, alan gizleme. Not: kendi adlandırma hatam yüzünden anlamsız kalan yedi vaka (o03, o13–o16, o34, o35: değişken adı sınıf adıyla aynı) ikinci turda düzeltilmiş hâlleriyle yer aldığından bu dosyadan çıkarıldı; ham sonuç dosyasında durur |
| `iddia_oop2.iddia.json` | 47 | İkinci tur: yalnız **sayı yazdıran** sürümler (WASM metin yazamadığı için altı yol karşılaştırılır): `DELETE`, takma ad, taban tipli `DELETE`, sanal çağrı seçimi (üç seviye), kurucuda sanal çağrı, parametreli taban kurucusu, `SUPER(5)`, `ABSTRACT/FINAL/SEALED`, `MIXIN` (tek, iki, `EXTENDS`'li, başlıkta), aynı adlı metotlu karışım, F64 kurucu/yöntem/sanal metot, `MAGIC ADD`, `USING Ng`, `PROPERTY`, Türkçe ad, `NULL`/`NOTHING`, yapısal arayüz, arayüz denetimi, kurucu ve yıkıcı sırası |
| `iddia_oop3.iddia.json` | 30 | Kusurları en küçük programa indirgeme: WASM kurucu/alan, JS parametreli metot (`CALL` ve çok parametre), x64 F64 alan, fabrika işlevi, `PROPERTY` biçimi, sınıf bayrakları, `THIS`/`ME` |
| `iddia_oop4.iddia.json` | 17 | x64 F64 alan aritmetiği (`k + k`, `k * k`, `k * 2.0` …) ve eski AST-x64 F64 kurucu |
| `iddia_oop5.iddia.json` | 17 | Düzeltme sonrası doğrulama: `ME`/`SUPER` çağrıları, `DIM x AS Sinif = ifade` biçimleri (fabrika işlevi, başka değişken, `MAGIC ADD` sonucu, yanlış sınıf reddi), F64 alan aritmetiği ve F32/I32 kontrolleri |
| `iddia_oop6.iddia.json` | 30 | Düzeltme turu 4: `THIS`/`ME`/niteliksiz çağrı matrisi (tek ve üç seviye), kurucu/yıkıcıda sanal ve sanal olmayan çağrı, kurucusuz türetilmiş sınıfta taban kurucusu, boş gövdeli rutinler (`SUB`, `FUNCTION`, `METHOD`, kurucu, yıkıcı), sonucu atanmayan `FUNCTION`/`METHOD` ve `F = değer` sonrası deyimler |
| `../memref_dolu_yoklama.py` | — | `MemoryRef` 4096 yuva sınırı (K-06) |

Her dosya `[{"ad": ..., "kod": ...}]` biçimindedir. **Ham sonuçlar** (her vaka ve motor için çıkış kodu ve ilk çıktı satırları, ikilinin özeti) `docs/kitaplar/_ortak/oop_partisi_20261016/` altındadır:

| Sonuç dosyası | İkili | Ne |
|---|---|---|
| `oop1_sonuc.json` … `oop4_sonuc.json` | `bin\uxb_kilavuz_20261014_0253.exe` (kılavuzun ölçüm ikilisi) | Düzeltmeden **önce** 123 vaka |
| `oop5_sonuc_oop1017.json` | `bin\uxb_oop1017.exe` | düzeltmenin ilk dalgası sonrası 17 vaka |
| `oop1_5_sonuc_oop1024.json` | `bin\uxb_oop1024.exe` | **Düzeltmeden sonra** 140 vaka (oop1 … oop5) |
| `oop6_sonuc_oop1024.json` | `bin\uxb_oop1024.exe` | **Düzeltmeden sonra** 30 ek vaka |
| `oop1_5_fark_0253_oop1024.txt` | — | 140 vakanın eski ve yeni sonucu arasındaki **210 vaka×motor farkı** (hepsi beklenen iyileşme; gerileme yok) |
| `oop1_5_kalan_ayrisma_oop1024.txt` | — | yeni ikilide motorların **hâlâ ayrıştığı** 57 vaka (çoğu WASM'ın bilinen ondalık/metin reddi; gerçek ayrışmalar yaşam döngüsü S-473/S-486/S-574, parametreli taban kurucusu ve `SUPER(...)` S-485/S-487, eski AST-x64 arayüz ve `USING` S-578/S-585) |
| `memref_dolu_olcum.txt`, `heap_ayirma_olcum.txt`, `heap_ayirma_olcum_oop1020.txt` | `0253`, `oop1020` | K-06 ve K-12 ölçümleri (düzeltme öncesi/sonrası) |

Yeniden koşturma (depo kökünden; **çalışma dizini olarak depo kökünü ya da boş bir klasörü kullanın**: `uxb` her koşuda çalışma dizinine `build/<tarih>/` klasörü yazar):

```
python tools\kitap\kilavuz_v2\yoklama\vaka_kos.py kos --uxb bin\uxb_oop1024.exe --klasor tools\kitap\kilavuz_v2\yoklama\iddia_oop_20261016 --motor AST,MIR,x64,JS,WASM,x64a --cikti sonuc.json --is 4
```

Not: `vaka_kos.py` WASM için `tools\wabt\bin\wat2wasm.exe` ve `node` ister. Düzeltmelerin **kalıcı kanıtı** `tests/oop_parity` içindeki testlerdir (S-570 … S-599; 309/309 kontrol `bin\uxb_oop1024.exe` ile geçti); bu klasördeki vakalar keşif ve eski/yeni karşılaştırması içindir.
