# Önceki AST davranışının karşılaştırması

Bu paket çok boyutlu REDIM desteği kanıtı değildir. Başlangıç ikilisi oop6:

* `expression_bounds_ast`: doğru çıktı 17.
* `redim_existing_ast`: `array index out of bounds` hatası; REDIM şekli açık kusur.
* `runtime_bounds_ast`: `multi-dimensional array bounds must be compile-time integer constants`
  tanısı; çalışma anı şekli açık hedef.

Son iki hatanın beklenmesi, mevcut eksikliğin değişmeden kaldığını kaydeder.
İlk pozitif beklentilerin başarısız olduğu ham koşular da raporda saklanır;
bu hatalar çözülmüş özellik diye sayılmaz. Ortak statik şekil indirgemesi,
REDIM içeren veya sınırı hesaplanamayan diziyi ilk DIM'e sabitlemez.
