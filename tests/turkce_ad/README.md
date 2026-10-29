# Türkçe tanımlayıcı kabul paketi

`run_turkce_ad_tests.ps1 -Uxb <ayrı derleyici.exe>` veya ana model koşucusunda
`-Only turkce_ad` ile çalışır. `cases.json` beklentileri, `run_tests.py` altı
motorun derleme ve gerçek yürütmesini denetler. Çıkış kodu sıfır olmayan bir
çalıştırma olumlu kabul edilmez; olumsuz testte hem sıfır olmayan çıkış hem
beklenen tanı aranır. Her denemenin komutu, ham stdout/stderr ve çıkış kodu
ayrı `reports/turkce_ad_<tarih>/` dizininde saklanır. Dosya silinmez.

Harf kuralı: ASCII büyük/küçük harfler, ç/Ç, ğ/Ğ, ö/Ö, ş/Ş, ü/Ü eşleşir.
I/İ/i aynı, noktasız ı ayrıdır. `Artır` = `ARTıR`; `ARTIR` farklı addır.
Bu, Claude'un yarım kalan uygulamasındaki kuraldır; Türkçe yerel ayarına
göre `I` harfini `ı` yapıp mevcut ASCII adları değiştirmez.

`tr11_dizi` ve `tr13_byref` doğru yazılmış olumlu örneklerdir. Eski
`SAYILAR` yazımı `hata_tanimsiz_cagri` içinde hata vakası olarak korunur.
`hata_buyuk_noktasiz_i` da yanlış harf seçimini sınar.
`tr18_kod_cakismasi` Türkçe ad ile ASCII kod benzeri adların ayrımını,
`hata_kod_benzeri_ad` tanının ASCII adı değiştirmemesini denetler.
Tarihsel `hata_ayrilmis_yazim` dosyası silinmeden olumlu beklentiye alındı:
bu ASCII yazımlar yasak değildir, doğru kaçırılarak ayrı ad olur.

`tr12_metin` WASM'da mevcut STRING reddini; `tr13_byref` eski AST-x64 ve
WASM'da mevcut BYREF reddini bekler. Bunların geçmesi STRING/BYREF
uygulamasının tamamlandığı anlamına gelmez. Diğer motorlarda aynı programın
gerçek çıktısı karşılaştırılır. Hiçbir motor sessizce atlanmaz; iki özel
tanımsız çağrı testi yalnız ilgili WASM düzeltmesini denetler.
