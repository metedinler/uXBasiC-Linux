# -*- coding: utf-8 -*-
"""uXBasic Dil Tanımı birleştirici.

docs/kitaplar/_ortak/dil_tanimi/alanlar/<alan>/bolum.md bölümlerini sırayla tek belgeye
(docs/kitaplar/UXBASIC_DIL_TANIMI.md) birleştirir ve ekleri ogeler.json / sonuc.json / yüzey
envanterlerinden MEKANİK olarak üretir (elle yazılmaz, uydurulamaz):

  Ek A  Uygunluk tablosu   — her öğe: karar, AST/MIR/x64 durumu, örnek, sorun numaraları
  Ek B  Karar bekleyenler  — ÖNERİ ve KARAR GEREKİYOR öğeleri (Mete'nin onayı için)
  Ek C  Uyum hataları      — bölümlerin bulduğu sorunlar (SORUN_TAKIP numaraları + yeni bulgular)
  Ek D  Kütüphane imza kataloğu — kutuphane_yuzeyi.json'dan 46 kütüphanenin tüm fonksiyon/sub imzaları
  Ek E  Kapsam denetimi    — lexer anahtar sözcükleri, yerleşik adlar ve kütüphanelerden belgede
                             hiç geçmeyenler (boş değilse belge eksiktir)

Kullanım: python tools/kitap/dil_tanimi_birlestir.py [--denetim-json <yol>]
Çıkış kodu: 0 = kapsam tam, 3 = kapsam eksiği var (Ek E dolu), 2 = bölüm/JSON hatası.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORTAK = os.path.join(KOK, "docs", "kitaplar", "_ortak")
DT = os.path.join(ORTAK, "dil_tanimi")
ALANLAR = os.path.join(DT, "alanlar")
CIKTI = os.path.join(KOK, "docs", "kitaplar", "UXBASIC_DIL_TANIMI.md")
GIRIS = os.path.join(DT, "00_giris.md")

MOTOR = ("AST", "MIR", "x64")
ISARET = {"GECTI": "✓", "FARKLI": "≠", "HATA": "✗", "DENENMEDI": "·", "": "·"}


def oku_json(p, varsayilan):
    if not os.path.exists(p):
        return varsayilan
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def alan_listesi():
    if not os.path.isdir(ALANLAR):
        return []
    return sorted(d for d in os.listdir(ALANLAR) if os.path.isdir(os.path.join(ALANLAR, d)))


def bolum_basligi(md):
    m = re.search(r"(?m)^#\s+(.+)$", md)
    return m.group(1).strip() if m else ""


def durum_hucresi(d):
    d = d or {}
    return " ".join(f"{m} {ISARET.get(str(d.get(m, '')).upper(), '?')}" for m in MOTOR)


def md_kacis(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def normal_ad(s):
    return re.sub(r"[^A-Z0-9_%.]", "", str(s).upper())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--denetim-json", help="workflow denetim özetlerinin JSON'u (isteğe bağlı, Ek C'ye eklenir)")
    a = ap.parse_args()

    hatalar = []
    bolumler, ogeler = [], []
    for alan in alan_listesi():
        d = os.path.join(ALANLAR, alan)
        bp = os.path.join(d, "bolum.md")
        if not os.path.exists(bp):
            hatalar.append(f"{alan}: bolum.md yok")
            continue
        md = open(bp, encoding="utf-8").read().strip()
        try:
            og = oku_json(os.path.join(d, "ogeler.json"), [])
        except json.JSONDecodeError as e:
            hatalar.append(f"{alan}: ogeler.json geçersiz ({e})")
            og = []
        if not isinstance(og, list):
            hatalar.append(f"{alan}: ogeler.json dizi değil")
            og = []
        sonuc = {}
        try:
            for r in oku_json(os.path.join(d, "sonuc.json"), []):
                sonuc[os.path.basename(r.get("dosya", ""))] = r
        except json.JSONDecodeError as e:
            hatalar.append(f"{alan}: sonuc.json geçersiz ({e})")
        for o in og:
            if isinstance(o, dict):
                o["_alan"] = alan
                # ogeler.json'daki durum yerine, varsa gerçek çalıştırma sonucunu esas al
                ornek = os.path.basename(str(o.get("ornek", "")))
                if ornek in sonuc:
                    o["_calisma"] = {m: sonuc[ornek]["motor"].get(m, {}).get("durum", "") for m in MOTOR}
                ogeler.append(o)
        bolumler.append((alan, bolum_basligi(md), md, len(og), sum(1 for r in sonuc.values() if r.get("hepsi"))))

    # ---- kapsam envanterleri
    yuzey = oku_json(os.path.join(ORTAK, "dil_yuzeyi.json"), [])
    kutup = oku_json(os.path.join(ORTAK, "kutuphane_yuzeyi.json"), [])
    govde = "\n".join(md for _, _, md, _, _ in bolumler)
    govde_ust = govde.upper()
    belgelenen = {normal_ad(o.get("ad", "")) for o in ogeler}
    for o in ogeler:
        for v in o.get("varyantlar", []) or []:
            if isinstance(v, dict):
                for w in re.findall(r"[A-Za-z_%][A-Za-z0-9_]*", str(v.get("yazim", ""))):
                    belgelenen.add(normal_ad(w))
        for w in re.findall(r"[A-Za-z_%][A-Za-z0-9_]*", str(o.get("kanonik", ""))):
            belgelenen.add(normal_ad(w))

    def geciyor(ad):
        n = normal_ad(ad)
        return n in belgelenen or re.search(r"(?<![A-Z0-9_])" + re.escape(n) + r"(?![A-Z0-9_])", govde_ust) is not None

    eksik_anahtar = sorted(r["ad"] for r in yuzey if r.get("sinif") == "anahtar" and not geciyor(r["ad"]))
    eksik_yerlesik = sorted(r["ad"] for r in yuzey if r.get("sinif") == "yerlesik" and not geciyor(r["ad"]))
    eksik_kutuphane = sorted(k["kutuphane"] for k in kutup if k["kutuphane"].upper() not in govde_ust)

    # ---- belge
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    if os.path.exists(GIRIS):
        L.append(open(GIRIS, encoding="utf-8").read().strip().replace("{{TARIH}}", tarih))
    else:
        L.append(f"# uXBasic Dil Tanımı\n\n_Üretim: {tarih} — giriş bölümü (00_giris.md) henüz yazılmadı._")
    L.append("\n## İçindekiler\n")
    for i, (alan, bas, _, n, g) in enumerate(bolumler, 1):
        L.append(f"{i}. {bas or alan} — {n} öğe, {g} örnek üç motorda geçiyor")
    L += ["A. Ek A — Uygunluk tablosu", "B. Ek B — Mete'nin kararını bekleyen konular",
          "C. Ek C — Uyum hataları", "D. Ek D — Kütüphane imza kataloğu", "E. Ek E — Kapsam denetimi", ""]
    for i, (alan, bas, md, _, _) in enumerate(bolumler, 1):
        L.append(f"\n---\n\n<!-- bölüm {i}: alanlar/{alan}/bolum.md -->\n")
        L.append(md)

    # Ek A
    L.append("\n---\n\n# Ek A — Uygunluk tablosu\n")
    L.append("Her öğe: karar durumu ve motorlardaki GERÇEK çalıştırma sonucu (örnek dosyasının `sonuc.json` kaydından; "
             "kayıt yoksa bölüm yazarının beyanı). ✓ geçti · ≠ farklı çıktı · ✗ hata · · denenmedi.\n")
    say = Counter()
    L.append("| Bölüm | Öğe | Tür | Karar | Motorlar | Örnek | Sorun |")
    L.append("|---|---|---|---|---|---|---|")
    for o in ogeler:
        dur = o.get("_calisma") or o.get("durum") or {}
        tam = all(str(dur.get(m, "")).upper() == "GECTI" for m in MOTOR)
        say["tam" if tam else "eksik"] += 1
        L.append(f"| {o['_alan']} | `{md_kacis(o.get('ad', ''))}` | {md_kacis(o.get('tur', ''))} | {md_kacis(o.get('karar', ''))} | "
                 f"{durum_hucresi(dur)} | {md_kacis(os.path.basename(str(o.get('ornek', ''))))} | "
                 f"{md_kacis(', '.join(o.get('sorunlar', []) or []))} |")
    L.insert(len(L) - len(ogeler) - 2,
             f"Toplam **{len(ogeler)}** öğe; üç motorda da geçen **{say['tam']}**, en az bir motorda sorunlu ya da denenmemiş **{say['eksik']}**.\n")

    # Ek B
    L.append("\n# Ek B — Mete'nin kararını bekleyen konular\n")
    L.append("ÖNERİ: kaynak sırasına göre önerilen kanon (onaylanınca KARARLI olur). KARAR GEREKİYOR: seçenekler bölümde.\n")
    for tur in ("KARAR GEREKİYOR", "ÖNERİ"):
        secili = [o for o in ogeler if str(o.get("karar", "")).upper().startswith(tur[:5])]
        L.append(f"\n## {tur} ({len(secili)})\n")
        for o in secili:
            L.append(f"- **{md_kacis(o.get('ad', ''))}** ({o['_alan']}): {md_kacis(o.get('karar_kaynagi', ''))}")

    # Ek C
    L.append("\n# Ek C — Uyum hataları\n")
    sorun_say = Counter(s for o in ogeler for s in (o.get("sorunlar") or []))
    L.append("SORUN_TAKIP numaralarına göre etkilenen öğe sayısı:\n")
    for s, n in sorted(sorun_say.items()):
        L.append(f"- {s}: {n} öğe")
    yeni = [o for o in ogeler if str(o.get("yeni_sorun", "")).strip()]
    L.append(f"\nBölüm yazarlarının bulduğu, SORUN_TAKIP'e henüz işlenmemiş bulgular ({len(yeni)}):\n")
    for o in yeni:
        L.append(f"- ({o['_alan']}) `{md_kacis(o.get('ad', ''))}`: {md_kacis(o['yeni_sorun'])} — örnek `{md_kacis(o.get('ornek', ''))}`")
    if a.denetim_json and os.path.exists(a.denetim_json):
        den = oku_json(a.denetim_json, [])
        L.append("\nBağımsız denetim özetleri:\n")
        for d in den:
            if isinstance(d, dict):
                L.append(f"- {d.get('alan')}: denetçi {d.get('denetci')}, bulgu {d.get('bulgu_sayisi')}, "
                         f"kabul {d.get('kabul')}, red {d.get('red')} — {md_kacis(d.get('degisiklik_ozeti', ''))}")

    # Ek D
    L.append("\n# Ek D — Kütüphane imza kataloğu\n")
    L.append("`tools/kitap/yuzey_tara.py` ile `libsx/` kaynağından otomatik çıkarılır. **Testte**: tam adı "
             "(`namespace.Ad`) `tests/` ya da `examples/` altındaki bir programda geçiyor.\n")
    for k in kutup:
        f = k.get("fonksiyon", [])
        if not f:
            continue
        L.append(f"\n## {k['kutuphane']}  ({', '.join(k.get('namespace', [])) or 'namespace yok'}; "
                 f"{len(f)} fonksiyon/sub, {k.get('sabit', 0)} sabit, testte çağrılan {sum(1 for x in f if x.get('testte'))})\n")
        L.append("| Ad | Parametreler | Dönüş | Testte |")
        L.append("|---|---|---|---|")
        for x in f:
            L.append(f"| `{x['ad']}` | `{md_kacis(x['param'])}` | {x['donus']} | {'✓' if x.get('testte') else ''} |")

    # Ek E
    L.append("\n# Ek E — Kapsam denetimi\n")
    L.append("Lexer anahtar sözcükleri, yerleşik ad adayları ve kütüphanelerden belgede HİÇ geçmeyenler. "
             "Boş değilse belge eksiktir.\n")
    L.append(f"- Anahtar sözcük ({len(eksik_anahtar)}): " + (", ".join(f"`{x}`" for x in eksik_anahtar) or "yok"))
    L.append(f"- Yerleşik ad ({len(eksik_yerlesik)}): " + (", ".join(f"`{x}`" for x in eksik_yerlesik) or "yok"))
    L.append(f"- Kütüphane ({len(eksik_kutuphane)}): " + (", ".join(f"`{x}`" for x in eksik_kutuphane) or "yok"))
    if hatalar:
        L.append("\n**Birleştirme hataları:**\n" + "\n".join(f"- {h}" for h in hatalar))

    os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
    with open(CIKTI, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    kapsam = {"anahtar": eksik_anahtar, "yerlesik": eksik_yerlesik, "kutuphane": eksik_kutuphane}
    with open(os.path.join(DT, "kapsam_eksikleri.json"), "w", encoding="utf-8") as f:
        json.dump(kapsam, f, ensure_ascii=False, indent=1)
    boyut = os.path.getsize(CIKTI) / 1024
    print(f"bölüm {len(bolumler)}, öğe {len(ogeler)} (üç motorda tam {say['tam']}), belge {boyut:.0f} KB -> {CIKTI}")
    print(f"kapsam eksiği: anahtar {len(eksik_anahtar)}, yerleşik {len(eksik_yerlesik)}, kütüphane {len(eksik_kutuphane)}")
    for h in hatalar:
        print("HATA:", h)
    if hatalar:
        return 2
    return 3 if (eksik_anahtar or eksik_yerlesik or eksik_kutuphane) else 0


if __name__ == "__main__":
    sys.exit(main())
