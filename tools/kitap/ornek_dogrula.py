# -*- coding: utf-8 -*-
"""Kitap örneklerini AST, MIR ve native x64 motorlarında çalıştırıp beklenen çıktıyla karşılaştırır.

Örnek dosya biçimi (docs/kitaplar/_ortak/ornekler/<grup>/<ad>.uxb):
    ' KONU: IF / ELSEIF / ELSE
    ' KOMUTLAR: IF THEN ELSEIF ELSE END
    ' ACIKLAMA: tek satırlık açıklama (isteğe bağlı)
    '= beklenen çıktının 1. satırı
    '= beklenen çıktının 2. satırı
    ...program...
Beklenen satırlar birebir karşılaştırılır (sağdaki boşluklar ve INFO/WARN satırları yok sayılır).

Sonuç: docs/kitaplar/_ortak/ornek_sonuclari.json  (her örnek için motor -> GECTI/FARKLI/HATA + çıktı)
Kullanım: python tools/kitap/ornek_dogrula.py [--uxb bin\\uxb_openclaw_S087.exe] [--grup akis] [--ad if_elseif] [--is 3]
          [--kok <örnek klasörü>] [--sonuc <sonuç.json>]   (paralel işlerde her iş kendi --kok/--sonuc'unu verir)
Yorumlayıcılar ve native derleme geçici bir klasörde çalışır; proje köküne build\\<tarih> klasörü açılmaz.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import tempfile
import time

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORNEK = os.path.join(KOK, "docs", "kitaplar", "_ortak", "ornekler")
SONUC = os.path.join(KOK, "docs", "kitaplar", "_ortak", "ornek_sonuclari.json")
DLL = ("uxb_runtime.dll",)
SURE = 60


def oku(p):
    bas = {"konu": "", "komutlar": [], "aciklama": "", "beklenen": [], "has_oracle": False, "motorlar": ["AST", "MIR", "x64"], "kok_klasor": False, "zaman": None}
    for s in open(p, encoding="utf-8").read().splitlines():
        t = s.strip()
        m = re.match(r"(?i)^'\s*ZAMAN:\s*(\d+)", t)
        if m:
            # çok sayıda DLL çağrısı yapan örnekler AST'de dakikalar sürer (G-HIZ-2): bu örnek için süre sınırı (saniye)
            bas["zaman"] = int(m.group(1))
            continue
        if re.match(r"(?i)^'\s*CALISMA:\s*kok", t):
            # örnek, derleyicinin PROJE KÖKÜNDEN çalıştırılmasını ister (örn. %%CONFIG_FILE yolu çalışma klasörüne göredir)
            bas["kok_klasor"] = True
            continue
        if re.match(r"(?i)^'\s*MOTORLAR:", t):
            # bu örneğin GEÇMESİ BEKLENEN motorlar (örn. ' MOTORLAR: AST JS); ötekiler yalnız bilgi için çalıştırılır
            bas["motorlar"] = t.split(":", 1)[1].split()
            continue
        if t.startswith("'="):
            bas["has_oracle"] = True
            bas["beklenen"].append((t[2:][1:] if t[2:3] == " " else t[2:]).rstrip())
        elif re.match(r"(?i)^'\s*KONU:", t):
            bas["konu"] = t.split(":", 1)[1].strip()
        elif re.match(r"(?i)^'\s*KOMUTLAR:", t):
            bas["komutlar"] = t.split(":", 1)[1].split()
        elif re.match(r"(?i)^'\s*ACIKLAMA:", t):
            bas["aciklama"] = t.split(":", 1)[1].strip()
    return bas


def temizle(cikti):
    satir = [s.rstrip() for s in cikti.replace("\r\n", "\n").split("\n")]
    satir = [s for s in satir if not re.match(r"^(INFO|WARN)\b", s)]
    while satir and not satir[-1]:
        satir.pop()
    return satir


CIKTI_SINIRI = 2 * 1024 * 1024   # kaçak PRINT döngüsü RAM'i/diski doldurmasın (S-109 disk olayı)


def calistir(komut, cwd=None, env=None, sure=None):
    """Komutu çalıştırır; sure (varsayılan SURE) saniyeyi ya da CIKTI_SINIRI baytı aşarsa süreci öldürür."""
    p = subprocess.Popen(komut, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    parcalar, toplam, durum = [], 0, {"asim": False}

    def oku():
        nonlocal toplam
        for parca in iter(lambda: p.stdout.read(65536), b""):
            if toplam < CIKTI_SINIRI:
                parcalar.append(parca[:CIKTI_SINIRI - toplam])
            toplam += len(parca)
            if toplam >= CIKTI_SINIRI and not durum["asim"]:
                durum["asim"] = True
                p.kill()

    import threading
    t = threading.Thread(target=oku, daemon=True)
    t.start()
    try:
        rc = p.wait(timeout=sure or SURE)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        t.join(5)
        return -9, b"".join(parcalar).decode("utf-8", "replace") + "\nZAMAN_ASIMI"
    t.join(5)
    metin = b"".join(parcalar).decode("utf-8", "replace")
    if durum["asim"]:
        return -8, metin + "\nCIKTI_SINIRI_ASILDI"
    return rc, metin


def kisalt(s):
    # ilk 40 satır + (uzunsa) son 2 satır: ZAMAN_ASIMI / CIKTI_SINIRI_ASILDI işareti kayıtta görünsün
    return s[:40] + (['...'] + s[-2:] if len(s) > 42 else s[40:])


# Derleyicinin "bunu yapamıyorum" diye AÇIKÇA söylediği iletiler (fail-closed). Bunlar sessiz hata ya da çökme değildir.
ACIK_RET_IZI = re.compile(r"(?i)refus|not implemented|is not supported|does not support|unsupported|desteklenm|henuz uygulanmad|henüz uygulanmad|"
                          r"NATIVE_ONLY|fail-closed|not available|lowering unavailable|kapisi|kapısı|reddedil|requires native|cannot be emitted|must be compile-time|in current backend|build_all.bat failed|"
                          r"UXB_LIBTYPE_PROVIDER_UNAVAILABLE|provider unavailable")


def karar(rc, satir, beklenen, has_oracle=True):
    if rc in (-8, -9):
        # zaman aşımı / çıktı sınırı aşıldı: derleyicinin "yapamıyorum" demesi değil, gerçek hata (çıktıdaki sözcükler yanıltmasın)
        return "HATA"
    if rc == 0 and not has_oracle:
        return "BEKLENTI_YOK"
    if rc == 0 and satir == beklenen:
        return "GECTI"
    if rc != 0 or any(re.search(r"(?i)\berror\b|hata|exception|BUILDFAIL", s) for s in satir):
        # çıkış kodu sıfır değil: derleyici nedenini açıkça yazdıysa "ACIK_RET", yoksa gerçek "HATA"
        if any(ACIK_RET_IZI.search(s) for s in satir):
            return "ACIK_RET"
        return "HATA"
    return "FARKLI"


NODE = shutil.which("node")
WAT2WASM = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")


def web_dogrula(uxb, p, bas, tmp, sonuc):
    """JS (uxb jsw -> node) ve WASM (uxb wat --emit-wasm -> wat2wasm -> node run_wasm.js) hedeflerini gerçekten çalıştırır."""
    if not NODE:
        for ad in ("JS", "WASM"):
            sonuc["motor"][ad] = {"durum": "HATA", "cikti": ["node bulunamadi"], "rc": -1}
        return
    cw = KOK if bas.get("kok_klasor") else tmp
    oo = ["--out-root", tmp] if cw != tmp else []
    jd = os.path.join(tmp, "js")
    os.makedirs(jd, exist_ok=True)
    rc, c = calistir([uxb, "jsw", p, "--js-out", os.path.join(jd, "p.js")] + oo, cwd=cw)
    if os.path.exists(os.path.join(jd, "p.js")):
        rc, c = calistir([NODE, os.path.join(jd, "p.js")], cwd=jd)
        s = temizle(c)
        sonuc["motor"]["JS"] = {"durum": karar(rc, s, bas["beklenen"], bas["has_oracle"]), "cikti": kisalt(s), "rc": rc}
    else:
        s = temizle(c)
        d = "ACIK_RET" if any(ACIK_RET_IZI.search(x) for x in s) else "HATA"
        sonuc["motor"]["JS"] = {"durum": d, "cikti": ["BUILDFAIL"] + s[-6:], "rc": rc}
    wd = os.path.join(tmp, "wasm")
    os.makedirs(wd, exist_ok=True)
    rc, c = calistir([uxb, "wat", p, "--emit-wasm", "--wasm-out", os.path.join(wd, "p.wasm"),
                      "--wat-out", os.path.join(wd, "p.wat"), "--wat2wasm=" + WAT2WASM] + oo, cwd=cw)
    if os.path.exists(os.path.join(wd, "p.wasm")) and os.path.exists(os.path.join(wd, "run_wasm.js")):
        rc, c = calistir([NODE, os.path.join(wd, "run_wasm.js")], cwd=wd)
        s = temizle(c)
        sonuc["motor"]["WASM"] = {"durum": karar(rc, s, bas["beklenen"], bas["has_oracle"]), "cikti": kisalt(s), "rc": rc}
    else:
        s = temizle(c)
        d = "ACIK_RET" if any(ACIK_RET_IZI.search(x) for x in s) else "HATA"
        sonuc["motor"]["WASM"] = {"durum": d, "cikti": ["BUILDFAIL"] + s[-6:], "rc": rc}


def dogrula(uxb, p, web=False):
    bas = oku(p)
    sonuc = {"dosya": os.path.relpath(p, KOK).replace("\\", "/"), **bas, "motor": {}}
    tmp = tempfile.mkdtemp(prefix="uxb_kitap_")
    try:
        # yorumlayıcılar çalışma klasöründe build\<tarih> açar: proje köküne değil geçici klasöre düşsün
        cw = KOK if bas.get("kok_klasor") else tmp
        for ad, ek in (("AST", []), ("MIR", ["--interpreter-backend", "MIR"])):
            rc, c = calistir([uxb, "run", p] + ek + (["--out-root", tmp] if cw != tmp else []), cwd=cw, sure=bas["zaman"])
            s = temizle(c)
            sonuc["motor"][ad] = {"durum": karar(rc, s, bas["beklenen"], bas["has_oracle"]), "cikti": kisalt(s), "rc": rc}
        rc, c = calistir([uxb, "bld", p, "--out-root", tmp], cwd=(KOK if bas.get("kok_klasor") else None))
        exe = None
        for dp, dn, fn in os.walk(tmp):
            if "program.exe" in fn:
                exe = os.path.join(dp, "program.exe")
        if not exe:
            s = temizle(c)
            sonuc["motor"]["x64"] = {"durum": "HATA", "cikti": ["BUILDFAIL"] + s[-8:], "rc": rc}
        else:
            for d in DLL:
                q = os.path.join(os.path.dirname(uxb), d)
                if os.path.exists(q):
                    shutil.copy(q, os.path.dirname(exe))
            # üçüncü taraf DLL'lere bağımlı kütüphaneler (DuckDB, SDL3 ...) için derleyicinin bin klasörü PATH'e eklenir
            # (gerçek dağıtımda .exe, DLL'lerle aynı klasörde olurdu)
            ortam = dict(os.environ)
            ortam["PATH"] = os.path.dirname(uxb) + os.pathsep + ortam.get("PATH", "")
            # "CALISMA: kok" başlıklı örnekler (göreli yol kullananlar) x64'te de proje kökünden çalışır
            rc, c = calistir([exe], cwd=(KOK if bas.get("kok_klasor") else os.path.dirname(exe)), env=ortam, sure=bas["zaman"])
            s = temizle(c)
            sonuc["motor"]["x64"] = {"durum": karar(rc, s, bas["beklenen"], bas["has_oracle"]), "cikti": kisalt(s), "rc": rc}
        # "hepsi" yalnız AST/MIR/x64 için (eski anlam korunur); JS/WASM ayrıca "web_hepsi" ile raporlanır
        if web:
            web_dogrula(uxb, p, bas, tmp, sonuc)
            sonuc["web_hepsi"] = all(sonuc["motor"][k]["durum"] == "GECTI" for k in ("JS", "WASM"))
        # "hepsi": örneğin MOTORLAR başlığında beklenen (varsayılan AST/MIR/x64) motorların hepsi geçti mi
        sonuc["hepsi"] = all(sonuc["motor"].get(k, {}).get("durum") == "GECTI" for k in bas["motorlar"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", default=os.path.join(KOK, "bin", "uxb_openclaw_S087.exe"))
    ap.add_argument("--grup")
    ap.add_argument("--ad")
    ap.add_argument("--is", type=int, default=3, dest="isci")
    ap.add_argument("--web", action="store_true", help="JS (jsw+node) ve WASM (wat+wat2wasm+node) hedeflerini de çalıştır")
    ap.add_argument("--desen", help="grup adı bu düzenli ifadeyle eşleşen klasörleri çalıştır (örn. _kv_)")
    ap.add_argument("--kok", default=ORNEK, help="örneklerin aranacağı klasör (alt klasörler dahil)")
    ap.add_argument("--sonuc", default=SONUC, help="sonuç JSON dosyası (paralel çalışan her iş kendi dosyasını kullanmalı)")
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    sonuc_yolu = os.path.abspath(a.sonuc)
    dosyalar = []
    for dp, dn, fn in os.walk(os.path.abspath(a.kok)):
        for f in sorted(fn):
            if f.endswith(".uxb"):
                g = os.path.basename(dp)
                if (a.grup and g != a.grup) or (a.ad and os.path.splitext(f)[0] != a.ad):
                    continue
                if a.desen and not re.search(a.desen, g):
                    continue
                dosyalar.append(os.path.join(dp, f))
    eski = {}
    if os.path.exists(sonuc_yolu):
        eski = {r["dosya"]: r for r in json.load(open(sonuc_yolu, encoding="utf-8"))}
    t0 = time.time()
    with cf.ThreadPoolExecutor(a.isci) as ex:
        for r in ex.map(lambda p: dogrula(uxb, p, a.web), dosyalar):
            eski[r["dosya"]] = r
            m = r["motor"]
            print(f"{'OK ' if r['hepsi'] else '-- '} {r['dosya']:<60} "
                  + "  ".join(f"{k}={v['durum']}" for k, v in m.items()), flush=True)
    # silinmiş örneklerin kaydını at
    kalan = [r for d, r in sorted(eski.items()) if os.path.exists(os.path.join(KOK, d))]
    os.makedirs(os.path.dirname(sonuc_yolu), exist_ok=True)
    json.dump(kalan, open(sonuc_yolu, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    known = [r for r in kalan if r.get('has_oracle', bool(r.get('beklenen')))]
    print(f"{len(dosyalar)} örnek, {sum(1 for r in known if r['hepsi'])}/{len(known)} beklentili örnek üç motorda geçti; "
          f"{len(kalan)-len(known)} örnekte çıktı beklentisi yok, {time.time()-t0:.0f} sn")


if __name__ == "__main__":
    main()
