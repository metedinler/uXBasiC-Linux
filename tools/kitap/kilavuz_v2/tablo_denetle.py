# -*- coding: utf-8 -*-
"""Üretilen kılavuzdaki Markdown tablolarının sütun sayısı tutarlı mı? (kod blokları ve ters tırnak içindeki | sayılmaz)

Kullanım (proje kökünden): python tools/kitap/kilavuz_v2/tablo_denetle.py [kılavuz.md]
Çıkış kodu: sorunlu satır yoksa 0, varsa 1.
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VARSAYILAN = os.path.join(KOK, "docs", "tasarim", "uXBasic_Hedeflenen_Sistem_ve_Kullanma_Kilavuzu_V2_TR.md")
YOL = sys.argv[1] if len(sys.argv) > 1 else VARSAYILAN
satirlar = open(YOL, encoding="utf-8").read().split("\n")


def sutun_say(s):
    s = s.strip()
    s = re.sub(r"`[^`]*`", lambda m: m.group(0).replace("|", "§"), s)  # ters tırnak içi
    s = s.replace("\\|", "§")
    if not s.startswith("|"):
        return None
    govde = s[1:-1] if s.endswith("|") else s[1:]
    return govde.count("|") + 1


kod = False
sorun = 0
blok_bas, ref = None, None
for i, s in enumerate(satirlar, 1):
    if s.strip().startswith("```"):
        kod = not kod
        blok_bas, ref = None, None
        continue
    if kod:
        continue
    n = sutun_say(s) if s.lstrip().startswith("|") else None
    if n is None:
        blok_bas, ref = None, None
        continue
    if ref is None:
        blok_bas, ref = i, n
    elif n != ref:
        sorun += 1
        if sorun <= 25:
            print(f"satır {i}: {n} sütun (tablo {blok_bas}. satırda {ref} sütunla başladı): {s.strip()[:150]}")
print("toplam sorunlu satır:", sorun)
sys.exit(1 if sorun else 0)
