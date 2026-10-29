# -*- coding: utf-8 -*-
"""Kılavuz örneklerini ESKİ AST-x64 yoluyla (`uxb bld --build-x64 --x64-mode AST`) derleyip çalıştırır ve sonucu
`ornek_dogrula.py`'nin kullandığı sınıflarla (GECTI / ACIK_RET / FARKLI / HATA / BEKLENTI_YOK) yazar.

Neden: 2026-10-11 kararıyla altı yol (AST, MIR, MIR-x64, AST-x64, JS, WAT/WASM) aynı dil davranışını vermelidir; ama ornek_dogrula.py'nin
"x64" sütunu yalnız MIR-x64'tür. Bu betik AST-x64 sütununu ayrıca ölçer; böylece sessiz yanlış sonuç (G-KTIP-7, G-TIP-16) gibi
yola özgü kusurlar kitapta gizli kalmaz.

Kullanım (proje kökünden):
  python tools\\kitap\\kilavuz_v2\\yoklama\\ornek_astx64.py --uxb bin\\uxb_kilavuz_20261013_1704.exe --sonuc astx64.json [--is 4] [--desen _kv_]
Çıktı: sonuç JSON'u (örnek başına durum/çıktı/rc) ve konsola durum sayıları.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(KOK, "tools", "kitap"))
import ornek_dogrula as od  # noqa: E402


def astx64(uxb, p):
    bas = od.oku(p)
    kayit = {"dosya": os.path.relpath(p, KOK).replace("\\", "/"), "motorlar": bas["motorlar"], "has_oracle": bas["has_oracle"]}
    tmp = tempfile.mkdtemp(prefix="uxb_astx64_")
    try:
        cwd = KOK if bas.get("kok_klasor") else None
        rc, c = od.calistir([uxb, "bld", p, "--build-x64", "--x64-mode", "AST", "--out-root", tmp], cwd=cwd)
        exe = None
        for dp, dn, fn in os.walk(tmp):
            if "program.exe" in fn:
                exe = os.path.join(dp, "program.exe")
        if not exe:
            s = od.temizle(c)
            ret = any(od.ACIK_RET_IZI.search(x) for x in s)
            kayit.update({"durum": "ACIK_RET" if ret else "HATA", "cikti": ["BUILDFAIL"] + s[-6:], "rc": rc})
        else:
            for d in od.DLL:
                q = os.path.join(os.path.dirname(uxb), d)
                if os.path.exists(q):
                    shutil.copy(q, os.path.dirname(exe))
            ortam = dict(os.environ)
            ortam["PATH"] = os.path.dirname(uxb) + os.pathsep + ortam.get("PATH", "")
            rc2, c2 = od.calistir([exe], cwd=(KOK if bas.get("kok_klasor") else os.path.dirname(exe)), env=ortam, sure=bas["zaman"])
            s = od.temizle(c2)
            kayit.update({"durum": od.karar(rc2, s, bas["beklenen"], bas["has_oracle"]), "cikti": od.kisalt(s), "rc": rc2})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return kayit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", required=True)
    ap.add_argument("--sonuc", required=True)
    ap.add_argument("--is", type=int, default=4, dest="isci")
    ap.add_argument("--desen", help="grup adı bu düzenli ifadeyle eşleşen klasörler (örn. _kv_)")
    ap.add_argument("--kok", default=od.ORNEK)
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    dosyalar = []
    for dp, dn, fn in os.walk(os.path.abspath(a.kok)):
        for f in sorted(fn):
            if f.endswith(".uxb"):
                if a.desen and not re.search(a.desen, os.path.basename(dp)):
                    continue
                dosyalar.append(os.path.join(dp, f))
    t0 = time.time()
    sonuc = []
    with cf.ThreadPoolExecutor(a.isci) as ex:
        for r in ex.map(lambda p: astx64(uxb, p), dosyalar):
            sonuc.append(r)
            print(f"{r['durum']:<13} {r['dosya']}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.sonuc)), exist_ok=True)
    json.dump(sonuc, open(a.sonuc, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sayac = {}
    for r in sonuc:
        sayac[r["durum"]] = sayac.get(r["durum"], 0) + 1
    print(f"{len(sonuc)} örnek AST-x64 yoluyla koşturuldu: " + ", ".join(f"{k}={v}" for k, v in sorted(sayac.items())) + f"; {time.time()-t0:.0f} sn")


if __name__ == "__main__":
    main()
