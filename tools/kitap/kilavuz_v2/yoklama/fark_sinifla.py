# -*- coding: utf-8 -*-
"""İki vaka_kos görüntüsünü karşılaştırır ve değişen hücreleri sınıflar:
  BOZULDU  : eski rc=0, yeni rc!=0 (çalışırken hata)
  DUZELDI  : eski rc!=0, yeni rc=0
  CIKTI    : ikisi de rc=0, çıktı farklı
  ILETI    : ikisi de hata, ileti/kod farklı
Kullanım: fark_sinifla.py eski.json yeni.json [sinif ...] [--motor AST]"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
E = json.load(open(args[0], encoding="utf-8"))["vakalar"]
Y = json.load(open(args[1], encoding="utf-8"))["vakalar"]
istenen = set(args[2:])
motor_suz = None
if "--motor" in sys.argv:
    motor_suz = sys.argv[sys.argv.index("--motor") + 1]


def ok(rc):
    return rc in (0, "0")


def sinif(e, y):
    if ok(e[0]) and not ok(y[0]):
        return "BOZULDU"
    if not ok(e[0]) and ok(y[0]):
        return "DUZELDI"
    if ok(e[0]) and ok(y[0]):
        return "CIKTI"
    return "ILETI"


satirlar = []
sayac = {}
for k in E:
    if k not in Y:
        continue
    for m in ("AST", "MIR", "x64", "JS"):
        if m in E[k] and m in Y[k] and E[k][m] != Y[k][m]:
            if motor_suz and m != motor_suz:
                continue
            s = sinif(E[k][m], Y[k][m])
            sayac[(m, s)] = sayac.get((m, s), 0) + 1
            if not istenen or s in istenen:
                satirlar.append((s, m, k, E[k][m], Y[k][m]))
print("özet (motor, sınıf): ", {f"{m}/{s}": n for (m, s), n in sorted(sayac.items())})
for s, m, k, e, y in sorted(satirlar, key=lambda x: (x[0], x[2], x[1])):
    kısa = lambda v: (str(v)[:150] + "…") if len(str(v)) > 150 else str(v)
    print(f"[{s}] {m:<3} {k.replace('.coklu.txt', '').replace('.satir.txt', '').replace('.iddia.json', '').replace('.pp.txt', '')}")
    print(f"      eski: {kısa(e)}\n      yeni: {kısa(y)}")
