# S-097 minimal testler (çalıştırılmadı)

`bounded_ok.uxb` → exit 0 ve çıktı `7`. Diğer beş dosya → exit != 0; tanıda `array index out of bounds`. Ek kriter: segfault ve sessiz veri bozulması FAIL. Bunlar amaçlanan sonuçlardır, ölçülmüş değildir. Legacy ile diğer motorların tümünde aynı beklenti kullanılmalıdır. `oob_nonzero_lower` ve namespace çakışması, çözümün sınır aritmetiğini doğrular.
