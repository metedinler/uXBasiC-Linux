# -*- coding: utf-8 -*-
"""Kılavuz V2 vaka külliyatını bir uxb ikilisiyle dört motorda (AST, MIR, x64, JS) koşturur ve anlık görüntü (JSON) yazar;
iki anlık görüntüyü karşılaştırarak bir derleyici sürümünden ötekine neyin değiştiğini gösterir.

Külliyat: tools/kitap/kilavuz_v2/yoklama/vaka/  (kılavuzdaki her anlatım iddiasının ve sınır kaydının küçük programları)
  *.coklu.txt   '=====' ile ayrılmış programlar; her parçanın ilk satırı başlıktır
  *.satir.txt   satır başına bir vaka:  ad | kurulum (\\n ile) | PRINT edilecek ifade(ler)
  *.pp.txt      önişlemci vakaları:  '=== ad' başlığı + kaynak satırları (ayrıca genişletilmiş kaynak da kaydedilir)
  *.iddia.json  iddia listesi: {ad, once, ifade | kod, beklenen, yoksay}  (beklenen burada yalnız bilgi; karşılaştırma görüntüler arasındadır)

Kullanım (proje kökünden):
  python tools\\kitap\\kilavuz_v2\\yoklama\\vaka_kos.py kos  --uxb bin\\uxb_kilavuz_20261013.exe --cikti %TEMP%\\vaka_yeni.json [--is 6] [--sadece desen]
  python tools\\kitap\\kilavuz_v2\\yoklama\\vaka_kos.py fark eski.json yeni.json [--tam]
Not: 1837 vaka (2026-10-13) x 4 motor; 6 işçiyle ve makine boşken ikili başına yaklaşık 100 dakika sürer (başka iş çalışırken daha uzun);
alt küme için --sadece desen (anahtar 'dosya::ad' içinde geçen metin) kullanın.
Eski AST-x64 yolu (`bld --build-x64 --x64-mode AST`) varsayılan motor listesinde yoktur; `--motor x64a` ile yalnız onu koşturabilirsiniz
(örn. iddia vakaları için: --motor x64a --sadece .iddia.json). Rakam, adres ve geçici dosya yarışı gürültüsü vardır
(x64'te çöp değer yazdıran vakalar, ZAMAN_ASIMI): fark çıktısında tek başına şaşırtıcı hücreyi yeniden koşturup doğrulayın."""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
VAKA = os.path.join(os.path.dirname(__file__), "vaka")
MOTORLAR = ["AST", "MIR", "x64", "JS"]
WAT2WASM = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")


# ---------------------------------------------------------------- külliyatı oku
def kodlari_oku(sadece=None, klasor=None):
    klasor = klasor or VAKA
    vakalar = []  # (anahtar, kod, yoksay, pp)

    def ekle(dosya, ad, kod, yoksay=(), pp=False):
        anahtar = f"{dosya}::{ad}"
        if sadece and sadece not in anahtar:
            return
        vakalar.append((anahtar, kod if kod.endswith("\n") else kod + "\n", set(yoksay), pp))

    for dosya in sorted(os.listdir(klasor)):
        yol = os.path.join(klasor, dosya)
        metin = open(yol, encoding="utf-8").read().replace("\r\n", "\n")
        if dosya.endswith(".coklu.txt"):
            for i, parca in enumerate(metin.split("=====")):
                satirlar = parca.strip("\n").split("\n")
                if not satirlar or not satirlar[0].strip():
                    continue
                ekle(dosya, f"{i + 1:02d} {satirlar[0].strip()}", "\n".join(satirlar[1:]))
        elif dosya.endswith(".satir.txt"):
            for s in metin.splitlines():
                if not s.strip() or s.startswith("#"):
                    continue
                m = re.match(r"^(\S+)\s+\|\s+(.*?)\s*\|\s+(\S.*)$", s)
                if not m:
                    continue
                kurulum, ifade = m.group(2).strip(), m.group(3).strip()
                kod = (kurulum.replace("\\n", "\n") + "\n" if kurulum else "") + ifade.replace("\\n", "\n")
                ekle(dosya, m.group(1), kod)
        elif dosya.endswith(".pp.txt"):
            ad, govde = None, []
            for s in metin.split("\n") + ["=== __son__"]:
                if s.startswith("=== "):
                    if ad is not None and ad != "__son__":
                        ekle(dosya, ad, "\n".join(govde), pp=True)
                    ad, govde = s[4:].strip(), []
                else:
                    govde.append(s)
        elif dosya.endswith(".iddia.json"):
            for i, o in enumerate(json.loads(metin)):
                kod = o.get("kod") or ((o.get("once", "") + "\n" if o.get("once") else "") + "PRINT " + o["ifade"])
                ekle(dosya, f"{i + 1:03d} {o.get('ad') or o.get('ifade') or ''}"[:80], kod, o.get("yoksay", []))
    return vakalar


# ---------------------------------------------------------------- koşturma
def norm(s):
    s = re.sub(r"\d\d_\d\d_\d{4}_\d\d_\d\d_\d\d", "<Z>", s)
    s = re.sub(r"[A-Za-z]:[\\/][^\s'\"]*", "<YOL>", s)
    s = re.sub(r"\b(cd|id|vk)_[a-z0-9_]{6,}\b", "<TMP>", s)
    return s.rstrip()


def calis(k, cwd, sure=60):
    try:
        # stdin kapalı (EOF) verilir: INPUT içeren vakalar çağıranın açık borusunda bekleyip ZAMAN_ASIMI'na düşmesin (2224 ölçümünde 7 hücre böyle düştü)
        r = subprocess.run(k, cwd=cwd, capture_output=True, timeout=sure, stdin=subprocess.DEVNULL)
        c = (r.stdout + r.stderr).decode("utf-8", "replace").splitlines()
        return r.returncode, [norm(s) for s in c if s.strip() and not s.startswith(("INFO", "WARN"))]
    except subprocess.TimeoutExpired:
        return -9, ["ZAMAN_ASIMI"]


def motor_kos(uxb, motor, yol, d):
    if motor == "AST":
        return calis([uxb, "run", yol, "--out-root", os.path.join(d, "a")], KOK)
    if motor == "MIR":
        return calis([uxb, "run", yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(d, "m")], KOK)
    if motor == "x64":
        exe = os.path.join(d, "cikti", "p.exe")
        rc, c = calis([uxb, "bld", yol, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(d, "x")], KOK, 120)
        if not os.path.exists(exe):
            return "DERLENMEDI", c[-2:]
        return calis([exe], d)
    if motor == "x64a":
        # eski AST-x64 yolu (2026-10-11 kararıyla korunur; altı yoldan biri). Varsayılan motor listesinde YOKTUR: --motor ile istenir.
        exe = os.path.join(d, "cikti", "pa.exe")
        rc, c = calis([uxb, "bld", yol, "--build-x64", "--x64-mode", "AST", "--build-x64-out", exe, "--out-root", os.path.join(d, "xa")], KOK, 120)
        if not os.path.exists(exe):
            return "DERLENMEDI", c[-2:]
        return calis([exe], d)
    if motor == "JS":
        js = os.path.join(d, "p.js")
        rc, c = calis([uxb, "jsw", yol, "--js-out", js, "--out-root", os.path.join(d, "j")], KOK)
        if not os.path.exists(js):
            return "DERLENMEDI", c[-2:]
        return calis(["node", js], d)
    if motor == "WASM":
        # WAT/WASM yolu (varsayılan motor listesinde YOKTUR: --motor WASM ile istenir). wat2wasm tools\wabt altındadır; node run_wasm.js gerçekten çalıştırır.
        wd = os.path.join(d, "w")
        os.makedirs(wd, exist_ok=True)
        rc, c = calis([uxb, "wat", yol, "--emit-wasm", "--wasm-out", os.path.join(wd, "p.wasm"), "--wat-out", os.path.join(wd, "p.wat"),
                       "--wat2wasm=" + WAT2WASM, "--out-root", os.path.join(d, "wo")], KOK, 120)
        if not (os.path.exists(os.path.join(wd, "p.wasm")) and os.path.exists(os.path.join(wd, "run_wasm.js"))):
            return "DERLENMEDI", c[-2:]
        return calis(["node", os.path.join(wd, "run_wasm.js")], wd)


def vaka_kos(uxb, motorlar, vaka):
    anahtar, kod, yoksay, pp = vaka
    d = tempfile.mkdtemp(prefix="vk_")
    yol = os.path.join(d, "p.uxb")
    open(yol, "w", encoding="utf-8", newline="\r\n").write(kod)
    sonuc = {"kod": kod}
    try:
        if pp:
            gen = os.path.join(d, "genis.uxb")
            rc, c = calis([uxb, "lex", yol, "--preprocessed-out", gen, "--out-root", os.path.join(d, "p")], KOK)
            sonuc["pp"] = [rc, open(gen, encoding="utf-8", errors="replace").read().strip().split("\n") if os.path.exists(gen) else c[-2:]]
        for m in motorlar:
            if m in yoksay:
                continue
            rc, c = motor_kos(uxb, m, yol, d)
            sonuc[m] = [rc, c[:8]]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return anahtar, sonuc


def kos(a):
    uxb = os.path.abspath(a.uxb)
    vakalar = kodlari_oku(a.sadece, a.klasor)
    motorlar = a.motor.split(",")
    print(f"ikili: {uxb}\nvaka: {len(vakalar)}; motor: {motorlar}; işçi: {a.isci}", flush=True)
    t = time.time()
    sonuclar = {}
    with cf.ThreadPoolExecutor(max_workers=a.isci) as ex:
        for n, (anahtar, s) in enumerate(ex.map(lambda v: vaka_kos(uxb, motorlar, v), vakalar), 1):
            sonuclar[anahtar] = s
            if n % 50 == 0:
                print(f"  {n}/{len(vakalar)}  {time.time() - t:.0f} sn", flush=True)
    h = hashlib.sha256(open(uxb, "rb").read()).hexdigest()
    json.dump({"ikili": uxb, "sha256": h, "zaman": time.strftime("%Y-%m-%d %H:%M:%S"), "vakalar": sonuclar},
              open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"tamam: {len(sonuclar)} vaka, {time.time() - t:.0f} sn -> {a.cikti}")


# ---------------------------------------------------------------- karşılaştırma
def fark(a):
    E = json.load(open(a.eski, encoding="utf-8"))
    Y = json.load(open(a.yeni, encoding="utf-8"))
    print(f"eski: {os.path.basename(E['ikili'])} ({E['sha256'][:12]}, {E['zaman']})\nyeni: {os.path.basename(Y['ikili'])} ({Y['sha256'][:12]}, {Y['zaman']})")
    ev, yv = E["vakalar"], Y["vakalar"]
    ortak = [k for k in ev if k in yv]
    print(f"ortak vaka: {len(ortak)}; yalnız eskide: {len(set(ev) - set(yv))}; yalnız yenide: {len(set(yv) - set(ev))}")
    degisen = {}
    for k in ortak:
        for m in MOTORLAR + ["x64a", "WASM", "pp"]:
            if m in ev[k] and m in yv[k] and ev[k][m] != yv[k][m]:
                degisen.setdefault(k, []).append(m)
    print(f"değişen vaka: {len(degisen)}")
    sayac = {}
    for k, ms in degisen.items():
        for m in ms:
            sayac[m] = sayac.get(m, 0) + 1
    print("motor başına değişen:", sayac)
    dosya = {}
    for k in degisen:
        dosya.setdefault(k.split("::")[0], []).append(k)
    for d, ks in sorted(dosya.items()):
        print(f"\n### {d}  ({len(ks)} değişen)")
        for k in ks:
            print(f"- {k.split('::', 1)[1]}   [{', '.join(degisen[k])}]")
            for m in degisen[k]:
                o, n = ev[k][m], yv[k][m]
                kisalt = (lambda x: (str(x)[:230] + "…") if len(str(x)) > 230 else str(x))
                print(f"    {m:<4} eski: {kisalt(o)}")
                print(f"    {'':<4} yeni: {kisalt(n)}")
            if a.tam:
                print("    kod:", ev[k]["kod"].replace("\n", " ⏎ ")[:300])


def main():
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    k = alt.add_parser("kos")
    k.add_argument("--uxb", required=True)
    k.add_argument("--cikti", required=True)
    k.add_argument("--is", dest="isci", type=int, default=6)
    k.add_argument("--sadece", default=None)
    k.add_argument("--klasor", default=None, help="vaka klasörü (varsayılan: bu betiğin yanındaki vaka/)")
    k.add_argument("--motor", default=",".join(MOTORLAR))
    f = alt.add_parser("fark")
    f.add_argument("eski")
    f.add_argument("yeni")
    f.add_argument("--tam", action="store_true")
    a = ap.parse_args()
    kos(a) if a.komut == "kos" else fark(a)


if __name__ == "__main__":
    main()
