# Tasarım soruları vaka partisi (2026-10-15)

Mete'nin 2026-10-15 tarihli sekiz tasarım sorusunu ölçmek için yazılan **117 küçük program**. Sonuçların yorumu `ai_koordinasyon/TASARIM_SORULARI_CEVAPLAR_20261015.md` belgesindedir; bu ölçümlerden açılan kayıtlar `SORUN_TAKIP.md` içinde S-544 … S-564'tür. Kitaptaki 1837 vakalık asıl külliyatı (`../vaka/`) etkilememek için bu partiler ayrı klasörde tutulur.

| Dosya | Vaka | Ne ölçer |
|---|---:|---|
| `iddia_sorular.iddia.json` | 69 | `d` DECLARE kuralı (18), `f` dosya kanalı ve tutamaç (6), `v` veri sabitleri ve DATA/READ (10), `t` tipler: ANY, VARIANT, NONE, NODE, NAN (10), `o` OOP: çoklu kalıtım, karışım, arayüz, kurucu (15), `a` ALIAS (7), `m` 6502 adresleme (3) |
| `iddia_sorular2.iddia.json` | 14 | `p` OOP ek vakaları ve WASM'da tanımsız çağrı (8), `n` iç içe `TYPE` bellek yerleşimi: `SIZEOF`, `OFFSETOF` (6) |
| `iddia_sorular3.iddia.json` | 6 | `INSTANCEOF`, kurucu aşırı yükü, `TYPENAME`, `VARPTR(kayıt dizisi)` (düzeltilmiş yazımlar) |
| `iddia_sorular4.iddia.json` | 1 | 6502 on iki adresleme kipi tablosu |
| `iddia_sorular5.iddia.json` | 9 | onaltılık, ikili ve sekizli sabitler; 6502 tablosunun son iki değeri |
| `iddia_sorular6.iddia.json` | 8 | `&H`/`&B` sabitleri tek başına ve ifade içinde, `0x` biçimi |
| `iddia_sorular7.iddia.json` | 2 | 6502 kipleri: ilk beş ve son beş |
| `iddia_sorular8.iddia.json` | 8 | `NULL`, `NOTHING`, `NIL` |

Her dosya `[{"ad": ..., "kod": ...}]` biçimindedir. İlk yazımında değişken adı ya da söz dizimi yanlış olan vakalar sonradan düzeltilerek yeniden yazılmıştır (adlarında "düzeltildi" geçer); yanlış yazımın verdiği hata derleyici kusuru sayılmadı.

## Yeniden koşturma (depo kökünden, altı yol)

```
python tools\kitap\kilavuz_v2\yoklama\vaka_kos.py kos --uxb bin\uxb_kilavuz_20261014_0253.exe --klasor tools\kitap\kilavuz_v2\yoklama\iddia_sorular_20261015 --motor AST,MIR,x64,JS,WASM,x64a --cikti sonuc.json --is 5
```

JS ve WASM yolları için `node` ve `wat2wasm` gerekir. Ham sonuçlar (her vaka ve motor için ilk sekiz çıktı satırı, ikilinin SHA-256 özeti ve zaman) `docs/kitaplar/_ortak/soru_partisi_20261015/sorular_sonuc*.json` dosyalarındadır; her sonuç dosyası aynı numaralı vaka dosyasının koşusudur. Yeni bir derlemede aynı komutla yeniden ölçülüp `vaka_kos.py fark eski.json yeni.json` ile karşılaştırılır.
