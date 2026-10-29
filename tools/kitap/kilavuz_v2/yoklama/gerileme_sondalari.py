# -*- coding: utf-8 -*-
"""Kılavuz V2 sırasında bulunan kusurları (SORUN_TAKIP S-480 … S-508) küçük programlarla yoklar; yeni bir derleme için ilk bakış.

Her sonda doğru davranışı bilir; her yol (AST, MIR, MIR-x64, AST-x64, JS, WASM) için sonuç şu simgelerden biridir:
  ✔  beklenen çıktıyı verdi
  ◌  açıkça reddetti (çıkış kodu sıfırdan farklı ve bir ERROR satırı var) — sessiz yanlış değildir
  ✖  yanlış çıktı verdi (sessiz hata) ya da iletisiz çöktü
  ·  bu yol için beklenti tanımlı değil
Yol başına beklenti 'ok' (tam çıktı), 'ret' (açık ret de kabul) ya da yok. Çıkış: sorun varsa 1.

Kullanım (proje kökünden):
  python tools\\kitap\\kilavuz_v2\\yoklama\\gerileme_sondalari.py --uxb bin\\uxb_kilavuz_20261013_2052.exe [--sadece S-504] [--is 3]
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yol_matrisi as ym  # noqa: E402

TUM = ("AST", "MIR", "MIR-x64", "AST-x64", "JS")
HEPSI = TUM + ("WASM",)


def sonda(kimlik, kayit, ad, kod, beklenen, ret_kabul=(), yollar=TUM):
    """beklenen: tam çıktı satırları (liste); ret_kabul: açık retin de kabul edildiği yollar; yollar: ölçülecek yollar."""
    return dict(kimlik=kimlik, kayit=kayit, ad=ad, kod=kod, beklenen=beklenen, ret_kabul=set(ret_kabul), yollar=yollar)


SONDALAR = [
    sonda("S-504", "G-ISLEC-8", "ondalık karşılaştırma değeri",
          "DIM x AS F64 = 2.5\nDIM b AS I32\nb = (x >= 0)\nPRINT b\nPRINT x >= 0\nPRINT TIMER >= 0\n", ["-1", "-1", "-1"]),
    sonda("S-504-b", "G-ISLEC-8", "ondalık karşılaştırma değeri: AND ile bileşik (rnd_randomize örneği)",
          "RANDOMIZE 7\nDIM r AS F64 = RND(1)\nPRINT (r >= 0) AND (r < 1)\nDIM x AS F64 = 2.5\nPRINT (x >= 0) AND (x < 10)\nPRINT (x < 0) OR (x > 1)\n", ["-1", "-1", "-1"],
          ret_kabul=("JS",)),
    sonda("S-506", "G-TIP-17", "tamsayı dönüşümü ondalığı keser",
          "DIM p AS F64 = 3.9\nPRINT I64(p); \" \"; U8(p); \" \"; I32(p); \" \"; I8(-3.9)\n", ["3 3 3 -3"]),
    sonda("S-499", "G-KTIP-7", "RATIONAL toplama (MIR dışında açık ret)",
          "DIM a AS RATIONAL\nDIM b AS RATIONAL\nDIM c AS RATIONAL\na = 1\nb = 2\nc = a + b\nPRINT c\n", ["3/1"],
          ret_kabul=("AST", "MIR-x64", "AST-x64", "JS", "WASM"), yollar=HEPSI),
    sonda("S-507", "G-KTIP-8", "RATIONAL sıfıra bölme (iletisiz çökme yok)",
          "DIM a AS RATIONAL\nDIM b AS RATIONAL\nDIM c AS RATIONAL\na = 3\nc = a / b\nPRINT c\n", None,
          ret_kabul=("AST", "MIR", "MIR-x64", "AST-x64", "JS", "WASM"), yollar=HEPSI),
    sonda("S-446/S-503", "G-TIP-13", "F32 bildirim başlangıcı yuvarlanır",
          "DIM f AS F32 = 16777217\nPRINT f\n", ["1.677722e+07"]),
    sonda("S-503", "G-TIP-15", "F32 dizi elemanı yuvarlanır ve 7 hane yazılır",
          "DIM a(2) AS F32\na(0) = 16777217\nPRINT a(0)\n", ["1.677722e+07"]),
    sonda("S-502", "G-TIP-16", "F32 dizi elemanı PRINT",
          "DIM a(2) AS F32\na(0) = 2.5\na(1) = 1.25\nPRINT a(0)\nPRINT a(1)\n", ["2.5", "1.25"]),
    sonda("S-509", "G-TIP-19", "F32 dizi elemanı aritmetikte ve F64 değişkene atamada okunur (2333 MIR-x64 gerilemesi)",
          "DIM a(2) AS F32\na(0) = 2.5\na(1) = 1.25\nDIM y AS F64\ny = a(0)\nPRINT a(0) + a(1)\nPRINT y\nPRINT a(0) * 2\n", ["3.75", "2.5", "5"]),
    sonda("S-510", "G-TIP-20", "F32 değeri tek duyarlığa yuvarlanır (değer düzeyi: yazdırma biçimi değil)",
          "DIM f AS F32 = 16777217\nPRINT f - 16777216\nDIM g AS F32\ng = 16777217\nPRINT g - 16777216\n", ["0", "0"]),
    sonda("S-511", "G-TIP-21", "F32(x) dönüşümünün sonucu aritmetik işlenen olur",
          "DIM d AS F64 = 2.5\nPRINT F32(d) + 1\nPRINT F32(d) * 2\n", ["3.5", "5"]),
    sonda("S-512", "G-TIP-22", "F64 değişkenden başlatılan F32 değişken aritmetikte doğru (DIM t AS F32 = d)",
          "DIM d AS F64 = 2.5\nDIM t AS F32 = d\nPRINT t + 1\n", ["3.5"]),
    sonda("S-480-A", "—", "çok boyutlu dizi (eski AST-x64 açıkça reddeder)",
          "DIM m(2, 3) AS I32\nm(1, 2) = 42\nPRINT m(1, 2)\n", ["42"], ret_kabul=("AST-x64",)),
    sonda("S-480-D", "—", "CONTINUE",
          "DIM i AS I32\nDIM t AS I32\nt = 0\nFOR i = 1 TO 4\n  IF i = 2 THEN CONTINUE\n  t = t + i\nNEXT\nPRINT t\n", ["8"]),
    sonda("S-219", "G-ISLEC-1", "ROL / ROR döndürme (U8 129 ROL 1 = 3)",
          "DIM x AS U8 = 129\nPRINT x ROL 1\nPRINT x ROR 1\n", ["3", "192"]),
    sonda("S-459", "G-DIL-14", "ondalık + metin birleştirmesi derleme zamanında reddedilir (UXB_MIXED_STRING_NUMERIC)",
          "DIM f AS F32 = 2.5\nPRINT f + \"a\"\n", None, ret_kabul=HEPSI, yollar=HEPSI),
    sonda("S-508", "G-TIP-18", "FIX sonucu değişkene atanır (ret kusurdur)",
          "DIM p AS F64 = 3.9\nDIM a AS I32\na = FIX(p)\nPRINT a\n", ["3"]),
    sonda("S-480-B", "—", "sınır dışı dizi erişimi hata verir",
          "DIM a(3) AS I32\na(0) = 5\na(9) = 7\nPRINT a(0)\n", None, ret_kabul=("AST", "MIR"), yollar=("AST", "MIR")),
    sonda("S-505", "G-ISLEC-9", "-(karşılaştırma) = 1",
          "DIM x AS F64 = 2.5\nDIM n AS I32 = 5\nPRINT -(x > 1)\nPRINT -(n > 1)\n", ["1", "1"]),
    # --- 2026-10-14: değer düzeyinde (çıkarma ile) F32, WASM bit işleçleri, bileşik ROL/ROR, STRING += sayı
    sonda("S-515", "G-TIP-23", "F32: yordam içindeki yerel değişkene yazma tek duyarlığa yuvarlanır",
          "SUB Yerel()\n  DIM y AS F32 = 16777217\n  PRINT y - 16777216\n  DIM z AS F32\n  z = 16777217\n  PRINT z - 16777216\nEND SUB\nYerel()\n", ["0", "0"]),
    sonda("S-516", "G-TIP-24", "F32: TYPE alanı aritmetik işlenen olur",
          "TYPE R\n  v AS F32\nEND TYPE\nDIM r AS R\nr.v = 2.5\nPRINT r.v + 1\nPRINT r.v * 2\nr.v = 16777217\nPRINT r.v - 16777216\n", ["3.5", "5", "0"]),
    sonda("S-517", "G-TIP-25", "F32: yordam içinden genel değişkene atama yuvarlanır",
          "DIM gl AS F32\nSUB Yaz()\n  gl = 16777217\n  PRINT gl - 16777216\nEND SUB\nYaz()\n", ["0"]),
    sonda("S-518", "G-TIP-26", "F32: BYVAL parametre yuvarlanır",
          "SUB B(BYVAL p AS F32)\n  PRINT p - 16777216\nEND SUB\nB(16777217)\n", ["0"]),
    sonda("S-519", "G-TIP-27", "F32: aritmetik ara sonuç dört yolla aynı (AST ayrışıyor)",
          "DIM u AS F32 = 16777216\nPRINT (u + 1) - 16777216\n", ["0"]),
    sonda("S-513", "G-WASM-21", "WASM: işaretsiz SHR (U8, U32)",
          "DIM a AS U8 = 129\nPRINT a SHR 1\nDIM u AS U32 = 16\nPRINT u SHR 2\n", ["64", "4"], yollar=HEPSI),
    sonda("S-514", "G-WASM-22", "WASM: ROL / ROR (I32, U8)",
          "DIM i AS I32 = 20\nPRINT i ROL 1\nDIM a AS U8 = 129\nPRINT a ROR 1\n", ["40", "192"], yollar=HEPSI),
    sonda("S-520", "G-ISLEC-10", "ROL= / ROR= bileşik atama döndürür",
          "DIM a AS U8 = 129\na ROL= 1\nPRINT a\nDIM b AS U16 = 32769\nb ROL= 2\nPRINT b\n", ["3", "6"]),
    sonda("S-523", "G-NESNE-29", "MAGIC TOSTRING'li sınıfta F64 metot sonucu değişkene yazılır (AST gerilemesi, 20261013 12:37'den beri)",
          "CLASS Balik\nPRIVATE\n    __B AS F64\nPUBLIC\n    CONSTRUCTOR(B AS F64)\n        THIS.__B = B\n    END CONSTRUCTOR\n    METHOD GetB() AS F64\n        RETURN THIS.__B\n    END METHOD\n    MAGIC TOSTRING() AS STRING\n        RETURN \"x\"\n    END MAGIC\nEND CLASS\nDIM f AS Balik = NEW Balik(2.5)\nDIM b AS F64\nb = f.GetB()\nPRINT b\nPRINT f.GetB()\n", ["2.5", "2.5"], yollar=("AST", "MIR", "MIR-x64", "JS")),  # eski AST-x64 yolu 20261007'den beri başka nedenle çöp yazar (G-NESNE-8 ailesi)
    sonda("S-521", "G-DIL-16", "STRING += sayı reddedilir (UXB_MIXED_STRING_NUMERIC kapısı)",
          "DIM s AS STRING = \"a\"\ns += 7\nPRINT s\n", None, ret_kabul=HEPSI, yollar=HEPSI),
    # --- 2026-10-14 öğleden sonra: model paketlerinin bulduğu AST gerilemeleri, GOSUB/RETURN, eski AST-x64
    sonda("S-539", "G-MODUL-6", "NAMESPACE dizisine nitelikli erişim (AST gerilemesi, 20261013 12:37'den beri)",
          "NAMESPACE sayac\n  DIM kutu(3) AS I32\nEND NAMESPACE\nsayac.kutu(2) = 7\nPRINT sayac.kutu(2)\n", ["7"], ret_kabul=("AST-x64",)),
    sonda("S-540", "G-DIL-17", "1025 değişkenli program (AST gerilemesi: max 1024)",
          "\n".join(f"DIM v{i} AS I32 = {i}" for i in range(1025)) + "\nPRINT v1024\n", ["1024"], yollar=("AST", "MIR", "MIR-x64")),
    sonda("S-535", "G-DIS-13", "FFI'ye boş metin geçirmek (AST gerilemesi: segmentation violation)",
          "DIM e AS STRING\ne = \"\"\nDIM bad AS I32\nbad = CALL(DLL, \"kernel32.dll\", \"IsBadStringPtrA\", I32, STDCALL, \"STRPTR,U64\", e, 16)\nPRINT bad\n"
          "DIM n AS U64\nn = CALL(DLL, \"ucrtbase.dll\", \"strlen\", U64, CDECL, \"STRPTR\", \"\")\nPRINT n\n", ["0", "0"], yollar=("AST", "MIR", "MIR-x64", "AST-x64")),
    sonda("S-532", "G-AKIS-4", "döngü içinde GOSUB (AST: RETURN döngüyü bitirir)",
          "DIM i AS I32\nDIM t AS I32 = 0\nFOR i = 1 TO 3\n  GOSUB Ekle\nNEXT\nPRINT t\nEND\nEkle:\n  t = t + i\nRETURN\n", ["6"], ret_kabul=("AST-x64",), yollar=HEPSI),
    sonda("S-537", "G-AKIS-5", "GOSUB'suz RETURN hata verir (AST verir; öteki yollar sessiz çıkar)",
          "DIM x AS I32 = 1\nPRINT x\nRETURN\nPRINT 2\n", None, ret_kabul=HEPSI, yollar=HEPSI),
    sonda("S-543", "G-YORDAM-8", "AST/MIR: 100 seviye özyineleme doğru çalışır (0253: 50 üstünde iletisiz erişim ihlali; k1022i'den beri 999'a kadar doğru)",
          "FUNCTION T(n AS I64) AS I64\n  IF n = 0 THEN RETURN 0\n  RETURN n + T(n - 1)\nEND FUNCTION\nPRINT T(100)\n", ["5050"], yollar=("AST", "MIR")),
    sonda("S-543-B", "G-YORDAM-8", "AST/MIR: çok derin özyineleme (5000) iletisiz çökmez, açık hata verir (call stack limit exceeded)",
          "FUNCTION T(n AS I64) AS I64\n  IF n = 0 THEN RETURN 0\n  RETURN n + T(n - 1)\nEND FUNCTION\nPRINT T(5000)\n", None, ret_kabul=("AST", "MIR"), yollar=("AST", "MIR")),
    sonda("S-524", "G-ISLEC-11", "F64 tekli eksi (eski AST-x64 bit düzenini eksiltir)",
          "DIM x AS F64 = -2.5\nx = -x\nPRINT x\nDIM a AS F64 = 2.5\nPRINT -a\n", ["2.5", "-2.5"]),
]


def sonuc_simge(rc, cikti, bek, ret_kabul_mi):
    """bek None ise 'hata beklenir' (başarıyla çıktı yazmak sessiz yanlıştır)."""
    satir = [s.strip() for s in cikti]
    if bek is not None and rc in (0, "0") and satir == [b.strip() for b in bek]:
        return "✔"
    if rc in (0, "0"):
        return "✖"
    # çıkış kodu sıfırdan farklı
    if isinstance(rc, int) and rc > 0x80000000:
        return "✖"            # işletim sistemi istisnası (iletisiz çökme)
    if any("ERROR" in s or "error" in s or "requires" in s or "host binding" in s or "Aborting" in s for s in satir) or rc == "DERLENMEDI":
        return "◌" if (ret_kabul_mi or bek is None) else "✖"
    return "✖"


def calistir(uxb, s):
    ham = ym.kos(uxb, s["kod"])
    satir = {}
    for y in s["yollar"]:
        rc, c = ham[y]
        satir[y] = (sonuc_simge(rc, c, s["beklenen"], y in s["ret_kabul"]), rc, c)
    return s, satir


def tani_dosyasi_sondalari(uxb):
    """S-498 (çalışma anı hataları yapılandırılmış dosyaya yazılır mı) ve S-410 (kütüphane tipi yedi hedef)."""
    sonuc = []
    d = tempfile.mkdtemp(prefix="gs_")
    try:
        yol = os.path.join(d, "t.uxb")
        open(yol, "w", encoding="utf-8", newline="\r\n").write("THROW 5\nPRINT 1\n")
        for ad, ek in (("AST", ["--interpreter-backend", "AST"]), ("MIR", ["--interpreter-backend", "MIR"])):
            dj = os.path.join(d, f"all_{ad}.json")
            subprocess.run([uxb, "run", yol, *ek, "--all-diagnostics-json-out", dj, "--out-root", os.path.join(d, ad)], cwd=KOK, capture_output=True, timeout=90)
            n = -1
            if os.path.exists(dj):
                try:
                    n = len(json.load(open(dj, encoding="utf-8")).get("diagnostics", []))
                except Exception:
                    pass
            sonuc.append(("S-498", "G-HATA-11", f"çalışma anı hatası all_diagnostics.json'a yazılır ({ad})", "✔" if n > 0 else "✖", f"kayıt sayısı={n}"))
        src = os.path.join(KOK, "tests", "library_type_contract", "library_shared_value.uxb")
        hedefler = [("AST", ["run", src, "--interpreter-backend", "AST"]), ("AST-x64", ["bld", src, "--build-x64", "--x64-mode", "AST"]),
                    ("MIR-x64", ["bld", src, "--build-x64", "--x64-mode", "MIR"]), ("JS", ["jsw", src]), ("WAT", ["wat", src])]
        tamam = []
        for ad, a in hedefler:
            dj = os.path.join(d, f"lt_{ad}.json")
            p = subprocess.run([uxb, *a, "--all-diagnostics-json-out", dj, "--out-root", os.path.join(d, "o" + ad)], cwd=KOK, capture_output=True, timeout=240)
            kod = None
            if os.path.exists(dj):
                try:
                    kod = next((x["code"] for x in json.load(open(dj, encoding="utf-8")).get("diagnostics", []) if x.get("code") == "UXB_LIBTYPE_PROVIDER_UNAVAILABLE"), None)
                except Exception:
                    pass
            tamam.append((ad, p.returncode == 1 and kod is not None))
        ok = all(t for _, t in tamam)
        sonuc.append(("S-410", "G-HEDEF-20", "TEXT_REF yedi hedefte UXB_LIBTYPE_PROVIDER_UNAVAILABLE + çıkış 1 (beşi denendi)", "✔" if ok else "✖", " ".join(f"{a}={'✔' if t else '✖'}" for a, t in tamam)))
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
    return sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uxb", required=True)
    ap.add_argument("--sadece")
    ap.add_argument("--is", type=int, default=3, dest="isci")
    ap.add_argument("--ayrinti", action="store_true")
    a = ap.parse_args()
    uxb = os.path.abspath(a.uxb)
    secili = [s for s in SONDALAR if not a.sadece or a.sadece in s["kimlik"] or a.sadece in s["kayit"]]
    sorun = 0
    print(os.path.basename(uxb))
    print(f"{'kayıt':<12} {'G-kaydı':<11} " + " ".join(f"{y:<8}" for y in HEPSI) + "  sonda")
    with cf.ThreadPoolExecutor(a.isci) as ex:
        for s, satir in ex.map(lambda x: calistir(uxb, x), secili):
            hucre = " ".join(f"{(satir[y][0] if y in satir else '·'):<8}" for y in HEPSI)
            print(f"{s['kimlik']:<12} {s['kayit']:<11} {hucre}  {s['ad']}")
            if any(v[0] == "✖" for v in satir.values()):
                sorun += 1
                if a.ayrinti:
                    for y, (sm, rc, c) in satir.items():
                        if sm == "✖":
                            print(f"      {y}: rc={rc} {' | '.join(c[:3])[:160]}")
    if not a.sadece or a.sadece in ("S-498", "S-410", "G-HATA-11", "G-HEDEF-20"):
        for kimlik, kayit, ad, sm, ayr in tani_dosyasi_sondalari(uxb):
            print(f"{kimlik:<12} {kayit:<11} {sm:<8} {ad}  [{ayr}]")
            if sm == "✖":
                sorun += 1
    print(f"\nsorunlu sonda: {sorun}")
    sys.exit(1 if sorun else 0)


if __name__ == "__main__":
    main()
