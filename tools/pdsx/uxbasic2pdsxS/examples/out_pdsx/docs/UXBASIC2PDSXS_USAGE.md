# uxbasic2pdsxS çıktısı

Bu klasör, uXBasic JSON çıktılarından pdsX proje düzeni üretmek için oluşturuldu.

## Ana hedefler

1. `json/ast.json` içindeki tüm uXBasic AST node türlerini pdsX BASX karşılığına çevirmek.
2. `.hx` üretmemek; `.hx` dosyaları pdsX/HXA veya programcı tarafından hazırlanır.
3. uXBasic yorum satırlarını (`REM`, `'`, `#`) kaynakta göründüğü sırayla BASX dosyasına taşımak.
4. `CALL DLL` ve `CALL API` satırlarını aynen korumak; altına programcıya DLL/API çözüm notu eklemek.
5. uXBasic içine pdsX backend gömmemek; ayrı ara bağlayıcı olarak çalışmak.

## Üretilen ana dosyalar

- Proje: `/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/demo.prj`
- BASX: `/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/basx/main.basx`
- Rapor: `/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/reports/uxbasic2pdsxS_report.json`
- Node kapsamı: `/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/reports/node_coverage.csv`
- Kaynak haritası: `/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/reports/source_map.json`

## pdsX ile devam

```bat
python C:\pdsx_wrapper\pdsx_cli.py check "/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/demo.prj"
python C:\pdsx_wrapper\pdsx_cli.py build "/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/demo.prj" --show-python
python C:\pdsx_wrapper\pdsx_cli.py run "/mnt/data/uxbasic2pdsxS_v0_2_work/examples/out_pdsx/demo.prj"
```
