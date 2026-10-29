# -*- coding: utf-8 -*-
"""Kılavuzdaki ARAÇ örneklerini (betikler) çalıştırır ve '#=' ile yazılmış beklenen çıktıyla karşılaştırır.

Örnek dosya: tools/kitap/kilavuz_v2/arac_ornekleri/<grup>/<ad>.py (ya da .ps1, .js)
    # KONU: ...      # KOMUTLAR: ...      # ACIKLAMA: ...
    #= beklenen çıktının 1. satırı  (.py/.ps1 için '#=', .js için '//=')
Betik proje kökünden çalıştırılır; derleyici yolu UXB_EXE ortam değişkeniyle verilir.
Sonuç: docs/kitaplar/_ortak/arac_sonuclari.json
Kullanım: python tools/kitap/arac_dogrula.py [--uxb bin\\uxb_kilavuz_20261007.exe] [--grup meta] [--ad ast_api_belgesi]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARAC = os.path.join(KOK, "tools", "kitap", "kilavuz_v2", "arac_ornekleri")
SONUC = os.path.join(KOK, "docs", "kitaplar", "_ortak", "arac_sonuclari.json")
SURE = 180


def oku(yol):
    bas = {"konu": "", "komutlar": "", "aciklama": "", "beklenen": []}
    for s in open(yol, encoding="utf-8").read().splitlines():
        t = s.strip()
        m = re.match(r"^(?:#|//)=\s?(.*)$", t)
        if m:
            bas["beklenen"].append(m.group(1).rstrip())
        elif re.match(r"^(?:#|//)\s*KONU:", t):
            bas["konu"] = t.split(":", 1)[1].strip()
        elif re.match(r"^(?:#|//)\s*KOMUTLAR:", t):
            bas["komutlar"] = t.split(":", 1)[1].strip()
        elif re.match(r"^(?:#|//)\s*ACIKLAMA:", t):
            bas["aciklama"] = t.split(":", 1)[1].strip()
    return bas


def calistir(yol, uxb):
    env = dict(os.environ)
    env["UXB_EXE"] = uxb
    env["PYTHONIOENCODING"] = "utf-8"
    if yol.endswith(".py"):
        komut = [sys.executable, "-I", yol]
    elif yol.endswith(".ps1"):
        komut = ["pwsh", "-NoProfile", "-File", yol]
    elif yol.endswith(".js"):
        komut = ["node", yol]
    else:
        return -1, "bilinmeyen betik türü"
    try:
        p = subprocess.run(komut, cwd=KOK, capture_output=True, timeout=SURE, env=env)
    except subprocess.TimeoutExpired:
        return -9, "ZAMAN_ASIMI"
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", default=os.path.join(KOK, "bin", "uxb_kilavuz_20261007.exe"))
    ap.add_argument("--grup")
    ap.add_argument("--ad")
    ap.add_argument("--sonuc", default=SONUC)
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    eski = {}
    if os.path.exists(a.sonuc):
        eski = {r["dosya"]: r for r in json.load(open(a.sonuc, encoding="utf-8"))}
    t0 = time.time()
    for dp, dn, fn in os.walk(ARAC):
        for f in sorted(fn):
            if not f.endswith((".py", ".ps1", ".js")):
                continue
            g = os.path.basename(dp)
            if (a.grup and g != a.grup) or (a.ad and os.path.splitext(f)[0] != a.ad):
                continue
            yol = os.path.join(dp, f)
            rel = os.path.relpath(yol, KOK).replace("\\", "/")
            bas = oku(yol)
            rc, cikti = calistir(yol, uxb)
            satir = [s.rstrip() for s in cikti.replace("\r\n", "\n").split("\n") if s.strip()]
            durum = "GECTI" if rc == 0 and satir == bas["beklenen"] else ("FARKLI" if rc == 0 else "HATA")
            eski[rel] = {"dosya": rel, **bas, "durum": durum, "rc": rc, "cikti": satir[:30], "hepsi": durum == "GECTI"}
            print(f"{'OK ' if durum == 'GECTI' else '-- '} {rel:<70} {durum}", flush=True)
            if durum != "GECTI":
                print("     beklenen:", bas["beklenen"][:6])
                print("     gelen   :", satir[:8])
    kalan = [r for d, r in sorted(eski.items()) if os.path.exists(os.path.join(KOK, d))]
    os.makedirs(os.path.dirname(a.sonuc), exist_ok=True)
    json.dump(kalan, open(a.sonuc, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(kalan)} araç örneği, {sum(1 for r in kalan if r['hepsi'])} geçti, {time.time()-t0:.0f} sn")


if __name__ == "__main__":
    main()
