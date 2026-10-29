# -*- coding: utf-8 -*-
"""uXBasic Hedeflenen Sistem ve Kullanma Kılavuzu V2 üreticisi.

sablon/*.md dosyalarını sırayla birleştirir; yer tutucuları DOĞRULANMIŞ içerikle doldurur:

  {{ORNEK:grup/ad}}                  docs/kitaplar/_ortak/ornekler/<grup>/<ad>.uxb: kod + beklenen çıktı + motor durumu
  {{ORNEK:grup/ad|baslik=Metin}}     aynısı, üstte kalın başlıkla
  {{ORNEK:grup/ad|durum=gizle}}      motor durum satırını göstermez
  {{ORNEK:grup/ad|anlat=evet}}       örnek dosyasındaki ACIKLAMA metnini kodun üstünde alıntı bloğu olarak gösterir (içindeki G-kayıtları "anılmış" sayılır)
  {{ORNEKKOD:grup/ad}}               yalnız kod (çıktısız, durumsuz)
  {{ARAC:grup/ad|baslik=..}}         tools/kitap/kilavuz_v2/arac_ornekleri altındaki betik (Python/PowerShell/JS) + beklenen çıktı + doğrulama
  {{CLI_SECENEKLER}}                 uxb --help kayıt listesinden seçenek tabloları
  {{ESLIK_OZETI}}                    örnek sonuçlarından motor eşliği özeti
  {{ESLIK_TOPLAM}}                   aynı verinin tek cümlelik toplamı (her motorda geçen / beklentili örnek)
  {{SINIRLAR}}                       veri/sinirlar.txt: bilinen sınırlar kataloğu (alan alan tablo + tür özeti)
  {{SINIRLAR:ALAN}}                  yalnız bir alanın tablosu (örn. CLI, JS)
  {{ONISLEMCI}}                      veri/onislemci.txt: 125 önişlemci yönergesinin dizini (kaynaktaki listeyle karşılaştırılır)
  {{ONISLEMCI:Grup adı}}             yalnız bir grubun tablosu
  {{KUTUPHANELER}}                   include/modules/*.uxmh dizini: başlık, ad alanı, işlev sayısı (kaynaktan sayılır), DLL sembol denetimi
                                     (veri/dll_denetim.json), el yazması açıklama (veri/kutuphaneler.txt) ve örnek durumu
  {{KUTUPHANELER:Kategori}}          yalnız bir kategorinin tablosu
  {{SURUM}}                          derleyici dosyası + SHA256 (doğrulamada kullanılan)
  {{KARARLAR}}                       her bölümün 'N.k … programlama kararları' maddelerini bölüm bölüm toplar (K<bölüm>.<sıra> numaralı)
  {{KARARLAR:OZET}}                  yalnız özet tablo: bölüm başına karar sayısı
  {{ANAHTAR_SOZCUKLER}}              Ek A: lexer_keyword_table.fbs'den gruplu sözcük tablosu + 18.09 tasarım karşılaştırması + bağlamsal sözcükler
  {{YERLESIK_ISLEVLER}}              Ek B: veri/yerlesik_islevler.csv (uxb sem --type-infer-report-csv-out) + veri/islev_aciklamalari.txt
  {{ONISLEMCI_DIZINI}}               Ek C: önişlemci yönergelerinin alfabetik dizini (söz dizimi, durum)
  {{CALLDLL_YOGUN}}                  libsx modüllerinde `CALL(DLL, …)` kullanan modül sayısı ve en yoğun altı modül (kaynaktan sayılır)

Sonuç dosyaları (ornek_dogrula.py --web çıktıları) SONUC_DOSYALARI sırasıyla birleştirilir; sonrakiler öncekini ezer.
Referans verilen bir örnek bulunamazsa ya da AST/MIR/x64'te beklenen çıktıyı vermiyorsa üretim UYARI yazar;
--sert verilirse çıkış kodu 1 olur (sahte "çalışıyor" yazılmasın).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SABLON = os.path.join(os.path.dirname(__file__), "sablon")
VERI = os.path.join(os.path.dirname(__file__), "veri")
ORNEK = os.path.join(KOK, "docs", "kitaplar", "_ortak", "ornekler")
ORTAK = os.path.join(KOK, "docs", "kitaplar", "_ortak")
CIKTI = os.path.join(KOK, "docs", "tasarim", "uXBasic_Hedeflenen_Sistem_ve_Kullanma_Kilavuzu_V2_TR.md")
RAPOR = os.path.join(KOK, "docs", "tasarim", "kilavuz_v2_uretim_raporu.json")
SONUC_DOSYALARI = ["ornek_sonuclari_web_20261014_0253.json", "ornek_sonuclari_web_20261025_s672.json"]
EXE = os.path.join(KOK, "bin", "uxb_kilavuz_20261014_0253.exe")
# Başka bir derlemenin sonuçlarıyla "ne olurdu" üretimi (ana kitaba dokunmadan: --cikti ile başka dosyaya yazın):
#   UXB_KILAVUZ_SONUC=ornek_sonuclari_web_20261013_1704.json  UXB_KILAVUZ_EXE=bin\uxb_kilavuz_20261013_1704.exe  python uret.py --cikti x.md
if os.environ.get("UXB_KILAVUZ_SONUC"):
    SONUC_DOSYALARI = [s for s in os.environ["UXB_KILAVUZ_SONUC"].split(",") if s]
if os.environ.get("UXB_KILAVUZ_EXE"):
    EXE = os.path.abspath(os.environ["UXB_KILAVUZ_EXE"])
YARDIM = None  # --yardim ile verilir (uxb --help çıktısı)

SIMGE = {"GECTI": "✔", "ACIK_RET": "◌", "HATA": "✖", "FARKLI": "≠", "BEKLENTI_YOK": "·"}
MOTORLAR = ["AST", "MIR", "x64", "JS", "WASM"]
uyarilar = []
kullanilan = {}
anlatilan = []  # |anlat=evet ile kitaba giren ACIKLAMA metinleri (G-kayıt tutarlılık denetimine katılır)


def sonuclari_yukle():
    s = {}
    for ad in SONUC_DOSYALARI:
        p = os.path.join(ORTAK, ad)
        if os.path.exists(p):
            for r in json.load(open(p, encoding="utf-8")):
                s[r["dosya"]] = r
    return s


def ornek_oku(yol):
    satirlar = open(yol, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    kod, beklenen, konu, aciklama = [], [], "", ""
    for s in satirlar:
        t = s.strip()
        if re.match(r"(?i)^'\s*(MOTORLAR|CALISMA):", t):
            continue
        if t.startswith("'="):
            beklenen.append((t[2:][1:] if t[2:3] == " " else t[2:]).rstrip())
        elif re.match(r"(?i)^'\s*KONU:", t):
            konu = t.split(":", 1)[1].strip()
        elif re.match(r"(?i)^'\s*KOMUTLAR:", t):
            pass
        elif re.match(r"(?i)^'\s*ACIKLAMA:", t):
            aciklama = t.split(":", 1)[1].strip()
        else:
            kod.append(s.rstrip())
    while kod and not kod[-1]:
        kod.pop()
    while kod and not kod[0]:
        kod.pop(0)
    return "\n".join(kod), beklenen, konu, aciklama


ACIK_RET_IZI = re.compile(r"(?i)refus|not implemented|is not supported|does not support|unsupported|desteklenm|henuz uygulanmad|"
                          r"NATIVE_ONLY|fail-closed|not available|lowering unavailable|kapisi|reddedil|requires native|cannot be emitted|must be compile-time|in current backend|build_all.bat failed|"
                          r"UXB_LIBTYPE_PROVIDER_UNAVAILABLE|provider unavailable")


def sinif(v):
    """Eski sonuç kayıtlarını yeni kurallara göre yeniden sınıflar: derleyicinin açıkça reddettiği şey 'açık ret',
    çalışma anında 'host binding missing' diyerek duran şey 'yürütme hatası'tır; ikisi de sessiz yanlış çıktı değildir."""
    d = v["durum"]
    if d == "HATA":
        satirlar = v.get("cikti", [])
        if v.get("rc") in (-8, -9) or any(s in ("ZAMAN_ASIMI", "CIKTI_SINIRI_ASILDI") for s in satirlar):
            return d  # zaman aşımı / çıktı sınırı gerçek hatadır; programın kendi çıktısındaki "reddedildi" derleyicinin açık reti değildir
        if any(ACIK_RET_IZI.search(s) for s in satirlar):
            return "ACIK_RET"
        if any("host binding missing" in s for s in satirlar):
            return "YURUTME_HATASI"
    return d


SIMGE["YURUTME_HATASI"] = "✖y"


def durum_satiri(rec):
    parcalar = []
    for m in MOTORLAR:
        v = (rec or {}).get("motor", {}).get(m)
        if not v:
            parcalar.append(f"{m} —")
        else:
            d = sinif(v)
            parcalar.append(f"{m} {SIMGE.get(d, '?')}")
    return "Motor durumu: " + " · ".join(parcalar)


def ornek_yer_tutucu(ref, secenek, sonuclar, sadece_kod=False):
    yol = os.path.join(ORNEK, ref.replace("/", os.sep) + ".uxb")
    rel = "docs/kitaplar/_ortak/ornekler/" + ref + ".uxb"
    if not os.path.exists(yol):
        uyarilar.append(f"ÖRNEK YOK: {ref}")
        return f"> ⚠ **Örnek bulunamadı:** `{ref}`"
    kod, beklenen, konu, aciklama = ornek_oku(yol)
    rec = sonuclar.get(rel)
    kullanilan[ref] = rec
    if rec is None:
        uyarilar.append(f"DOĞRULANMAMIŞ (sonuç kaydı yok): {ref}")
    else:
        for m in rec.get("motorlar", ["AST", "MIR", "x64"]):
            v = rec["motor"].get(m)
            if v and v["durum"] != "GECTI" and beklenen:
                uyarilar.append(f"{ref}: {m} {sinif(v)}")
    cikti = []
    if secenek.get("baslik"):
        cikti.append(f"**{secenek['baslik']}**\n")
    if secenek.get("anlat") == "evet" and aciklama and not sadece_kod:
        anlatilan.append(aciklama)
        cikti.append("> " + aciklama + "\n")
    cikti.append("```basic\n" + kod + "\n```")
    if sadece_kod:
        return "\n".join(cikti)
    if beklenen and secenek.get("cikti") != "gizle":
        cikti.append("Çıktı:\n\n```text\n" + "\n".join(beklenen) + "\n```")
    if secenek.get("durum") != "gizle":
        cikti.append("*" + durum_satiri(rec) + "*")
    return "\n\n".join(cikti)


ARAC_KLASOR = os.path.join(os.path.dirname(__file__), "arac_ornekleri")
ARAC_SONUC = os.path.join(ORTAK, "arac_sonuclari.json")
# Araç örneği, derleyicideki AÇIK ve kayıtlı bir kusur yüzünden düşüyorsa uyarı değil, kusuru adıyla anan bir ✖ olarak gösterilir.
# Beklenen çıktı DEĞİŞTİRİLMEZ (örnek doğru sonucu bekler); kusur giderilince girdi kaldırılır. Her girdi SORUN_TAKIP'ta kayıtlı olmalıdır.
ARAC_BILINEN_KUSUR = {
    "dis/uxclazz_uretici": "G-NESNE-29, S-523",
}
ARAC_DIL = {".py": "python", ".ps1": "powershell", ".js": "javascript"}


def arac_yer_tutucu(ref, secenek):
    """{{ARAC:grup/ad}}: arac_ornekleri altındaki betiği (kod + beklenen çıktı + doğrulama durumu) yazar."""
    yol = None
    for uz in ARAC_DIL:
        p = os.path.join(ARAC_KLASOR, ref.replace("/", os.sep) + uz)
        if os.path.exists(p):
            yol = p
            break
    if not yol:
        uyarilar.append(f"ARAÇ ÖRNEĞİ YOK: {ref}")
        return f"> ⚠ **Araç örneği bulunamadı:** `{ref}`"
    uz = os.path.splitext(yol)[1]
    yorum = "//" if uz == ".js" else "#"
    kod, beklenen, aciklama = [], [], ""
    for s in open(yol, encoding="utf-8").read().replace("\r\n", "\n").split("\n"):
        t = s.strip()
        if t.startswith(yorum + "="):
            beklenen.append((t[len(yorum) + 1:][1:] if t[len(yorum) + 1:len(yorum) + 2] == " " else t[len(yorum) + 1:]).rstrip())
        elif re.match(r"^" + re.escape(yorum) + r"\s*(KONU|KOMUTLAR|ACIKLAMA):", t):
            if re.match(r"^" + re.escape(yorum) + r"\s*ACIKLAMA:", t):
                aciklama = t.split(":", 1)[1].strip()
            continue
        else:
            kod.append(s.rstrip())
    while kod and not kod[0]:
        kod.pop(0)
    while kod and not kod[-1]:
        kod.pop()
    rel = os.path.relpath(yol, KOK).replace("\\", "/")
    rec = None
    if os.path.exists(ARAC_SONUC):
        rec = next((r for r in json.load(open(ARAC_SONUC, encoding="utf-8")) if r["dosya"] == rel), None)
    if rec is None:
        uyarilar.append(f"ARAÇ ÖRNEĞİ DOĞRULANMAMIŞ: {ref}")
        durum = "doğrulanmadı"
    elif rec["durum"] != "GECTI":
        kusur = ARAC_BILINEN_KUSUR.get(ref)
        if kusur:
            durum = f"✖ {rec['durum']} (bilinen derleyici kusuru: {kusur})"
        else:
            uyarilar.append(f"ARAÇ ÖRNEĞİ BAŞARISIZ: {ref} ({rec['durum']})")
            durum = "✖ " + rec["durum"]
    else:
        durum = "✔ geçti"
    cikti = []
    if secenek.get("baslik"):
        cikti.append(f"**{secenek['baslik']}**\n")
    if secenek.get("anlat") == "evet" and aciklama:
        anlatilan.append(aciklama)
        cikti.append("> " + aciklama + "\n")
    cikti.append(f"```{ARAC_DIL[uz]}\n" + "\n".join(kod) + "\n```")
    if beklenen and secenek.get("cikti") != "gizle":
        cikti.append("Çıktı:\n\n```text\n" + "\n".join(beklenen) + "\n```")
    cikti.append(f"*Araç doğrulaması: {durum} — proje kökünden `python tools\\kitap\\arac_dogrula.py` ile yinelenir.*")
    return "\n\n".join(cikti)


def cli_aciklamalari():
    """veri/cli_aciklama.txt: 'seçenek :: grup :: açıklama' satırları. Dosya sırası = tablo sırası."""
    p = os.path.join(VERI, "cli_aciklama.txt")
    sonuc, sira = {}, []
    for s in open(p, encoding="utf-8").read().splitlines():
        if not s.strip() or s.startswith("#"):
            continue
        parca = s.split(" :: ", 2)
        if len(parca) == 3:
            sonuc[parca[0].strip()] = (parca[1].strip(), parca[2].strip())
            sira.append(parca[0].strip())
    return sonuc, sira


def cli_secenekleri():
    """uxb --help 'KAYITLI TÜM CLI ANAHTARLARI' kayıtlarını, el yazması Türkçe açıklamalarla gruplu tablolara çevirir.
    Kayıtta olup açıklaması olmayan ya da açıklaması olup kayıtta olmayan seçenek UYARI üretir."""
    if not YARDIM or not os.path.exists(YARDIM):
        uyarilar.append("CLI yardım dosyası yok (--yardim)")
        return "> ⚠ CLI yardım dosyası verilmedi."
    metin = open(YARDIM, encoding="utf-8").read().splitlines()
    i = next((k for k, s in enumerate(metin) if "KAYITLI TÜM CLI ANAHTARLARI" in s), None)
    if i is None:
        return "> ⚠ Kayıtlı CLI anahtarları bulunamadı."
    kayit = {}
    for s in metin[i + 1:]:
        m = re.match(r"\s+(-{1,2}[A-Za-z0-9\-]+)(?:\s+(<[^>]+>))?\s+\[([^\]]+)\]\s*:\s*([^|]+)\|\s*(.*)$", s)
        if m:
            ad, arg, kod, grup, dogrulama = m.groups()
            kayit[ad] = (arg or "", kod)
    acik, sira = cli_aciklamalari()
    for ad in kayit:
        if ad not in acik:
            uyarilar.append(f"CLI seçeneği açıklamasız: {ad}")
    for ad in acik:
        if ad not in kayit:
            uyarilar.append(f"CLI açıklaması var, kayıtta yok: {ad}")
    gruplar = {}
    for ad in sira:
        g, a = acik[ad]
        arg, kod = kayit.get(ad, ("", "—"))
        gruplar.setdefault(g, []).append((ad, arg, kod, a))
    toplam = sum(len(v) for v in gruplar.values())
    sat = [f"Kayıtlı seçenek sayısı: **{len(kayit)}**; aşağıda açıklamalı olarak **{toplam}** seçenek gruplanmıştır.\n"]
    for g, lst in gruplar.items():
        sat.append(f"**{g}** ({len(lst)} seçenek)\n")
        sat.append("| Seçenek | Değer | Kısa kod | Ne işe yarar? |\n|---|---|---|---|")
        for ad, arg, kod, a in lst:
            sat.append(f"| `{ad}` | {('`' + arg + '`') if arg else ''} | `{kod}` | {a} |")
        sat.append("")
    return "\n".join(sat)


def esdegerlik_ozeti(sonuclar):
    gruplar = {}
    for dosya, rec in sonuclar.items():
        if not rec.get("beklenen"):
            continue
        g = dosya.split("/")[-2]
        d = gruplar.setdefault(g, {m: [0, 0] for m in MOTORLAR})
        for m in MOTORLAR:
            v = rec["motor"].get(m)
            if v:
                d[m][1] += 1
                d[m][0] += 1 if v["durum"] == "GECTI" else 0
    sat = ["| Örnek grubu | " + " | ".join(MOTORLAR) + " |", "|---|" + "---|" * len(MOTORLAR)]
    toplam = {m: [0, 0] for m in MOTORLAR}
    for g in sorted(gruplar):
        hucre = []
        for m in MOTORLAR:
            a, b = gruplar[g][m]
            toplam[m][0] += a
            toplam[m][1] += b
            hucre.append(f"{a}/{b}" if b else "—")
        sat.append(f"| {g} | " + " | ".join(hucre) + " |")
    sat.append("| **Toplam** | " + " | ".join(f"**{toplam[m][0]}/{toplam[m][1]}**" for m in MOTORLAR) + " |")
    return "\n".join(sat)


def esdegerlik_toplami(sonuclar):
    """Tek cümlelik toplam: çıktı beklentisi olan örneklerde her motorda geçen sayı."""
    toplam = {m: [0, 0] for m in MOTORLAR}
    for rec in sonuclar.values():
        if not rec.get("beklenen"):
            continue
        for m in MOTORLAR:
            v = rec["motor"].get(m)
            if v:
                toplam[m][1] += 1
                toplam[m][0] += 1 if v["durum"] == "GECTI" else 0
    return "Çıktı beklentisi olan örneklerde geçen sayılar: " + ", ".join(f"{m} **{a}/{b}**" for m, (a, b) in toplam.items()) + "."


SINIR_ALANLARI = {
    "CLI": "Komut satırı (CLI)", "DIL": "Dil ve ön yüz", "TIP": "Veri tipleri", "ISLEC": "İşleçler",
    "METIN": "Metin işlevleri", "KOLEKSIYON": "Koleksiyonlar", "AKIS": "Akış denetimi", "YORDAM": "Yordamlar",
    "VERI": "Veri yapıları", "NESNE": "Nesne yönelimi", "HATA": "Hata yönetimi", "DOSYA": "Dosya ve konsol",
    "KTIP": "Kütüphane tipleri", "MODUL": "Modül ve ad alanı", "ONISLEM": "Önişlemci (%% yönergeleri)", "META": "Meta sistemi (REM %%)",
    "GOREV": "Görevler ve eşzamanlılık", "DIS": "Dış dünya (DLL, C/C++/ASM, sistem API'si)",
    "KUT": "Standart kütüphaneler (libsx)", "JS": "JS hedefi", "WASM": "WAT/WASM hedefi", "HIZ": "Başarım (hız)",
    "ARAC": "Yardımcı araçlar (uxclazz, uxbdll)", "HEDEF": "Tasarımda olup kodda olmayanlar (◇ HEDEF)",
    "BELGE": "Belge ve örnek projeler",
}
SINIR_TURLERI = {"SESSİZ": "⚠ sessiz", "FARK": "≠ fark", "AÇIK": "◌ açık", "EKSİK": "✖ eksik", "ÇÖKME": "✖ çökme", "YAVAŞ": "◔ yavaş"}
SINIR_KIMLIK = re.compile(r"\bG-([A-ZÇĞİÖŞÜ]+)-(\d+)\b")


def sinirlari_oku():
    """veri/sinirlar.txt: 'KAYIT :: Etkilenen :: Tür :: Ne olur? :: Ne yapmalı?' satırları."""
    p = os.path.join(VERI, "sinirlar.txt")
    kayit = {}
    for s in open(p, encoding="utf-8").read().splitlines():
        if not s.strip() or s.startswith("#"):
            continue
        parca = [x.strip() for x in s.split(" :: ")]
        if len(parca) != 5:
            uyarilar.append(f"SINIR kaydı bozuk (5 alan olmalı): {s[:60]}")
            continue
        kimlik, etkilenen, tur, olur, yap = parca
        if not SINIR_KIMLIK.fullmatch(kimlik):
            uyarilar.append(f"SINIR kimliği geçersiz: {kimlik}")
            continue
        if tur not in SINIR_TURLERI:
            uyarilar.append(f"SINIR türü geçersiz ({kimlik}): {tur}")
        if kimlik in kayit:
            uyarilar.append(f"SINIR kimliği iki kez tanımlı: {kimlik}")
        kayit[kimlik] = (etkilenen, tur, olur, yap)
    return kayit


def sorun_eslemesi_oku():
    """veri/sorun_eslemesi.txt: 'G-CLI-1 = S-322' (sorun_takibe_isle.py yazar); Ek G'de her kaydın yanında SORUN_TAKIP numarası görünür."""
    p = os.path.join(VERI, "sorun_eslemesi.txt")
    e = {}
    if os.path.exists(p):
        for s in open(p, encoding="utf-8").read().splitlines():
            m = re.fullmatch(r"\s*(G-[A-ZÇĞİÖŞÜ]+-\d+)\s*=\s*(S-\d+)\s*", s)
            if m:
                e[m.group(1)] = m.group(2)
    return e


SORUN_TAKIP_YOLU = os.path.join(KOK, "ai_koordinasyon", "SORUN_TAKIP.md")
DURUM_KISA = {"YAPILDI-DOGRULANDI": "✔ kapandı", "YAPILDI": "✔ kapandı", "KISMEN-YAPILDI": "◐ kısmen", "KISMEN-DUZELTILDI": "◐ kısmen",
              "KISMEN-YAPILDI-DOGRULANDI": "◐ kısmen", "KISMI-YAPILDI": "◐ kısmen", "KISMI-DOGRULANDI": "◐ kısmen",
              "ACIK": "açık", "KARAR-BEKLIYOR": "karar bekliyor", "KARAR-VERILDI-POLITIKA-BELGELENDI": "karar verildi",
              "ACIK-TASARIM-KARARI-KAYITLI": "açık (tasarım onaylı)"}


def sorun_durumlari_oku():
    """SORUN_TAKIP.md: her '## S-nnn' kaydının ilk '**Durum:** `X`' değeri (kitabın üretildiği andaki durum)."""
    d = {}
    if os.path.exists(SORUN_TAKIP_YOLU):
        mevcut = None
        for s in open(SORUN_TAKIP_YOLU, encoding="utf-8").read().split("\n"):
            m = re.match(r"^## (S-\d+)\b", s)
            if m:
                mevcut = m.group(1)
                continue
            if mevcut and mevcut not in d:
                m2 = re.search(r"\*\*Durum:\*\*\s*`([^`]+)`", s)
                if m2:
                    d[mevcut] = m2.group(1)
    return d


def sinirlar_tablosu(sadece_alan=None):
    """sadece_alan verilirse (örn. 'CLI') yalnız o alanın tablosu yazılır; verilmezse özet + bütün alanlar."""
    kayit = sinirlari_oku()
    esleme = sorun_eslemesi_oku()
    durumlar = sorun_durumlari_oku()

    def takip_hucresi(kimlik):
        s = esleme.get(kimlik)
        if not s:
            return "—"
        d = durumlar.get(s)
        return f"{s} · {DURUM_KISA.get(d, d)}" if d else s
    for kimlik in kayit:
        if kimlik not in esleme:
            uyarilar.append(f"SINIR kaydı SORUN_TAKIP'a işlenmemiş (sorun_takibe_isle.py çalıştırın): {kimlik}")
    alanlar = {}
    for kimlik, v in kayit.items():
        alan, no = SINIR_KIMLIK.fullmatch(kimlik).groups()
        alanlar.setdefault(alan, []).append((int(no), kimlik, v))
    for alan in alanlar:
        if alan not in SINIR_ALANLARI:
            uyarilar.append(f"SINIR alanı tanımsız: {alan}")
    if sadece_alan and sadece_alan not in alanlar:
        uyarilar.append(f"SINIR alanı yok: {sadece_alan}")
    tur_say = {t: sum(1 for v in kayit.values() if v[1] == t) for t in SINIR_TURLERI}
    sat = []
    if not sadece_alan:
        durum_say = {}
        for kimlik in kayit:
            d = durumlar.get(esleme.get(kimlik, ""))
            durum_say[DURUM_KISA.get(d, d or "—")] = durum_say.get(DURUM_KISA.get(d, d or "—"), 0) + 1
        durum_yazi = ", ".join(f"{ad} **{n}**" for ad, n in sorted(durum_say.items(), key=lambda x: -x[1]))
        sat += [f"Katalogda **{len(kayit)}** kayıt var: " + ", ".join(f"{SINIR_TURLERI[t]} **{n}**" for t, n in tur_say.items()) + ".\n",
                f"SORUN_TAKIP'taki güncel durumlarına göre: {durum_yazi}.\n",
                "| Alan | Kayıt sayısı | " + " | ".join(SINIR_TURLERI.values()) + " |", "|---|---|" + "---|" * len(SINIR_TURLERI)]
        for alan, baslik in SINIR_ALANLARI.items():
            lst = alanlar.get(alan, [])
            if lst:
                sat.append(f"| {baslik} | {len(lst)} | " + " | ".join(str(sum(1 for _, _, v in lst if v[1] == t)) for t in SINIR_TURLERI) + " |")
        sat.append("")
    for alan, baslik in SINIR_ALANLARI.items():
        if sadece_alan and alan != sadece_alan:
            continue
        lst = sorted(alanlar.get(alan, []))
        if not lst:
            continue
        if not sadece_alan:
            sat.append(f"**{baslik}**\n")
        sat.append("| Kayıt | Sorun takip | Etkilenen | Tür | Ne olur? | Ne yapmalı? (geçici yol, sorunu çözmez) |\n|---|---|---|---|---|---|")
        for _, kimlik, (etk, tur, olur, yap) in lst:
            sat.append(f"| {kimlik} | {takip_hucresi(kimlik)} | {etk} | {SINIR_TURLERI.get(tur, tur)} | {olur} | {yap} |")
        sat.append("")
    return "\n".join(sat)


def sinir_tutarliligi(ham_metin):
    """Metinde anılan her G-kaydı katalogda tanımlı olmalı; katalogdaki her kayıt metinde en az bir kez anılmalı."""
    tanimli = set(sinirlari_oku())
    anilan = {f"G-{a}-{n}" for a, n in SINIR_KIMLIK.findall(ham_metin)}
    # {{SINIRLAR:ALAN}} yer tutucusu o alanın bütün kayıtlarını metne getirir; böyle yazılan alan "anılmış" sayılır
    for alan in re.findall(r"\{\{\s*SINIRLAR\s*:\s*([A-ZÇĞİÖŞÜ]+)\s*\}\}", ham_metin):
        anilan |= {k for k in tanimli if k.startswith(f"G-{alan}-")}
    for k in sorted(anilan - tanimli):
        uyarilar.append(f"SINIR metinde anılıyor ama katalogda yok: {k}")
    for k in sorted(tanimli - anilan):
        uyarilar.append(f"SINIR katalogda var ama metinde anılmıyor: {k}")


ONISLEMCI_DURUM = {"OK": "✔ çalışıyor", "KISMI": "◐ kısmi", "KAYIT": "◌ kayıt", "EKSIK": "✖ eksik"}


def onislemci_oku():
    """veri/onislemci.txt: 'AD :: Grup :: Söz dizimi :: Durum :: Ne yapar?'; kaynaktaki kanonik listeyle karşılaştırılır."""
    p = os.path.join(VERI, "onislemci.txt")
    sira, kayit = [], {}
    for s in open(p, encoding="utf-8").read().splitlines():
        if not s.strip() or s.startswith("#"):
            continue
        parca = [x.strip() for x in s.split(" :: ")]
        if len(parca) != 5:
            uyarilar.append(f"ÖNİŞLEMCİ kaydı bozuk (5 alan olmalı): {s[:60]}")
            continue
        ad, grup, soz, durum, aciklama = parca
        taban, _, ek = durum.partition("+")
        if taban not in ONISLEMCI_DURUM or ek not in ("", "B"):
            uyarilar.append(f"ÖNİŞLEMCİ durumu geçersiz ({ad}): {durum}")
        if ad in kayit:
            uyarilar.append(f"ÖNİŞLEMCİ yönergesi iki kez tanımlı: {ad}")
        kayit[ad] = (grup, soz, taban, ek == "B", aciklama)
        sira.append(ad)
    return sira, kayit


def onislemci_kaynak_listesi():
    """src/preprocessor/preprocess_parser.fbs içindeki UXBPreParseIsCanonicalCommand'ın 'Case' adları."""
    p = os.path.join(KOK, "src", "preprocessor", "preprocess_parser.fbs")
    if not os.path.exists(p):
        uyarilar.append("ÖNİŞLEMCİ kaynak listesi bulunamadı: " + p)
        return None
    ad, icerde = [], False
    for s in open(p, encoding="utf-8", errors="replace").read().splitlines():
        if re.match(r"(?i)^\s*Function\s+UXBPreParseIsCanonicalCommand\b.*As\s+Integer\s*$", s) and "Declare" not in s:
            icerde = True
            continue
        if icerde and re.match(r"(?i)^\s*End Function", s):
            break
        if icerde and re.match(r'^\s*Case\s+"', s):
            ad += re.findall(r'"([A-Z0-9_]+)"', s)
    return ad


def onislemci_tutarliligi():
    sira, kayit = onislemci_oku()
    kaynak = onislemci_kaynak_listesi()
    if kaynak is None:
        return
    for a in sorted(set(kaynak) - set(kayit)):
        uyarilar.append(f"ÖNİŞLEMCİ yönergesi kaynakta var, dizinde yok: {a}")
    for a in sorted(set(kayit) - set(kaynak)):
        uyarilar.append(f"ÖNİŞLEMCİ yönergesi dizinde var, kaynakta yok: {a}")


def onislemci_tablosu(sadece_grup=None):
    sira, kayit = onislemci_oku()
    gruplar = {}
    for ad in sira:
        gruplar.setdefault(kayit[ad][0], []).append(ad)
    sat = []
    if not sadece_grup:
        say = {d: sum(1 for a in sira if kayit[a][2] == d) for d in ONISLEMCI_DURUM}
        sat.append(f"Kaynaktaki kanonik liste **{len(sira)}** yönergeden oluşur: " + ", ".join(f"{ONISLEMCI_DURUM[d]} **{n}**" for d, n in say.items())
                   + ". Ortak motorda PP seçicisi yoktur.\n")
        sat.append("| Grup | Yönerge sayısı | " + " | ".join(ONISLEMCI_DURUM.values()) + " |")
        sat.append("|---|---|" + "---|" * len(ONISLEMCI_DURUM))
        for g, lst in gruplar.items():
            sat.append(f"| {g} | {len(lst)} | " + " | ".join(str(sum(1 for a in lst if kayit[a][2] == d)) for d in ONISLEMCI_DURUM) + " |")
        sat.append("")
    for g, lst in gruplar.items():
        if sadece_grup and g != sadece_grup:
            continue
        if not sadece_grup:
            sat.append(f"**{g}** ({len(lst)} yönerge)\n")
        sat.append("| Yönerge | Söz dizimi | Durum | Ne yapar? |\n|---|---|---|---|")
        for a in lst:
            _, soz, d, b, ac = kayit[a]
            sat.append(f"| `%%{a}` | {soz} | {ONISLEMCI_DURUM[d]}{' · B' if b else ''} | {ac} |")
        sat.append("")
    if sadece_grup and sadece_grup not in gruplar:
        uyarilar.append(f"ÖNİŞLEMCİ grubu yok: {sadece_grup}")
    return "\n".join(sat)


MODULLER = os.path.join(KOK, "include", "modules")
ARAC_KOK = os.path.join(os.path.dirname(__file__), "arac_ornekleri")


def kutuphaneler_oku():
    """veri/kutuphaneler.txt: 'başlık :: Kategori :: Dayandığı yazılım :: Ne işe yarar?' (dosya sırası = tablo sırası)."""
    sira, kayit = [], {}
    for s in open(os.path.join(VERI, "kutuphaneler.txt"), encoding="utf-8").read().splitlines():
        if not s.strip() or s.startswith("#"):
            continue
        parca = [x.strip() for x in s.split(" :: ", 3)]
        if len(parca) != 4:
            uyarilar.append(f"KÜTÜPHANE kaydı bozuk (4 alan olmalı): {s[:60]}")
            continue
        ad, kategori, yazilim, aciklama = parca
        if ad in kayit:
            uyarilar.append(f"KÜTÜPHANE iki kez tanımlı: {ad}")
        kayit[ad] = (kategori, yazilim, aciklama)
        sira.append(ad)
    return sira, kayit


def kutuphane_tara():
    """include/modules/*.uxmh dosyalarının gösterdiği .bas dosyalarını okur: ad alanları, işlev adları, sınıf sayısı, DLL adları.
    Sayılar elle yazılmaz; kaynak değişince tablo kendiliğinden değişir."""
    sonuc = {}
    for dosya in sorted(os.listdir(MODULLER)):
        if not dosya.endswith(".uxmh"):
            continue
        ad = dosya[:-5]
        govde = open(os.path.join(MODULLER, dosya), encoding="utf-8", errors="replace").read()
        kayit = {"ns": [], "isimler": [], "dll": [], "sinif": 0}
        for hedef in re.findall(r'INCLUDE\s+"([^"]+)"', govde):
            p = os.path.join(KOK, hedef.replace("/", os.sep))
            if not os.path.exists(p):
                uyarilar.append(f"KÜTÜPHANE hedef dosyası yok: {ad} -> {hedef}")
                continue
            for s in open(p, encoding="utf-8", errors="replace").read().splitlines():
                t = s.strip()
                m = re.match(r"(?i)^NAMESPACE\s+(\w+)", t)
                if m and m.group(1) not in kayit["ns"]:
                    kayit["ns"].append(m.group(1))
                m = re.match(r"(?i)^(?:FUNCTION|SUB)\s+(\w+)", t)
                if m:
                    kayit["isimler"].append(m.group(1))
                if re.match(r"(?i)^CLASS\s+\w+", t):
                    kayit["sinif"] += 1
                for d in re.findall(r'CALL\(DLL,\s*"([^"]+)"', t):
                    if d.lower() not in kayit["dll"]:
                        kayit["dll"].append(d.lower())
        sonuc[ad] = kayit
    return sonuc


def calldll_yogun():
    """libsx modül klasörlerindeki `CALL(DLL, …)` çağrı sayıları (elle yazılmaz): kaç modül kullanıyor, en yoğunları, kullanmayanlar."""
    libsx = os.path.join(KOK, "libsx")
    sayac = {}
    for modul in sorted(os.listdir(libsx)):
        yol = os.path.join(libsx, modul)
        if not os.path.isdir(yol):
            continue
        n = 0
        for dp, _, fn in os.walk(yol):
            for f in fn:
                if f.lower().endswith((".bas", ".bi", ".fbs", ".uxm", ".uxmh")):
                    n += len(re.findall(r"(?i)CALL\s*\(\s*DLL\s*,", open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()))
        sayac[modul] = n
    kullanan = [m for m, n in sayac.items() if n > 0]
    kullanmayan = [m for m, n in sayac.items() if n == 0]
    en = sorted(kullanan, key=lambda m: -sayac[m])[:6]
    yogun = ", ".join(f"`{m}` {sayac[m]}" for m in en)
    return (f"`libsx` altındaki {len(sayac)} modül klasöründen **{len(kullanan)}'i** sarmalayıcı kaynağında `CALL(DLL, …)` kullanır (en yoğunları {yogun}); "
            f"hiç `CALL(DLL)` içermeyen klasör: " + ", ".join(f"`{m}`" for m in kullanmayan))


def kutuphane_oneki(k):
    if k["ns"]:
        return ", ".join(f"`{n}.`" for n in k["ns"])
    if not k["isimler"]:
        return "—"
    ortak = os.path.commonprefix(k["isimler"])
    return f"`{ortak}*`" if len(ortak) >= 2 else "(önek yok)"


def kutuphane_ornekleri(sonuclar):
    """Örnek (.uxb) ve araç örneği (.py) dosyalarındaki INCLUDE'lardan kütüphane -> {dosya: geçti mi} eşlemesi."""
    harita = {"ornek": {}, "arac": {}}
    kalip = re.compile(r'include/modules/([A-Za-z0-9_]+)\.uxmh')
    for dp, dn, fn in os.walk(ORNEK):
        for f in fn:
            if not f.endswith(".uxb") or "_reddedilen" in dp:
                continue
            yol = os.path.join(dp, f)
            rel = os.path.relpath(yol, KOK).replace("\\", "/")
            rec = sonuclar.get(rel)
            for ad in set(kalip.findall(open(yol, encoding="utf-8", errors="replace").read())):
                harita["ornek"].setdefault(ad, {})[rel] = bool(rec and rec.get("hepsi"))
    arac_rec = {}
    if os.path.exists(ARAC_SONUC):
        arac_rec = {r["dosya"]: r for r in json.load(open(ARAC_SONUC, encoding="utf-8"))}
    for dp, dn, fn in os.walk(ARAC_KOK):
        for f in fn:
            if not f.endswith(".py"):
                continue
            yol = os.path.join(dp, f)
            rel = os.path.relpath(yol, KOK).replace("\\", "/")
            for ad in set(kalip.findall(open(yol, encoding="utf-8", errors="replace").read())):
                harita["arac"].setdefault(ad, {})[rel] = bool(arac_rec.get(rel, {}).get("hepsi"))
    return harita


def kutuphane_dll_hucresi(dlller, denetim):
    parca = []
    for d in dlller:
        r = denetim.get(d)
        if r is None:
            parca.append(f"`{d}` (denetlenmedi)")
        elif "yuklenemedi" in r:
            parca.append(f"`{d}` ✖ yüklenemiyor")
        elif r["eksik"]:
            parca.append(f"`{d}` {r['sembol_sayisi'] - len(r['eksik'])}/{r['sembol_sayisi']} (eksik: {', '.join(r['eksik'])})")
        else:
            parca.append(f"`{d}` {r['sembol_sayisi']}/{r['sembol_sayisi']} sembol")
    return "<br>".join(parca) if parca else "—"


def kutuphaneler_tablosu(sadece_kategori, sonuclar):
    sira, kayit = kutuphaneler_oku()
    tara = kutuphane_tara()
    for ad in tara:
        if ad not in kayit:
            uyarilar.append(f"KÜTÜPHANE açıklaması yok: {ad}")
    for ad in kayit:
        if ad not in tara:
            uyarilar.append(f"KÜTÜPHANE açıklaması var, başlık dosyası yok: {ad}")
    denetim = {}
    p = os.path.join(VERI, "dll_denetim.json")
    if os.path.exists(p):
        denetim = json.load(open(p, encoding="utf-8"))
    else:
        uyarilar.append("DLL denetim dosyası yok: python tools/kitap/kilavuz_v2/yoklama/dll_sembol_denetimi.py çalıştırın")
    ornek = kutuphane_ornekleri(sonuclar)
    kategoriler = {}
    for ad in sira:
        if ad in tara:
            kategoriler.setdefault(kayit[ad][0], []).append(ad)
    if sadece_kategori and sadece_kategori not in kategoriler:
        uyarilar.append(f"KÜTÜPHANE kategorisi yok: {sadece_kategori}")
    toplam_islev = sum(len(tara[a]["isimler"]) for a in tara)
    sat = []
    if not sadece_kategori:
        sembol = sum(r["sembol_sayisi"] for r in denetim.values())
        eksik = sum(len(r["eksik"]) for r in denetim.values())
        yuklenmeyen = [d for d, r in denetim.items() if "yuklenemedi" in r]
        orneksiz = [a for a in sira if a in tara and not ornek["ornek"].get(a) and not ornek["arac"].get(a)]
        sat.append(f"Dizinde **{len(tara)}** başlık (`include/modules/*.uxmh`) ve **{toplam_islev}** sarmalayıcı işlev vardır. "
                   f"DLL sembol denetimi: **{len(denetim)}** DLL'de **{sembol}** `CALL(DLL, …)` sembolü sınandı, **{eksik}** tanesi dışa aktarılmamış"
                   + (f"; yüklenemeyen DLL: {', '.join('`' + d + '`' for d in yuklenmeyen)}" if yuklenmeyen else "")
                   + f". Doğrulanmış örneği (örnek ya da araç örneği) olmayan başlık: **{len(orneksiz)}** ({', '.join('`' + a + '`' for a in orneksiz)}).\n")
        sat.append("| Kategori | Başlık sayısı | İşlev sayısı | Doğrulanmış örneği olan |\n|---|---|---|---|")
        for kat, adlar in kategoriler.items():
            sat.append(f"| {kat} | {len(adlar)} | {sum(len(tara[a]['isimler']) for a in adlar)} | "
                       f"{sum(1 for a in adlar if ornek['ornek'].get(a) or ornek['arac'].get(a))} / {len(adlar)} |")
        sat.append("")
    for kat, adlar in kategoriler.items():
        if sadece_kategori and kat != sadece_kategori:
            continue
        if not sadece_kategori:
            sat.append(f"**{kat}** ({len(adlar)} başlık)\n")
        sat.append("| Başlık | Ad alanı ya da önek | İşlev | Dayandığı yazılım · DLL (sembol denetimi) | Ne işe yarar? | Örnek |\n|---|---|---|---|---|---|")
        for ad in adlar:
            k = tara[ad]
            _, yazilim, aciklama = kayit[ad]
            dll_h = kutuphane_dll_hucresi(k["dll"], denetim)
            alt = f"{yazilim}<br>{dll_h}" if yazilim != "—" else dll_h
            isl = str(len(k["isimler"])) + (f" + {k['sinif']} sınıf" if k["sinif"] else "")
            o = ornek["ornek"].get(ad, {})
            a = ornek["arac"].get(ad, {})
            hucre = []
            if o:
                gecen = sum(1 for v in o.values() if v)
                hucre.append(f"{len(o)} örnek " + ("✔" if gecen == len(o) else f"({len(o) - gecen} başarısız ✖)"))
                for rel, v in o.items():
                    if not v:
                        uyarilar.append(f"KÜTÜPHANE örneği beklenen motorlarda geçmedi ya da doğrulanmadı: {rel}")
            if a:
                gecen = sum(1 for v in a.values() if v)
                hucre.append(f"{len(a)} araç " + ("✔" if gecen == len(a) else f"({len(a) - gecen} başarısız ✖)"))
                for rel, v in a.items():
                    if not v:
                        uyarilar.append(f"KÜTÜPHANE araç örneği geçmedi ya da doğrulanmadı: {rel}")
            sat.append(f"| `{ad}` | {kutuphane_oneki(k)} | {isl} | {alt} | {aciklama} | {'<br>'.join(hucre) if hucre else 'sınanmadı'} |")
        sat.append("")
    return "\n".join(sat)


def surum_bilgisi():
    if os.path.exists(EXE):
        h = hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()
        return f"`{os.path.relpath(EXE, KOK)}` (SHA256 `{h[:16]}…`)"
    return "derleyici dosyası bulunamadı"


KARAR_VERISI = []  # [(bölüm_no, bölüm_adı, alt_bölüm_no, [madde, ...])] -- kararlari_topla() doldurur
BOLUM_ADI_YEDEK = {0: "Başlarken"}


def kararlari_topla(sablonlar):
    """Her bölüm şablonundaki '## N.k ... programlama kararları' bölümünün '* ' maddelerini toplar.
    Maddeler yalnız bölümlerde yazılır (tek kaynak); 23. bölüm bunları otomatik birleştirir, böylece iki yerde ayrışmazlar."""
    veri = []
    for dosya, metin in sablonlar:
        try:
            no = int(dosya.split("_", 1)[0])
        except ValueError:
            continue
        bolum_adi = BOLUM_ADI_YEDEK.get(no, "")
        for s in metin.split("\n"):
            m = re.match(r"^#\s+(\d+)\.\s+(.+?)\s*$", s)
            if m:
                bolum_adi = m.group(2)
                break
        maddeler, acik, alt = [], False, ""
        for s in metin.split("\n"):
            m = re.match(r"^##\s+(\d+)\.(\d+)\s+(.+?)\s*$", s)
            if m:
                acik = "kararları" in m.group(3) and int(m.group(1)) == no
                if acik:
                    alt = f"{m.group(1)}.{m.group(2)}"
                continue
            if s.startswith("#"):
                acik = False
                continue
            if not acik:
                continue
            if s.startswith("* ") or s.startswith("- "):
                # 2026-10-17: 02_derleme_cli.md bir biçimlendirici tarafından «- » madde imine çevrilmişti (karar bölümü yok sayılıyordu);
                # iki imi de kabul etmek, şablonu yeniden biçimlendirmeye karşı dayanıklı kılar.
                maddeler.append(s[2:].strip())
            elif s.startswith("  ") and s.strip() and maddeler:
                maddeler[-1] += " " + s.strip()
        if maddeler:
            veri.append((no, bolum_adi, alt, maddeler))
        elif no <= 22 and not dosya.startswith("23_"):
            uyarilar.append(f"KARAR BÖLÜMÜ YOK: {dosya} ('## N.k … programlama kararları' başlığı ve '* ' maddeleri gerekir)")
    return veri


def kararlar_ozeti():
    sat = ["| Bölüm | Konu | Karar sayısı | Maddelerin yazıldığı yer |", "|---|---|---|---|"]
    toplam = 0
    for no, ad, alt, maddeler in KARAR_VERISI:
        sat.append(f"| {no} | {ad} | {len(maddeler)} | {alt} |")
        toplam += len(maddeler)
    sat.append(f"| | **Toplam** | **{toplam}** | |")
    return "\n".join(sat)


def kararlar_metni():
    cikti = []
    for no, ad, alt, maddeler in KARAR_VERISI:
        cikti.append(f"### Bölüm {no}: {ad} ({alt})")
        cikti.append("")
        for i, madde in enumerate(maddeler, 1):
            cikti.append(f"* **K{no}.{i}** — {madde}")
        cikti.append("")
    return "\n".join(cikti).rstrip()


SOZCUK_GRUPLARI = [  # (grubu tanıtan sözcük, grup adı, anlatıldığı bölüm)
    ("if", "Koşul ve seçim", "7"), ("try", "Hata yönetimi", "12"), ("event", "Olay ve görev yapıları", "15"),
    ("spawn", "Görev başlatma", "15"), ("for", "Döngü ve akış", "7"), ("sub", "Yordam", "8"),
    ("type", "Tip, nesne ve bildirim", "5, 10, 11, 16, 19"), ("public", "Erişim ve değişebilirlik", "11"),
    ("main", "Program, modül ve ad alanı", "3, 16"), ("defint", "Varsayılan tip (DEF…)", "5"),
    ("print", "Dosya ve konsol", "13"), ("cls", "Ekran", "13"), ("and", "Mantık ve bit işleci sözcükleri", "6"),
    ("inline", "INLINE ve SHELL seçenekleri", "13, 16"), ("i8", "Tip adları ve sabit sözcükleri", "4"),
    ("task", "Görev tipleri", "15"), ("array", "Koleksiyon tipleri", "10"),
    ("setstringsize", "Yerleşik işlev ve deyim adları", "9, 13, 14"), ("cint", "Dönüşüm ve rastgele", "4, 9"),
    ("peek", "Bellek", "14"),
]


def anahtar_sozcukler_tablosu():
    """Lexer anahtar sözcük tablosunu (src/parser/lexer/lexer_keyword_table.fbs) gruplar halinde yazar; tasarım sözcükleriyle karşılaştırır."""
    yol = os.path.join(KOK, "src", "parser", "lexer", "lexer_keyword_table.fbs")
    if not os.path.exists(yol):
        uyarilar.append("ANAHTAR SÖZCÜK tablosu bulunamadı: " + yol)
        return "(anahtar sözcük tablosu bulunamadı)"
    metin = open(yol, encoding="utf-8").read()
    gruplar = []
    for m in re.finditer(r"^\s*Case ((?:\"[a-z0-9_]+\"\s*,?\s*)+)\s*$", metin, re.M):
        gruplar.append(re.findall(r"\"([a-z0-9_]+)\"", m.group(1)))
    tum = set()
    for g in gruplar:
        tum |= {s.upper() for s in g}
    sat = [f"Derleyicinin sözcük çözümleyicisi (`lexer_keyword_table.fbs`) **{len(tum)}** benzersiz anahtar sözcük tanır. "
           "Bir sözcüğün anahtar sözcük olması onun bugün **çalıştığı** anlamına gelmez (`MIXIN`, `ABSTRACT` gibi sözcükler tanınır ama ayrıştırıcıda işlenmez, G-NESNE-6).\n",
           "| Grup | Sözcükler | Anlatıldığı bölüm |", "|---|---|---|"]
    kullanilan = set()
    for g in gruplar:
        ad, bolum = "Diğer", "—"
        for imza, grup_adi, grup_bolum in SOZCUK_GRUPLARI:
            if imza in g:
                ad, bolum = grup_adi, grup_bolum
                break
        if ad == "Diğer":
            uyarilar.append("ANAHTAR SÖZCÜK grubu adlandırılamadı: " + ", ".join(g[:4]))
        sozcukler = [s.upper() for s in g if s.upper() not in kullanilan]
        kullanilan |= set(sozcukler)
        if sozcukler:
            sat.append(f"| {ad} | " + " ".join(f"`{s}`" for s in sozcukler) + f" | {bolum} |")
    # tasarım belgesindeki (18.09) sözcüklerle karşılaştırma
    tasarim_yolu = os.path.join(KOK, "docs", "tasarim", "uXBasic_18_09_JS_WASM_Tam_Yuzey_Matrisi.md")
    if os.path.exists(tasarim_yolu):
        mat = open(tasarim_yolu, encoding="utf-8").read()
        if "## 3. Anahtar sözcük yüzeyi" in mat:
            bolum_metni = mat.split("## 3. Anahtar sözcük yüzeyi")[1].split("## 4. Operatör")[0]
            tas = set()
            for satir in bolum_metni.splitlines():
                if satir.startswith("|") and "---" not in satir and "Grup" not in satir:
                    hucre = satir.split("|")[2] if satir.count("|") >= 3 else ""
                    tas |= {k.upper() for k in re.findall(r"`([A-Za-z0-9_]+)`", hucre)}
            eksik = sorted(tas - tum)
            fazla = sorted(tum - tas)
            sat.append("")
            sat.append(f"**Tasarımla karşılaştırma.** Tasarım belgesindeki (18.09 yüzey matrisi) {len(tas)} anahtar sözcüğün "
                       + (f"**{len(tas) - len(eksik)}** tanesi sözlükte vardır" if eksik else "**tamamı** sözlükte vardır")
                       + (f"; sözlükte olmayanlar: {', '.join('`' + e + '`' for e in eksik)}" if eksik else "")
                       + (f". Sözlükte tasarım listesinden **fazla** olanlar: {', '.join('`' + f + '`' for f in fazla)}." if fazla else "."))
    sat.append("")
    sat.append("**Bağlamsal sözcükler.** Aşağıdakiler sözlükte olmasa da ayrıştırıcıda tanınır ve çalışır: `LOCK … END LOCK`, `MUTEX`, `ATOMIC`, `UNSAFE … END UNSAFE`, `TASK OF tip` içindeki `OF`, görev üyeleri (`WAIT`, `JOIN`, `CANCEL`, `RESULT`, `STATUS`, `ERRORTEXT`, `ADD`) "
               "ve `TASKOUT`. Yüzey kaydı bu sözcükleri henüz kapsamaz (S-196).")
    return "\n".join(sat)


def yerlesik_islevler_tablosu():
    """veri/yerlesik_islevler.csv (uxb sem --type-infer-report-csv-out) + veri/islev_aciklamalari.txt -> Ek B tablosu."""
    csv_yolu = os.path.join(VERI, "yerlesik_islevler.csv")
    aciklamalar = {}
    ap = os.path.join(VERI, "islev_aciklamalari.txt")
    for s in open(ap, encoding="utf-8").read().splitlines():
        if s.strip() and not s.startswith("#"):
            p = [x.strip() for x in s.split(" :: ")]
            if len(p) == 3:
                aciklamalar[p[0].upper()] = (p[1], p[2])
    ARG = {"STRING": "metin", "WSTRING": "geniş metin", "INT": "tamsayı", "NUMERIC": "sayı", "ANY": "herhangi", "PTR": "işaretçi", "LIST": "liste",
           "DICT": "sözlük", "SET": "küme", "TYPE": "tip", "IDENT": "değişken adı", "VALUE": "değer", "ARRAY": "dizi", "NOARGS": "argümansız",
           "OPTIONAL_SEED": "[tohum]", "OPTIONAL_PROMPT": "[istem]", "BIG_EXTERNAL_INIT": "tür, metin, duyarlık", "EXTFP_CONSTRUCT": "metin"}
    HEDEF = {"ALL": "tüm hedefler", "CONSOLE_RUNTIME": "konsol çalışma zamanı", "NATIVE_RUNTIME": "yerel", "EXTFP_RUNTIME": "geniş sayı çalışma zamanı"}
    satirlar = open(csv_yolu, encoding="utf-8").read().splitlines()[1:]
    import csv as _csv
    sat = ["| İşlev | Argüman | Döner | Hedef | Bölüm | Ne yapar? |", "|---|---|---|---|---|---|"]
    gorulen = set()
    for r in _csv.reader(satirlar):
        ad, don, arg, hedef = r[0], r[1], r[2], r[3]
        gorulen.add(ad.upper())
        arg_metni = arg
        for k, v in ARG.items():
            arg_metni = re.sub(r"\b" + k + r"\b", v, arg_metni)
        arg_metni = arg_metni.replace(":1", " (1)")
        ac = aciklamalar.get(ad.upper())
        if not ac:
            uyarilar.append(f"YERLEŞİK İŞLEV açıklaması yok: {ad}")
            ac = ("—", "")
        sat.append(f"| `{ad}` | {arg_metni} | `{don.replace('TYPE_', '')}` | {HEDEF.get(hedef, hedef)} | {ac[0]} | {ac[1]} |")
    for ad in sorted(set(aciklamalar) - gorulen):
        uyarilar.append(f"YERLEŞİK İŞLEV açıklaması var ama kayıtta yok: {ad}")
    return "\n".join(sat)


def onislemci_dizini():
    """Ek C: bütün yönergeler alfabetik; ayrıntı Bölüm 17'dedir."""
    sira, kayit = onislemci_oku()
    sat = [f"Kaynaktaki kanonik liste **{len(sira)}** yönergeden oluşur; her yönergenin gruplu anlatımı ve örnekleri Bölüm 17'dedir. "
           "Bu dizin yalnızca **alfabetik arama** içindir.\n",
           "| Yönerge | Grup | Söz dizimi | Durum |", "|---|---|---|---|"]
    for ad in sorted(sira):
        grup, soz, taban, b, _ac = kayit[ad]
        sat.append(f"| `%%{ad}` | {grup} | {soz} | {ONISLEMCI_DURUM[taban]} |")
    return "\n".join(sat)


YER_TUTUCULAR = {"ORNEK", "ORNEKKOD", "ARAC", "CLI_SECENEKLER", "ESLIK_OZETI", "ESLIK_TOPLAM", "SINIRLAR", "ONISLEMCI", "KUTUPHANELER", "SURUM", "KARARLAR",
                 "ANAHTAR_SOZCUKLER", "YERLESIK_ISLEVLER", "ONISLEMCI_DIZINI", "CALLDLL_YOGUN"}


def isle(metin, sonuclar):
    def degistir(m):
        ad, ayrac, arg = m.group(1).partition(":")
        ad = ad.strip()
        if ad not in YER_TUTUCULAR:
            # {{AD}}, {{K}}, {{INDEX}} gibi önişlemci döngü değişkenleri kılavuz metninde olduğu gibi yazılır; yalnız
            # "AD:bir şey" biçimindeki (üretici söz dizimine benzeyen) bilinmeyen yer tutucu uyarı üretir.
            if ayrac:
                uyarilar.append(f"BİLİNMEYEN YER TUTUCU: {m.group(0)}")
            return m.group(0)
        kisim = arg.split("|")
        ref = kisim[0].strip()
        secenek = {}
        for k in kisim[1:]:
            if "=" in k:
                a, b = k.split("=", 1)
                secenek[a.strip()] = b.strip()
        if ad == "ORNEK":
            return ornek_yer_tutucu(ref, secenek, sonuclar)
        if ad == "ORNEKKOD":
            return ornek_yer_tutucu(ref, secenek, sonuclar, sadece_kod=True)
        if ad == "ARAC":
            return arac_yer_tutucu(ref, secenek)
        if ad == "CLI_SECENEKLER":
            return cli_secenekleri()
        if ad == "ESLIK_OZETI":
            return esdegerlik_ozeti(sonuclar)
        if ad == "ESLIK_TOPLAM":
            return esdegerlik_toplami(sonuclar)
        if ad == "SINIRLAR":
            return sinirlar_tablosu(ref or None)
        if ad == "ONISLEMCI":
            return onislemci_tablosu(ref or None)
        if ad == "KUTUPHANELER":
            return kutuphaneler_tablosu(ref or None, sonuclar)
        if ad == "SURUM":
            return surum_bilgisi()
        if ad == "KARARLAR":
            return kararlar_ozeti() if ref.upper() == "OZET" else kararlar_metni()
        if ad == "ANAHTAR_SOZCUKLER":
            return anahtar_sozcukler_tablosu()
        if ad == "YERLESIK_ISLEVLER":
            return yerlesik_islevler_tablosu()
        if ad == "ONISLEMCI_DIZINI":
            return onislemci_dizini()
        if ad == "CALLDLL_YOGUN":
            return calldll_yogun()
        return m.group(0)

    return re.sub(r"\{\{\s*([A-Z_]+(?::[^}]*)?)\s*\}\}", degistir, metin)


def main():
    global YARDIM
    ap = argparse.ArgumentParser()
    ap.add_argument("--sert", action="store_true", help="uyarı varsa çıkış kodu 1")
    ap.add_argument("--yardim", default=os.path.join(VERI, "cli_help.txt"))
    ap.add_argument("--cikti", default=CIKTI)
    a = ap.parse_args()
    YARDIM = a.yardim
    sonuclar = sonuclari_yukle()
    parcalar, ham = [], []
    dosyalar = sorted(f for f in os.listdir(SABLON) if f.endswith(".md"))
    sablonlar = [(f, open(os.path.join(SABLON, f), encoding="utf-8").read().rstrip() + "\n") for f in dosyalar]
    KARAR_VERISI[:] = kararlari_topla(sablonlar)
    for f, metin in sablonlar:
        ham.append(metin)
        parcalar.append(isle(metin, sonuclar))
    sinir_tutarliligi("\n".join(ham) + "\n" + "\n".join(anlatilan))
    onislemci_tutarliligi()
    govde = "\n\n".join(parcalar)
    bugun = datetime.date.today().isoformat()
    govde = govde.replace("@@TARIH@@", bugun)
    os.makedirs(os.path.dirname(a.cikti), exist_ok=True)
    open(a.cikti, "w", encoding="utf-8", newline="\n").write(govde)
    uyarilar[:] = list(dict.fromkeys(uyarilar))  # aynı örnek birden çok bölümde geçince uyarı yinelenmesin
    gecen = sum(1 for r in kullanilan.values() if r and all(r["motor"].get(m, {}).get("durum") == "GECTI" for m in ("AST", "MIR", "x64")))
    # Bir örnek başlığında "' MOTORLAR:" ile alt küme bildirmişse (örn. yalnız AST) beklenen motorlar yalnız onlardır.
    beklenen_gecen = sum(1 for r in kullanilan.values()
                         if r and all(r["motor"].get(m, {}).get("durum") == "GECTI" for m in r.get("motorlar", ["AST", "MIR", "x64"])))
    rapor = {"tarih": bugun, "bolum_dosyasi": len(dosyalar), "satir": govde.count("\n"), "karakter": len(govde),
             "ornek_sayisi": len(kullanilan), "uc_motorda_gecen": gecen, "beklenen_motorlarda_gecen": beklenen_gecen, "uyarilar": uyarilar}
    json.dump(rapor, open(RAPOR, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Yazıldı: {a.cikti}")
    print(f"bölüm dosyası: {len(dosyalar)} · satır: {rapor['satir']} · örnek: {len(kullanilan)} · "
          f"beklenen motorlarda geçen: {beklenen_gecen}/{len(kullanilan)} · AST+MIR+x64'ün üçünde geçen: {gecen}")
    for u in uyarilar:
        print("  UYARI:", u)
    if a.sert and uyarilar:
        sys.exit(1)


if __name__ == "__main__":
    main()
