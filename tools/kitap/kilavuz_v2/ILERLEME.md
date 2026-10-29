# Kılavuz V2 — yapım notları ve ilerleme

Hedef belge: `docs/tasarim/uXBasic_Hedeflenen_Sistem_ve_Kullanma_Kilavuzu_V2_TR.md`
(`python tools/kitap/kilavuz_v2/uret.py` ile `sablon/*.md` dosyalarından üretilir; elle düzenlenmez.)

## Neden böyle?
Mete'nin 2026-10-07 isteği: bundan sonraki geliştirmenin ASIL belgesi. 17-25 yaş, saf Türkçe, tablolarla gruplanmış, profesyonel
düzey. Her komut/önişlemci/meta/işlev/işleç/tip/veri yapısı/kütüphane + CLI + FreeBASIC ile derleme + programlama kararları.
İlke: SESSİZ HATA YOK, SAHTE İŞ YOK. Bu yüzden her örnek gerçek derleyicide çalıştırılır; belgede olmayan şey "çalışıyor" diye
yazılmaz; tasarlanmış ama olmayan şey [HEDEF] etiketiyle ayrıca gösterilir.

## Etiketler (her bölümde aynı)
| Etiket | Anlamı |
|---|---|
| ✔ ÇALIŞIYOR | Bu kılavuzdaki örnekle gerçek derleyicide denendi (hangi motorlarda olduğu örnek altında yazar) |
| ◐ KISMEN | Bir kısmı çalışıyor; sınırı yazılı |
| ◇ HEDEF | Tasarım kararı var, henüz derleyicide yok (derleyici açıkça reddeder ya da tanımaz) |
| ✖ SINIR | Bilinen hata ya da eksik; SORUN_TAKIP numarası verilir |
| ⌛ ESKİ | Eski uyumluluk biçimi; yeni kodda kullanma |
| ? DENENMEDİ | Kaynakta var, bu kılavuz yazılırken örnekle sınanmadı |

Motor sütunları: AST (yorumlayıcı), MIR (yorumlayıcı), x64 (yerel), JS, WASM. Eski AST-x64 ("legacy") görev/yeni özellikleri bugün açıkça
reddeder (ara durum; yol 2026-10-11 kararıyla korunur); ayrıca anılır. Örnek altındaki durum: ✔ geçti · ◌ açık ret (derleyici nedenini yazdı) · ✖ hata · ≠ farklı çıktı · — denenmedi.

## Yazım rehberi (saf Türkçe)
- Kısa cümle. Önce "ne işe yarar", sonra "nasıl yazılır", sonra örnek, sonra "dikkat / benzerinden farkı".
- Terim karşılıkları: function=işlev, SUB=yordam, statement=deyim, expression=ifade, operator=işleç, variable=değişken, constant=sabit,
  array=dizi, string=metin, integer=tamsayı, floating point=kayan noktalı (ondalıklı) sayı, loop=döngü, condition=koşul,
  parser=çözümleyici (parser), lexer=sözcük çözümleyici, semantic=anlam çözümleme, compiler=derleyici, interpreter=yorumlayıcı,
  backend/target=hedef (arka uç), runtime=çalışma zamanı, preprocessor=önişlemci, directive=yönerge, attribute=öznitelik,
  handle=tutamaç, pointer=işaretçi, memory=bellek, thread=iş parçacığı, task=görev, scheduler=zamanlayıcı, deadlock=kilitlenme,
  race=yarış durumu, diagnostic=tanı (hata/uyarı iletisi), fail-closed="kapalı başarısızlık" (emin olmadığı şeyi reddetme),
  library=kütüphane, module=modül, namespace=ad alanı, include=dahil etme, build=derleme/yapı, release=yayın, parity=eşlik (motorlar aynı sonucu verir).
- Anahtar sözcükler ve kod her zaman olduğu gibi (İngilizce) kalır. Kod içindeki yorumlar Türkçe.
- Bol tablo; her grubun sonunda "Benzerlerinden farkı" tablosu.
- Örnek seviyesi: tek satırlık basit örnekler "Hızlı bakış" tablolarında kalabilir; bölüm örnekleri orta/üst düzey (iki üç özelliği birleştiren).
- Uydurma yok: bilinmeyen = "DENENMEDİ"; tasarım = "HEDEF".

## Bölümler ve durum
(Durum sütunu `ilerleme_guncelle.py` ile kaynak şablonlardan sayılır; konu sütunu elle yazılır. Bölümün **doğruluğu** ayrıca `uret.py --sert` (örnek sonuçları, kayıt tutarlılığı) ve `tablo_denetle.py` ile denetlenir.)
| No | Dosya | Konu | Durum |
|---|---|---|---|
| 00 | 00_baslarken | nasıl okunur, etiketler, sözlük | yazıldı · 164 satır · 3 doğrulanmış örnek · 1 Ek G kaydı · 4 ◇ HEDEF |
| 01 | 01_ilkeler | amaç, ilkeler, motorlar, boru hattı | yazıldı · 258 satır · 37 Ek G kaydı · 3 ◇ HEDEF |
| 02 | 02_derleme_cli | FreeBASIC ile derleme, CLI fiilleri/seçenekleri | yazıldı · 420 satır · 21 Ek G kaydı |
| 03 | 03_program_yapisi | program, MAIN, yorumlar, ad kuralları | yazıldı · 142 satır · 10 doğrulanmış örnek · 10 Ek G kaydı · 1 ◇ HEDEF |
| 04 | 04_tipler | veri tipleri | yazıldı · 383 satır · 8 doğrulanmış örnek · 38 Ek G kaydı · 2 ◇ HEDEF |
| 05 | 05_degisken | DIM/CONST/REDIM/DEF*/kapsam/ENUM | yazıldı · 112 satır · 7 doğrulanmış örnek · 5 Ek G kaydı |
| 06 | 06_isleclar | işleçler | yazıldı · 233 satır · 10 doğrulanmış örnek · 16 Ek G kaydı |
| 07 | 07_akis | koşul/döngü/FOR EACH-DO EACH | yazıldı · 216 satır · 19 doğrulanmış örnek · 11 Ek G kaydı · 1 ◇ HEDEF |
| 08 | 08_yordamlar | SUB/FUNCTION/özyineleme | yazıldı · 200 satır · 12 doğrulanmış örnek · 20 Ek G kaydı · 2 ◇ HEDEF |
| 09 | 09_metin_sayi | metin ve sayı işlevleri | yazıldı · 160 satır · 15 doğrulanmış örnek · 12 Ek G kaydı |
| 10 | 10_veri_yapilari | dizi/TYPE/UNION/LIST/DICT/SET | yazıldı · 193 satır · 10 doğrulanmış örnek · 25 Ek G kaydı · 5 ◇ HEDEF |
| 11 | 11_nesne | CLASS/INTERFACE/MAGIC | yazıldı · 1518 satır · 13 doğrulanmış örnek · 105 Ek G kaydı · 17 ◇ HEDEF |
| 12 | 12_hata | TRY/CATCH/ASSERT/tanı | yazıldı · 206 satır · 5 doğrulanmış örnek · 35 Ek G kaydı · 2 ◇ HEDEF |
| 13 | 13_dosya_konsol | dosya/konsol/SHELL | yazıldı · 130 satır · 7 doğrulanmış örnek · 16 Ek G kaydı |
| 14 | 14_bellek | PTR/PEEK/POKE/VIRTUAL | yazıldı · 198 satır · 9 doğrulanmış örnek · 17 Ek G kaydı · 4 ◇ HEDEF |
| 15 | 15_gorevler | EVENT/PIPE/THREAD/PARALEL/SLOT/TASK | yazıldı · 483 satır · 16 doğrulanmış örnek · 21 Ek G kaydı · 16 ◇ HEDEF |
| 16 | 16_moduller_dis | INCLUDE/MODULE/CALL(DLL/API) | yazıldı · 217 satır · 4 doğrulanmış örnek · 21 Ek G kaydı |
| 17 | 17_onislemci | %% yönergeleri | yazıldı · 264 satır · 11 doğrulanmış örnek · 23 Ek G kaydı · 1 ◇ HEDEF |
| 18 | 18_meta | REM %% meta | yazıldı · 191 satır · 1 doğrulanmış örnek · 8 Ek G kaydı · 6 ◇ HEDEF |
| 19 | 19_kutuphane_tipi | RATIONAL/LIBTYPE | yazıldı · 163 satır · 2 doğrulanmış örnek · 17 Ek G kaydı · 2 ◇ HEDEF |
| 20 | 20_kutuphaneler | include/modules + libsx | yazıldı · 289 satır · 28 doğrulanmış örnek · 24 Ek G kaydı · 2 ◇ HEDEF |
| 21 | 21_hedefler | x64/JS/WAT/WASM | yazıldı · 880 satır · 54 Ek G kaydı · 3 ◇ HEDEF |
| 22 | 22_ic_ice | bileşilebilirlik | yazıldı · 187 satır · 7 doğrulanmış örnek · 40 Ek G kaydı · 2 ◇ HEDEF |
| 23 | 23_kararlar | programlama kararları | yazıldı · 106 satır · 25 Ek G kaydı · 4 ◇ HEDEF |
| 24 | 24_programlar | büyük örnek programlar | yazıldı · 78 satır · 2 doğrulanmış örnek · 10 Ek G kaydı |
| 90 | 90_ekler | dizinler, sınırlar, sözlük | yazıldı · 474 satır · 116 Ek G kaydı · 1 ◇ HEDEF |
