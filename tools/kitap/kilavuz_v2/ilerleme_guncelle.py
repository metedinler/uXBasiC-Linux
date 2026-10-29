# -*- coding: utf-8 -*-
"""ILERLEME.md'deki "Bölümler ve durum" tablosunun Durum sütununu kaynak şablonlardan sayarak yazar.

Sayılan her değer şablondan gelir, elle girilmez:
  satır   = şablon dosyasının satır sayısı
  örnek   = {{ORNEK:...}} yer tutucusu (aynı örnek iki bölümde geçerse ikisinde de sayılır)
  kayıt   = şablonda geçen benzersiz Ek G kaydı (G-ALAN-n)
  hedef   = "◇ HEDEF" işaretli yer
Kullanım (proje kökünden): python tools\\kitap\\kilavuz_v2\\ilerleme_guncelle.py"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KLASOR = os.path.dirname(os.path.abspath(__file__))
SABLON = os.path.join(KLASOR, "sablon")
ILERLEME = os.path.join(KLASOR, "ILERLEME.md")


def sayimlar(dosya):
    t = open(os.path.join(SABLON, dosya + ".md"), encoding="utf-8").read()
    return {
        "satir": t.count("\n"),
        "ornek": len(re.findall(r"\{\{ORNEK:", t)),
        "kayit": len(set(re.findall(r"G-[A-ZÇĞİÖŞÜ]+-\d+", t))),
        "hedef": t.count("◇ HEDEF"),
    }


def durum(dosya):
    s = sayimlar(dosya)
    parca = [f"yazıldı · {s['satir']} satır"]
    if s["ornek"]:
        parca.append(f"{s['ornek']} doğrulanmış örnek")
    if s["kayit"]:
        parca.append(f"{s['kayit']} Ek G kaydı")
    if s["hedef"]:
        parca.append(f"{s['hedef']} ◇ HEDEF")
    return " · ".join(parca)


def main():
    satirlar = open(ILERLEME, encoding="utf-8").read().split("\n")
    degisen = 0
    for i, s in enumerate(satirlar):
        m = re.match(r"^\|\s*(\d\d)\s*\|\s*([a-z0-9_]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", s)
        if not m or not os.path.exists(os.path.join(SABLON, m.group(2) + ".md")):
            continue
        satirlar[i] = f"| {m.group(1)} | {m.group(2)} | {m.group(3)} | {durum(m.group(2))} |"
        degisen += 1
    metin = "\n".join(satirlar)
    metin = metin.replace("(bu liste uret.py tarafından değil elle güncellenir)",
                          "(Durum sütunu `ilerleme_guncelle.py` ile kaynak şablonlardan sayılır; konu sütunu elle yazılır. "
                          "Bölümün **doğruluğu** ayrıca `uret.py --sert` (örnek sonuçları, kayıt tutarlılığı) ve `tablo_denetle.py` ile denetlenir.)")
    open(ILERLEME, "w", encoding="utf-8", newline="\n").write(metin)
    print("güncellenen bölüm satırı:", degisen)


if __name__ == "__main__":
    main()
