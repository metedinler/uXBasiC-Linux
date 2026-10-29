Beklenen değer klasörü.

Manifest içindeki expected_stdout_path buradaki .stdout.txt dosyalarını gösterebilir.
Her test için şu dosyalar kullanılabilir:
  t00001.stdout.txt
  t00001.stderr_contains.txt
  t00001.ast_contains.json
  t00001.mir_contains.json

UXR önce stdout eşitliğine bakar; stdout beklenmiyorsa AST/MIR eşitliği ve katman durumlarını denetler.
