# S-629: sabit şekilli çok boyutlu CLASS dizileri

`run_oop_multidim_tests.ps1` ana model koşucusunda `oop_multidim` paketidir.
13 kaynak, altı motorda 78 kontrol: 53 gerçek pozitif çıktı, 24 sözleşme hata
denetimi ve WASM F64 için 1 mevcut destek kapısı denetimi.
Beklentiler `cases.json` içindedir; hata kontrolü sıfır olmayan çıkış ve tanı
gerektirir. Bir özellik reddedilerek çalışıyor sayılmaz.

Kapsam: 2D/3D, negatif ve sıfır olmayan alt sınırlar, yerel/global gölgeleme ve özyinelemede ayrı yerel depo,
derleme zamanında hesaplanabilen sınır ifadeleri, I32/F64 alanı, statik/sanal
yöntem, alias, NULL, DELETE, bileşik atamada tek ve sıralı indeks değerlendirme,
LBOUND/UBOUND/SIZEOF ve eksen/rank denetimleri. I32 ortak pozitif kapsam altı
motordadır. F64 alan okuma/yazma/bileşik atama beş motorda pozitif sınanır;
WASM F64 yürütmesi S-150 kapsamında açıktır.

REDIM, çalışma anında belirlenen çok boyutlu sınırlar ve çok boyutlu dizi
parametreleri bu paketin destek iddiası değildir. Kalan imalat
`ai_koordinasyon/OOP_COK_BOYUTLU_IMALAT_20261018.md` içinde izlenir.

İlk F64 WASM denemesi pozitif beklentiyle başarısız oldu (aday6); mevcut
genel F64 geçidi gerçek tanı verdi. Bu nedenle manifest bu motorda kapının
korunduğunu denetler. Hedeflenen F64 desteği tamamlandı sayılmaz; ilk hata
kaydı korunur. Gölgeleme hatalarının pozitif beklentileri değiştirilmedi.

Ham sonuçlar kaynak/derleyici SHA256, komut, gerçek çıktı ve çıkış kodu içerir.
Büyük yerel derleme eserleri yalnız bu koşunun sistem Temp dizisinde üretilir;
çalıştırıldıktan ve hash kaydı alındıktan sonra kaldırılır. Çalışma alanındaki
kaynaklar ve başarısız koşular korunur.
