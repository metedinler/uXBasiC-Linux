# -*- coding: utf-8 -*-
"""Kılavuz örneklerinin iki derleyici sürümündeki sonucunu karşılaştırır.

  eski: ornek_sonuclari_web_20261007.json + ornek_sonuclari_kv.json (uret.py'nin kullandığı birleşim; sonrakiler öncekini ezer)
  yeni: ornek_dogrula.py --web --sonuc <json> ile yeni ikiliyle alınmış tam sonuç dosyası

Kullanım: python tools/kitap/kilavuz_v2/yoklama/ornek_fark.py <yeni.json> [--sadece-kitap] [--ayrinti]
  --sadece-kitap : yalnız şablonlarda {{ORNEK:...}} ile anılan örnekler
Çıktı: motor ve durum başına değişim sayısı, ardından değişen örnekler (örnek, motor, eski durum -> yeni durum, yeni çıktı)."""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ORTAK = os.path.join(KOK, "docs", "kitaplar", "_ortak")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import uret  # noqa: E402  (kitabın kullandığı sınıflama: açık ret / yürütme hatası / zaman aşımı; iki taraf da aynı kuralla okunur)


def yukle(yol):
    return json.load(open(yol, encoding="utf-8"))


def birlestir(*dosyalar):
    s = {}
    for d in dosyalar:
        for k in yukle(d):
            s[k["dosya"]] = k
    return s


def kitaptaki_ornekler():
    kume = set()
    for yol in glob.glob(os.path.join(KOK, "tools", "kitap", "kilavuz_v2", "sablon", "*.md")):
        for m in re.finditer(r"\{\{ORNEK:([^|}]+)", open(yol, encoding="utf-8").read()):
            kume.add("docs/kitaplar/_ortak/ornekler/" + m.group(1).strip() + ".uxb")
    return kume


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    eski = birlestir(os.path.join(ORTAK, "ornek_sonuclari_web_20261007.json"), os.path.join(ORTAK, "ornek_sonuclari_kv.json"))
    yeni = birlestir(args[0])
    kume = kitaptaki_ornekler() if "--sadece-kitap" in sys.argv else None
    sayac = {}
    satirlar = []
    ortak = [d for d in eski if d in yeni and (kume is None or d in kume)]
    for d in ortak:
        for m in ("AST", "MIR", "x64", "JS", "WASM"):
            e = eski[d].get("motor", {}).get(m)
            y = yeni[d].get("motor", {}).get(m)
            if not e or not y:
                continue
            ed, yd = uret.sinif(e), uret.sinif(y)
            if ed != yd or (e.get("durum") == "GECTI" and e.get("cikti") != y.get("cikti")):
                anahtar = (m, ed, yd)
                sayac[anahtar] = sayac.get(anahtar, 0) + 1
                satirlar.append((d, m, ed, yd, y.get("cikti")))
    print(f"karşılaştırılan örnek: {len(ortak)}" + (" (yalnız kitapta anılanlar)" if kume is not None else ""))
    for (m, e, y), n in sorted(sayac.items()):
        print(f"  {m:<5} {e} -> {y}: {n}")
    if "--ayrinti" in sys.argv:
        for d, m, e, y, c in sorted(satirlar):
            print(f"- {d.replace('docs/kitaplar/_ortak/ornekler/', '')}  [{m}] {e} -> {y}   {str(c)[:140]}")


if __name__ == "__main__":
    main()
