# -*- coding: utf-8 -*-
"""uxb komut satırı seçeneklerini TEK TEK ölçer ve özetler (Kılavuz V2, Bölüm 2.8 / Ek G'nin ölçüm kaynağı).

Neden: yardım metni ve kayıt defteri her seçeneğin ne yaptığını söyler; bu betik gerçekten ne yaptığını ölçer. Yeni bir derleyici
ikilisi çıktığında aynı ölçüm tekrarlanır ve hangi G-CLI kayıtlarının kapandığı görülür.

  A) Dosya çıktılı seçenekler (değer alan `…-out`): her seçenek TEK BAŞINA, her fiille (lex par ast sem hir mir run runmir x64 bld jsw jswb wat wasm),
     ayrı klasörde. Ölçülen: dosya oluştu mu, boş mu, geçerli JSON mu, `schema`/`status` var mı, çıkış kodu, ilk ERROR.
  B) Bayraklar (değer almayan): altı fiilde bayraksız tabana göre çıkış kodu / stdout / üretilen dosya kümesi farkı.
  Ek: aynı içeriği yazan seçenek grupları (normalize edilmiş karma), yalnız sayaç/iskelet yazanlar.

Kullanım (proje kökünden):
  python tools\\kitap\\kilavuz_v2\\yoklama\\cli_secenek_tarama.py --uxb bin\\uxb_kilavuz_20261007.exe --cikti %TEMP%\\cli_tarama
  seçenekler: --mod AB (varsayılan), --is 4 (paralel işçi), --sinir N (yalnız ilk N seçenek; denemek için)
Çıktı: <cikti>\\cli_tarama_raporu.json ve konsola özet. Dikkat: ~1300 koşu yapar (4 işçiyle yaklaşık 4-6 dakika)."""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
YARDIM = os.path.join(os.path.dirname(__file__), "..", "veri", "cli_help.txt")
SRC_ICERIK = "DIM a AS I32\r\na = 6 * 7\r\nPRINT a\r\n"  # metin sabiti yok: WAT/WASM da derler
HARIC = {"--js-out", "--wat-out", "--wasm-out", "--html-out", "--emit-x64-nasm-out", "--build-x64-out", "--out-root", "--artifact-root",
         "--x64gen-out", "--extfp-runtime-dir", "--error-language-file", "-elf", "--source", "-s", "--run-id", "--max-steps", "--task-workers",
         "--virtual", "--target", "--stop-after", "--diag-format", "--error-limit", "--codegen-source", "--interpreter-backend", "--x64-mode",
         "--message-lang", "--language", "--console-mode", "--wat2wasm"}
SIRA = ["lex", "par", "ast", "sem", "hir", "mir", "run", "runmir", "x64", "bld", "jsw", "jswb", "wat", "wasm"]


def fiiller(wat2wasm):
    return {
        "lex": ["lex", "p.uxb"], "par": ["par", "p.uxb"], "ast": ["ast", "p.uxb"], "sem": ["sem", "p.uxb"], "hir": ["hir", "p.uxb"],
        "mir": ["mir", "p.uxb", "--semantic"], "run": ["run", "p.uxb"], "runmir": ["run", "p.uxb", "--interpreter-backend", "MIR"],
        "x64": ["x64", "p.uxb", "--emit-x64-nasm", "--emit-x64-nasm-out", "ana.asm"],
        # Dikkat G-CLI-21: klasörsüz EXE adı (ana.exe) çıkış 14 verir; klasörlü yol kullanılır.
        "bld": ["bld", "p.uxb", "--build-x64", "--build-x64-out", "cikti/ana.exe"],
        "jsw": ["jsw", "p.uxb", "--js-out", "ana.js"],
        "jswb": ["jsw", "p.uxb", "--emit-browser", "--html-out", "ana.html", "--js-out", "ana.js"],
        "wat": ["wat", "p.uxb", "--emit-wat", "--wat-out", "ana.wat"],
        "wasm": ["wat", "p.uxb", "--emit-wasm", "--wasm-out", "ana.wasm", "--wat-out", "ana.wat", "--wat2wasm=" + wat2wasm],
    }


def kayit_oku():
    kayit = {}
    for s in open(YARDIM, encoding="utf-8").read().splitlines():
        m = re.match(r"^  (-{1,2}[A-Za-z0-9][\w-]*)( <değer>)?( \[[^\]]+\])? : (.*)$", s)
        if m and "|" in m.group(4):
            kayit[m.group(1)] = dict(deger=bool(m.group(2)), kriter=m.group(4).split("|", 1)[1].strip())
    return kayit


def uzanti(ad):
    if ad.endswith("-csv-out"):
        return ".csv"
    if "json" in ad or ad.endswith("matrix-out"):
        return ".json"
    return ".txt"


def norm(s):
    s = re.sub(r"\d\d_\d\d_\d{4}_\d\d_\d\d_\d\d", "<Z>", s)
    s = re.sub(r"[A-Za-z]:[\\/][^\s\"]*", "<YOL>", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(\d+(\.\d+)?)\s*(us|ms)\b", "N", s)
    return re.sub(r'("[a-z_]*(?:time|ms|us|micro|elapsed|duration)[a-z_]*":\s*)[\d.]+', r"\1N", s, flags=re.I)


class Olcer:
    def __init__(self, uxb, cikti, wat2wasm, temizle=True):
        # temizle: her ölçümden sonra koşunun çıktı klasörü silinir (~1300 koşu ≈ 1 GB build\ ağacı bırakırdı; 2026-10-13 disk olayı)
        self.uxb, self.cikti, self.f, self.temizle = uxb, cikti, fiiller(wat2wasm), temizle

    def bitir(self, d):
        if self.temizle:
            shutil.rmtree(d, ignore_errors=True)

    def cal(self, d, args, sure=240):
        p = subprocess.run([self.uxb, *args], cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=sure)
        return p.returncode, p.stdout + p.stderr

    def hazirla(self, *parca):
        d = os.path.join(self.cikti, *parca)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "p.uxb"), "w", encoding="utf-8", newline="").write(SRC_ICERIK)
        return d

    @staticmethod
    def incele(yol):
        if not os.path.exists(yol):
            return dict(var=False)
        b = os.path.getsize(yol)
        r = dict(var=True, bayt=b)
        if b == 0:
            r["tur"] = "bos"
            return r
        ham = open(yol, "rb").read()
        metin = ham.decode("utf-8", errors="replace")
        r["karma"] = hashlib.md5(norm(metin).encode()).hexdigest()[:8]
        try:
            j = json.loads(metin)
            r["tur"] = "json"
            if isinstance(j, dict):
                r["schema"], r["status"] = "schema" in j, "status" in j
        except Exception:
            r["tur"] = "metin"
        return r

    def dosya_isi(self, g):
        fad, o, i = g
        d = self.hazirla("A", fad, str(i))
        rel = f"cikti_{i}{uzanti(o)}"
        kod, metin = self.cal(d, self.f[fad] + [o, rel, "--out-root", "kok"])
        err = next((l.strip() for l in metin.splitlines() if l.strip().startswith(("ERROR", "Aborting"))), "")
        sonuc = dict(kod=kod, err=err[:160], **self.incele(os.path.join(d, rel)))
        self.bitir(d)
        return fad, o, sonuc

    @staticmethod
    def dosya_kumesi(d):
        out = set()
        for kok, _, dosyalar in os.walk(d):
            for f in dosyalar:
                rel = re.sub(r"(^|[\\/])\d\d_\d\d_\d{4}_\d\d_\d\d_\d\d([\\/])", r"\1<ZAMAN>\2", os.path.relpath(os.path.join(kok, f), d))
                if rel != "p.uxb":
                    out.add(rel.replace("\\", "/"))
        return out

    def bayrak_isi(self, g):
        fad, o, i = g
        d = self.hazirla("B", fad, str(i) if o else "taban")
        kod, metin = self.cal(d, self.f[fad] + ([o] if o else []) + ["--out-root", "kok"])
        sonuc = dict(kod=kod, stdout=[l for l in metin.splitlines() if l.strip()], dosyalar=sorted(self.dosya_kumesi(d)))
        self.bitir(d)
        return fad, o, sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", default=os.path.join(KOK, "bin", "uxb.exe"))
    ap.add_argument("--cikti", default=os.path.join(os.environ.get("TEMP", "."), "cli_tarama"))
    ap.add_argument("--mod", default="AB")
    ap.add_argument("--is", dest="isci", type=int, default=4)
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--sakla", action="store_true", help="koşu klasörlerini silme (varsayılan: her ölçümden sonra sil; tam saklama ≈ 1 GB tutar)")
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    cikti = os.path.abspath(a.cikti)
    os.makedirs(cikti, exist_ok=True)
    wat2wasm = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")
    ol = Olcer(uxb, cikti, wat2wasm, temizle=not a.sakla)
    kayit = kayit_oku()
    dosya = [x for x, v in kayit.items() if v["deger"] and x not in HARIC]
    bayrak = [x for x, v in kayit.items() if not v["deger"] and x not in ("--help", "--version")]
    if a.sinir:
        dosya, bayrak = dosya[: a.sinir], bayrak[: a.sinir]
    print(f"ikili: {uxb}\nseçenek: {len(dosya)} dosya-çıktılı, {len(bayrak)} bayrak; kayıt defteri {len(kayit)}", flush=True)
    rapor = {"ikili": uxb, "zaman": time.strftime("%Y-%m-%d %H:%M:%S"), "A": {}, "B": {}}

    if "A" in a.mod:
        gorev = [(f, o, i) for f in SIRA for i, o in enumerate(dosya)]
        t = time.time()
        with cf.ThreadPoolExecutor(max_workers=a.isci) as ex:
            for fad, o, r in ex.map(ol.dosya_isi, gorev):
                rapor["A"].setdefault(o, {})[fad] = r
        print(f"A tamam: {len(gorev)} koşu, {time.time()-t:.0f} sn")
        A = rapor["A"]
        durum = lambda r: "YOK" if not r.get("var") else ("BOS" if r.get("tur") == "bos" else "OK")
        print("\n== hiçbir fiille dosya yazmayan seçenekler (bağlamsız):")
        for o, vr in A.items():
            if not any(durum(r) != "YOK" for r in vr.values()):
                print("  ", o, dict(Counter(r["kod"] for r in vr.values())))
        print("\n== JSON olup `schema` ve `status` alanı olmayanlar:")
        yok = [o for o, vr in A.items() for r in [next((vr[f] for f in SIRA if f in vr and durum(vr[f]) == "OK" and vr[f].get("tur") == "json" and vr[f].get("schema") is not None), None)] if r and not r["schema"] and not r["status"]]
        print("  ", len(yok), "seçenek:", ", ".join(yok))
        print("\n== aynı içeriği yazan gruplar (run, mir, sem fiillerinde):")
        for fiil in ("run", "mir", "sem"):
            gr = defaultdict(list)
            for o, vr in A.items():
                r = vr.get(fiil, {})
                if r.get("var") and r.get("bayt"):
                    gr[r["karma"]].append((o, r["bayt"]))
            for h, g in gr.items():
                if len(g) > 1:
                    print(f"  [{fiil}] ~{g[0][1]} B: " + ", ".join(x[0] for x in g))
        print("\n== fiil başına çıkış kodları:")
        for f in SIRA:
            print("  ", f, dict(Counter(vr[f]["kod"] for vr in A.values() if f in vr)))

    if "B" in a.mod:
        bf = ["run", "x64", "jsw", "wat", "mir", "bld"]
        taban = {f: ol.bayrak_isi((f, None, 0))[2] for f in bf}
        gorev = [(f, o, i) for f in bf for i, o in enumerate(bayrak)]
        t = time.time()
        B = {"taban": taban}
        with cf.ThreadPoolExecutor(max_workers=a.isci) as ex:
            for fad, o, r in ex.map(ol.bayrak_isi, gorev):
                B.setdefault(o, {})[fad] = r
        rapor["B"] = B
        print(f"\nB tamam: {len(gorev)} koşu, {time.time()-t:.0f} sn")
        etkisiz = []
        for o in bayrak:
            if all(B[o][f]["kod"] == taban[f]["kod"] and sorted(norm(" ".join(B[o][f]["stdout"]))) == sorted(norm(" ".join(taban[f]["stdout"])))
                   and set(B[o][f]["dosyalar"]) == set(taban[f]["dosyalar"]) for f in bf):
                etkisiz.append(o)
        print("== altı fiilde de tabanla AYNI görünen (etkisiz) bayraklar:", ", ".join(etkisiz))
    json.dump(rapor, open(os.path.join(cikti, "cli_tarama_raporu.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nrapor:", os.path.join(cikti, "cli_tarama_raporu.json"))


if __name__ == "__main__":
    main()
