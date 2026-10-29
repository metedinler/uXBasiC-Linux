# Karar turu yoklamaları (2026-10-15, akşam)

Mete'nin 2026-10-15 akşam karar mesajından sonra, tasarım belgelerinin dayandığı olguları (ve yan bulguları) ölçmek için yazılan **53 küçük program**. Yorum: `docs/tasarim/UXB_S550_S551_DATA_READ_RESTORE_VE_VERI_SABITLERI_20261015_TR.md` Bölüm 2 ve `ai_koordinasyon/DURUM.md` (2026-10-15 18:35). Açılan kayıtlar: S-565 … S-569; S-326'ya ek ölçüm.

| Dosya | Vaka | Ne ölçer |
|---|---:|---|
| `iddia_karar2.iddia.json` | 20 | `_` satır devamı ✔, ayraç içi satır sonu ✖, tür çıkarımı ✖, `a()` bütün-dizi yazımı ✖, `data`/`read`/`restore` adlı değişkenler ✔, etiket, `CONST` ifadeli dizi sınırı, `DECLARE` ile ve `DECLARE`siz ileri çağrı, `FILE_HANDLE`, kanal değişkeni, `TRUE`/`FALSE` değerleri |
| `iddia_karar3.iddia.json` | 8 | `SUB` ve `FUNCTION` içinde etiket ve `GOTO` (S-566, S-567), `UBOUND`/`LBOUND` |
| `iddia_karar4.iddia.json` | 5 | `CONST` ifadeli ve adlı dizi sınırı (S-326, S-565), `FUNCTION` içi etiket iletisi |
| `iddia_karar5.iddia.json` | 6 | `CONST` adlı sınırın MIR-x64'te davranışı; sonuç dört derlemede (`20261007`, `20261013_1341`, `20261013_2333`, `20261014_0253`) aynı: süregelen sınır, gerileme değil |
| `iddia_karar6.iddia.json` | 8 | Dizi bildirim biçimleri (`DIM a()`, `REDIM`), çok boyutlu dizi, dizi için skaler başlangıç değeri (S-568), `LIST_NEW`, `DICTSET` |
| `iddia_karar7.iddia.json` | 6 | `DICTHAS`/`SETHAS` doğru değeri (S-569), dizi skaler başlangıç değeri |

Her dosya `[{"ad": ..., "kod": ...}]` biçimindedir. Ham sonuçlar (her vaka ve motor için ilk çıktı satırları, ikilinin özeti, zaman): `docs/kitaplar/_ortak/karar_partisi_20261015/karar*_sonuc.json`; `karar5_surum_*.json` aynı altı vakanın dört derlemedeki MIR-x64 sonucudur.

Yeniden koşturma (depo kökünden):

```
python tools\kitap\kilavuz_v2\yoklama\vaka_kos.py kos --uxb bin\uxb_kilavuz_20261014_0253.exe --klasor tools\kitap\kilavuz_v2\yoklama\iddia_karar_20261015 --motor AST,MIR,x64,JS,WASM,x64a --cikti sonuc.json --is 5
```

Not: `iddia_karar2` içindeki `c15` vakası çalışma klasörüne `karar2_deneme.txt` yazar (AST ve MIR göreli yolu kullanır); koşucu çalıştırıldıktan sonra bu 3 baytlık dosya silinebilir.
