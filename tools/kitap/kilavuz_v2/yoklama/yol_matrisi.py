# -*- coding: utf-8 -*-
"""Küçük programları ALTI yolda (AST, MIR, MIR-x64, AST-x64, JS, WASM) koşturur ve yan yana yazar.

Neden: 2026-10-11 kararıyla altı yol aynı dil davranışını vermelidir; ornek_dogrula.py ve vaka_kos.py varsayılan olarak AST-x64'ü ve WASM'ı
vaka düzeyinde ölçmez. Bu betik bir vaka dosyasındaki (.coklu.txt biçimi: ilk satır ad, sonra kod, `=====` ayırıcı) ya da tek bir .uxb dosyasındaki
programlar için altı yolun çıktısını tek tabloda verir; WASM yolu yalnız tamsayı yazdıran programlarda anlamlıdır (G-WASM-7, G-WASM-8).

Kullanım (proje kökünden):
  python tools\\kitap\\kilavuz_v2\\yoklama\\yol_matrisi.py --uxb bin\\uxb_kilavuz_20261013_1704.exe --vaka tools\\kitap\\kilavuz_v2\\yoklama\\vaka\\ktip_dene2.coklu.txt [--is 3] [--json cikti.json]
  python tools\\kitap\\kilavuz_v2\\yoklama\\yol_matrisi.py --uxb bin\\<x>.exe --dosya program.uxb
Tabloda her yol icin ilk 3 cikti satiri gorunur; daha uzun ciktilar icin `--satir 12 --genislik 300`.
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
WAT2WASM = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")
YOLLAR = ["AST", "MIR", "MIR-x64", "AST-x64", "JS", "WASM"]


def calis(k, cwd=None, sure=90):
    try:
        r = subprocess.run(k, cwd=cwd, capture_output=True, timeout=sure)
        c = (r.stdout + r.stderr).decode("utf-8", "replace").splitlines()
        return r.returncode, [s.rstrip() for s in c if s.strip() and not s.startswith(("INFO", "WARN"))]
    except subprocess.TimeoutExpired:
        return -9, ["ZAMAN_ASIMI"]


def exe_calistir(exe, uxb, d):
    ortam = dict(os.environ)
    ortam["PATH"] = os.path.dirname(uxb) + os.pathsep + ortam.get("PATH", "")
    try:
        r = subprocess.run([exe], cwd=d, capture_output=True, timeout=60, env=ortam)
        c = (r.stdout + r.stderr).decode("utf-8", "replace").splitlines()
        return r.returncode, [s.rstrip() for s in c if s.strip()]
    except subprocess.TimeoutExpired:
        return -9, ["ZAMAN_ASIMI"]


def kos(uxb, kod):
    d = tempfile.mkdtemp(prefix="ym_")
    yol = os.path.join(d, "p.uxb")
    open(yol, "w", encoding="utf-8", newline="\r\n").write(kod if kod.endswith("\n") else kod + "\n")
    s = {}
    try:
        s["AST"] = calis([uxb, "run", yol, "--interpreter-backend", "AST", "--out-root", os.path.join(d, "a")], KOK)
        s["MIR"] = calis([uxb, "run", yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(d, "m")], KOK)
        for ad, mod in (("MIR-x64", "MIR"), ("AST-x64", "AST")):
            exe = os.path.join(d, ad, "p.exe")
            os.makedirs(os.path.dirname(exe), exist_ok=True)
            rc, c = calis([uxb, "bld", yol, "--build-x64", "--x64-mode", mod, "--build-x64-out", exe, "--out-root", os.path.join(d, "x" + mod)], KOK, 150)
            s[ad] = exe_calistir(exe, uxb, d) if os.path.exists(exe) else ("DERLENMEDI", c[-2:])
        js = os.path.join(d, "p.js")
        rc, c = calis([uxb, "jsw", yol, "--js-out", js, "--out-root", os.path.join(d, "j")], KOK)
        s["JS"] = calis(["node", js], d) if os.path.exists(js) else ("DERLENMEDI", c[-2:])
        wd = os.path.join(d, "w")
        os.makedirs(wd, exist_ok=True)
        rc, c = calis([uxb, "wat", yol, "--emit-wasm", "--wasm-out", os.path.join(wd, "p.wasm"), "--wat-out", os.path.join(wd, "p.wat"),
                       "--wat2wasm=" + WAT2WASM, "--out-root", os.path.join(d, "wo")], KOK)
        if os.path.exists(os.path.join(wd, "p.wasm")) and os.path.exists(os.path.join(wd, "run_wasm.js")):
            s["WASM"] = calis(["node", os.path.join(wd, "run_wasm.js")], wd)
        else:
            s["WASM"] = ("DERLENMEDI", c[-2:])
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return s


def vakalari_oku(yol):
    metin = open(yol, encoding="utf-8").read().replace("\r\n", "\n")
    vakalar = []
    for parca in metin.split("====="):
        satirlar = parca.strip("\n").split("\n")
        if satirlar and satirlar[0].strip():
            vakalar.append((satirlar[0].strip(), "\n".join(satirlar[1:])))
    return vakalar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", required=True)
    ap.add_argument("--vaka")
    ap.add_argument("--dosya")
    ap.add_argument("--is", type=int, default=3, dest="isci")
    ap.add_argument("--json")
    ap.add_argument("--satir", type=int, default=3, help="her yol icin tabloda gosterilecek cikti satiri (varsayilan 3; JSON en az 6 tutar)")
    ap.add_argument("--genislik", type=int, default=150, help="tablodaki ozet satirinin en fazla karakteri")
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    if a.vaka:
        vakalar = vakalari_oku(a.vaka)
    else:
        vakalar = [(os.path.basename(a.dosya), open(a.dosya, encoding="utf-8").read())]
    with cf.ThreadPoolExecutor(a.isci) as ex:
        sonuc = list(ex.map(lambda v: kos(uxb, v[1]), vakalar))
    print(os.path.basename(uxb))
    kayit = []
    for (ad, kod), s in zip(vakalar, sonuc):
        print(f"\n## {ad}")
        satir = {}
        for y in YOLLAR:
            rc, c = s[y]
            ozet = " | ".join(c[:a.satir])[:a.genislik]
            print(f"  {y:<8} rc={rc!s:<10} {ozet}")
            satir[y] = [rc, c[:max(6, a.satir)]]
        kayit.append({"ad": ad, "kod": kod, "yollar": satir})
    if a.json:
        json.dump({"ikili": uxb, "vakalar": kayit}, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
