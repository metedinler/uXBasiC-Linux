# -*- coding: utf-8 -*-
"""vaka_kos anlık görüntüsündeki iddia vakalarını, iddia.json dosyalarındaki 'beklenen' değerlerle karşılaştırır.
Kullanım: iddia_beklenen.py goruntu.json [--ayrinti]"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
VAKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vaka")
G = json.load(open(sys.argv[1], encoding="utf-8"))
ayrinti = "--ayrinti" in sys.argv
V = G["vakalar"]
print(os.path.basename(G["ikili"]), G["sha256"][:12], G["zaman"])
toplam = gecen = 0
sorunlu = []
motorsay = {}
for dosya in sorted(os.listdir(VAKA)):
    if not dosya.endswith(".iddia.json"):
        continue
    liste = json.load(open(os.path.join(VAKA, dosya), encoding="utf-8"))
    for i, o in enumerate(liste):
        ad = f"{i + 1:03d} {o.get('ad') or o.get('ifade') or ''}"[:80]
        anahtar = f"{dosya}::{ad}"
        if anahtar not in V or "beklenen" not in o:
            continue
        bek = o["beklenen"]
        bek = [str(x) for x in (bek if isinstance(bek, list) else [bek])]
        for m in ("AST", "MIR", "x64", "x64a", "JS", "WASM"):
            if m in o.get("yoksay", []) or m not in V[anahtar]:
                continue
            rc, c = V[anahtar][m]
            if all(x == "?" for x in bek):
                continue  # beklenen bilinmiyor: ölçüm amaçlı vaka
            toplam += 1
            if bek == ["HATA"]:
                ok = rc not in (0, "0")  # hata (derleme/çalışma) beklenir
            else:
                ok = rc in (0, "0") and [x.strip() for x in c] == [x.strip() for x in bek]
            if ok:
                gecen += 1
            else:
                sorunlu.append((dosya.replace(".iddia.json", ""), ad, m, bek, rc, c))
                motorsay[m] = motorsay.get(m, 0) + 1
print(f"beklenen karşılaştırması: {gecen}/{toplam} geçti; sapma: {len(sorunlu)}  motor başına: {motorsay}")
if ayrinti:
    for d, ad, m, bek, rc, c in sorunlu:
        print(f"- [{d}] {ad}  ({m})\n    beklenen: {bek}\n    gelen   : rc={rc} {c[:4]}")
