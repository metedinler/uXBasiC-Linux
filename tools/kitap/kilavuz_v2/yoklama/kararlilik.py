# -*- coding: utf-8 -*-
"""Bir programı aynı motorda N kez koşturur ve sonuç dağılımını yazar (aralıklı takılma / yarış denetimi).

Neden: Kılavuz V2 örneklerinden `20_esz/mutex` ve `53_kv_gorev/paralel_asal_sayim` MIR yorumlayıcıda bazen doğru çıktıyı yazıp sonlanmıyor
(60 sn zaman aşımı); bu tek koşuda görünmez. Bu betik sonucu `ok` (beklenen çıktı + çıkış 0), `takildi` (zaman aşımı) ve `yanlis` diye sayar.

Kullanım (proje kökünden; makine boşken):
  python tools\\kitap\\kilavuz_v2\\yoklama\\kararlilik.py --uxb bin\\uxb_kilavuz_20261007.exe --dosya docs\\kitaplar\\_ortak\\ornekler\\20_esz\\mutex.uxb --motor MIR --kez 10 [--sure 90]
"""
import argparse
import collections
import os
import re
import subprocess
import sys
import tempfile
import time
import shutil

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def beklenen(dosya):
    return [re.sub(r"^'=\s?", "", s).rstrip() for s in open(dosya, encoding="utf-8").read().splitlines() if s.strip().startswith("'=")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", required=True)
    ap.add_argument("--dosya", required=True)
    ap.add_argument("--motor", default="MIR", choices=["AST", "MIR"])
    ap.add_argument("--kez", type=int, default=10)
    ap.add_argument("--sure", type=int, default=90)
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    dosya = os.path.abspath(a.dosya)
    bek = beklenen(dosya)
    sayac = collections.Counter()
    sureler = []
    for i in range(a.kez):
        d = tempfile.mkdtemp(prefix="krl_")
        t0 = time.time()
        try:
            try:
                r = subprocess.run([uxb, "run", dosya, "--interpreter-backend", a.motor, "--out-root", d], cwd=KOK, capture_output=True, timeout=a.sure)
                cikti = [s.rstrip() for s in (r.stdout + r.stderr).decode("utf-8", "replace").splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]
                durum = "ok" if (r.returncode == 0 and cikti == bek) else "yanlis"
                ayrinti = f"rc={r.returncode} {' | '.join(cikti[:2])[:80]}"
            except subprocess.TimeoutExpired as e:
                durum = "takildi"
                cikti = [s.rstrip() for s in (e.stdout or b"").decode("utf-8", "replace").splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]
                ayrinti = f"çıktı={' | '.join(cikti[:2])[:80]}"
        finally:
            shutil.rmtree(d, ignore_errors=True)
        sure = time.time() - t0
        sureler.append(sure)
        sayac[durum] += 1
        print(f"  koşu {i + 1:2d}: {durum:<7} {sure:6.1f} sn  {ayrinti}", flush=True)
    print(f"\n{os.path.basename(uxb)} / {os.path.basename(dosya)} / {a.motor}: {dict(sayac)}; süre en az {min(sureler):.1f} en çok {max(sureler):.1f} sn")


if __name__ == "__main__":
    main()
