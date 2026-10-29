# Gerçek WASM metin/tip ve erken S kayıtları kabulü

`run_wasm_types_tests.ps1 -Uxb .\bin\uxb.exe` ortak altı motor koşucusunu
kullanır. Her derleme ve yürütmenin gerçek çıkış kodu/çıktısı, compiler ve
kaynak kimliği, WAT/WASM/JS/native artifact hash'leri sonuç klasöründe tutulur.

S-001 parametre daraltma, tek argüman değerlendirme ve sınırlar; S-005 LONG
32 bitliği; S-006 parametre PRINT; S-007 CLNG/FIX ve çift sayıya bağlanan
.5 yuvarlaması; F32/F64 scalar/global/parametre/dönüş/aritmetik/karşılaştırma/
dizi/kurucu/sanal çağrı/STR/VAL; metin sabit/boş/concat/karşılaştırma/yordam/
dizi/UTF-8 çıktı/büyüme/alias/NUL ve S-524 unary float yolları sınanır.
`runtime_name_isolation` bir kullanıcı `UX_STR_ALLOC` yordamının iç WASM
runtime isimleriyle çakışmamasını doğrular.

- `text_trim` legacy AST-x64 motorunda mevcut bağsız TRIM nedeniyle bu motoru
  hedeflemez; kapsamı açık AST/MIR/x64/JS/WASM'dır. Diğer vakalar altı motordur.
- `text_nul` **altı motorda hedef 3 / 66** bekler. İki native yolda eski aday9
  da 2 / 66 üretir (S-630/G-METIN-7). Test beklentisi gevşetilmedi;
  yeni WASM özelliğinin native STRING ABI açığını kapattığı iddia edilmez.
- `float_class_array.uxb` dosyası ilk teşhis fixture'ı olarak korunur;
  aynı içerik `oop_multidim/float_field` paketinde tek kabul sayılır.
- Eski WASM F64 ret vektörleri `wasm_model/neg_float_refused` ve
  `oop_remaining/interface_*`, `oop_multidim/float_field` içinde artık
  gerçek pozitif çıktıyı gerektirir. Geçmiş isimler ve ham eski sonuçlar korunur.

UTF-8 code point birlikteliği, tüm metin işlevleri, native embedded-NUL,
F80/F128, tam I64/U64 ve arena reclamation ayrı açık hedeflerdir.
WASM concat/compare/LEN/LEFT/RIGHT/ASC/CHR linear memory içindedir;
Unicode case conversion/TRIM ve konsol sayfa/Node host bağları üzerinden yürür.
Özellik reddi veya WAT artifact'ının varlığı, çalışan özellik kabulü değildir.
