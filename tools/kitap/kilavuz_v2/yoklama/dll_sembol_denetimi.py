# -*- coding: utf-8 -*-
"""libsx sarmalayıcılarındaki CALL(DLL, "x.dll", "sembol", ...) çağrılarının, bin klasöründeki DLL'lerde gerçekten
dışa aktarıldığını denetler ve sonucu veri/dll_denetim.json dosyasına yazar (kılavuz üreticisi bu dosyayı okur).

Kullanım (proje kökünden):  python tools\\kitap\\kilavuz_v2\\yoklama\\dll_sembol_denetimi.py
Not: DLL'ler bu süreçte yüklenir; yüklenemeyen DLL ("yuklenemedi") ayrıca raporlanır."""
import ctypes
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BIN = os.path.join(KOK, "bin")
CIKTI = os.path.join(os.path.dirname(__file__), "..", "veri", "dll_denetim.json")

os.add_dll_directory(BIN)
os.environ["PATH"] = BIN + os.pathsep + os.environ["PATH"]
sonuc = {}
for dp, dn, fn in os.walk(os.path.join(KOK, "libsx")):
    for f in sorted(fn):
        if not f.lower().endswith(".bas"):
            continue
        yol = os.path.join(dp, f)
        for satir in open(yol, encoding="utf-8", errors="replace"):
            for dll, sembol in re.findall(r'CALL\(DLL,\s*"([^"]+)"\s*,\s*"([^"]+)"', satir):
                sonuc.setdefault(dll.lower(), {}).setdefault(sembol, set()).add(os.path.relpath(yol, KOK).replace("\\", "/"))

rapor = {}
for dll, semboller in sorted(sonuc.items()):
    dosya = os.path.join(BIN, dll)
    if not os.path.exists(dosya):
        rapor[dll] = {"yuklenemedi": "DLL bin klasöründe yok", "sembol_sayisi": len(semboller), "eksik": []}
        continue
    try:
        h = ctypes.WinDLL(dosya)
    except OSError as e:
        rapor[dll] = {"yuklenemedi": str(e)[:120], "sembol_sayisi": len(semboller), "eksik": []}
        continue
    eksik = sorted(s for s in semboller if not hasattr(h, s))
    rapor[dll] = {"sembol_sayisi": len(semboller), "eksik": eksik}

os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
json.dump(rapor, open(CIKTI, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
for dll, r in rapor.items():
    if "yuklenemedi" in r:
        print(f"{dll:<24} YÜKLENEMEDİ ({r['yuklenemedi']}) · sembol {r['sembol_sayisi']}")
    else:
        print(f"{dll:<24} sembol {r['sembol_sayisi']:<4} eksik {len(r['eksik'])}" + (f"  → {r['eksik'][:6]}" if r["eksik"] else ""))
print(f"{len(rapor)} DLL denetlendi -> {os.path.relpath(CIKTI, KOK)}")
