# -*- coding: utf-8 -*-
"""Kılavuz V2 sınır kataloğunu (veri/sinirlar.txt) ai_koordinasyon/SORUN_TAKIP.md'ye işler.

Her katalog kaydı (G-xxx-n) için SORUN_TAKIP'ta AYRI bir S-numaralı kayıt açar; böylece her kusur sırayla ve tek tek
düzeltilebilir. Eşleme veri/sorun_eslemesi.txt dosyasında tutulur ('G-CLI-1 = S-205'); eşlemesi olan kayıt yeniden yazılmaz,
bu yüzden betik katalog büyüdükçe yeniden çalıştırılabilir (yalnız yeni kayıtlar eklenir).

Yan çıktı: ai_koordinasyon/KILAVUZ_V2_SORUN_DIZINI.md (önerilen düzeltme sırasına göre dizin; her çalıştırmada yeniden yazılır).

Kullanım:
  python tools/kitap/kilavuz_v2/sorun_takibe_isle.py --dene      # ne yapılacağını yazar, dosyaya dokunmaz
  python tools/kitap/kilavuz_v2/sorun_takibe_isle.py             # yazar
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VERI = os.path.join(os.path.dirname(__file__), "veri")
SINIRLAR = os.path.join(VERI, "sinirlar.txt")
ESLEME = os.path.join(VERI, "sorun_eslemesi.txt")
TAKIP = os.path.join(KOK, "ai_koordinasyon", "SORUN_TAKIP.md")
DIZIN = os.path.join(KOK, "ai_koordinasyon", "KILAVUZ_V2_SORUN_DIZINI.md")

# Önerilen düzeltme sırası: önce ilkeyi çiğneyen (yanlış sonuç), sonra çökme, motorlar arası ayrışma, açık ret, eksik özellik, yavaşlık.
TUR_SIRASI = ["SESSİZ", "ÇÖKME", "FARK", "AÇIK", "EKSİK", "YAVAŞ"]
TUR_ACIKLAMA = {
    "SESSİZ": "yanlış sonuç ya da hatasız kabul (İlke 2'yi çiğner)",
    "ÇÖKME": "tanımsız davranış (yığın bozulması, erişim ihlali)",
    "FARK": "motorlar farklı davranır (İlke 1'i çiğner)",
    "AÇIK": "açık hata verir ama istenen davranış bu değildir",
    "EKSİK": "tasarımda olan özellik kodda yok",
    "YAVAŞ": "doğru çalışır ama kullanılabilirliği sınırlayacak kadar yavaştır",
}
TUR_HEDEF = {
    "SESSİZ": "Hata sessiz geçmez (İlke 2): ya doğru sonuç ya da anlaşılır açık ret.",
    "ÇÖKME": "Tanımsız davranış olmaz: yığın bozulması/erişim ihlali yerine açık, anlaşılır hata.",
    "FARK": "Motorlar aynı gözlenebilir sonucu verir (İlke 1); doğru davranış, kayıttaki doğru motorun (ya da tasarım belgesinin) gösterdiğidir.",
    "AÇIK": "Özellik tasarıma uygun çalışır; çalışması öngörülmüyorsa nedenini doğru söyleyen bir ret iletisi verilir.",
    "EKSİK": "Tasarım belgelerindeki özellik uygulanır (kılavuzda ◇ HEDEF olarak anılır); uygulanana dek açık ret.",
    "YAVAŞ": "Ölçülebilir iyileştirme; ölçüm değerleri kayıtta yazılıdır, düzeltme sonrası aynı ölçüm tekrarlanır.",
}
VARSAYILAN_TARIH = "2026-10-11"  # ilk toplu işleme (169 kayıt) 2026-10-07/08 gözlemlerini taşır; sonradan eklenenler bulundukları gün yazılır
BULUNDU = {  # sonradan bulunanlar
    "G-KOLEKSIYON-2": "2026-10-11", "G-KOLEKSIYON-3": "2026-10-11", "G-KOLEKSIYON-4": "2026-10-11", "G-KOLEKSIYON-5": "2026-10-11",
    "G-NESNE-10": "2026-10-11", "G-NESNE-11": "2026-10-11", "G-NESNE-12": "2026-10-11", "G-NESNE-13": "2026-10-11", "G-GOREV-12": "2026-10-11", "G-VERI-9": "2026-10-11", "G-JS-12": "2026-10-11",
    # 2026-10-12 oturumu: 20.09/23.09 bellek ve kütüphane tipi belgelerinin taranması, WASM/geniş tip/işleç fark taraması
    "G-ISLEC-3": "2026-10-12", "G-ISLEC-4": "2026-10-12", "G-ISLEC-5": "2026-10-12", "G-TIP-10": "2026-10-12", "G-TIP-11": "2026-10-12", "G-TIP-12": "2026-10-12",
    "G-WASM-12": "2026-10-12", "G-WASM-13": "2026-10-12", "G-WASM-14": "2026-10-12", "G-WASM-15": "2026-10-12", "G-WASM-16": "2026-10-12", "G-WASM-17": "2026-10-12",
    "G-WASM-18": "2026-10-12", "G-WASM-19": "2026-10-12", "G-WASM-20": "2026-10-12", "G-HEDEF-21": "2026-10-12",
    "G-HATA-5": "2026-10-12", "G-HATA-6": "2026-10-12", "G-HATA-7": "2026-10-12", "G-HATA-8": "2026-10-12", "G-HATA-9": "2026-10-12",
    "G-YORDAM-6": "2026-10-12", "G-TIP-13": "2026-10-12", "G-JS-14": "2026-10-12", "G-DIS-11": "2026-10-12", "G-DIL-12": "2026-10-12", "G-VERI-11": "2026-10-12", "G-NESNE-21": "2026-10-12", "G-DOSYA-5": "2026-10-12", "G-NESNE-20": "2026-10-12", "G-ISLEC-6": "2026-10-12", "G-METIN-5": "2026-10-12",
    "G-CLI-10": "2026-10-12", "G-CLI-11": "2026-10-12", "G-CLI-12": "2026-10-12", "G-CLI-13": "2026-10-12", "G-CLI-14": "2026-10-12", "G-CLI-15": "2026-10-12",
    "G-CLI-16": "2026-10-12", "G-CLI-17": "2026-10-12", "G-CLI-18": "2026-10-12", "G-CLI-19": "2026-10-12", "G-CLI-20": "2026-10-12", "G-HATA-10": "2026-10-12",
    "G-DIL-13": "2026-10-12", "G-DIL-14": "2026-10-12", "G-CLI-21": "2026-10-12",
    "G-CLI-22": "2026-10-12", "G-CLI-23": "2026-10-12", "G-CLI-24": "2026-10-12", "G-CLI-25": "2026-10-12", "G-CLI-26": "2026-10-12", "G-CLI-27": "2026-10-12", "G-CLI-28": "2026-10-12",
    "G-CLI-29": "2026-10-12", "G-CLI-30": "2026-10-12", "G-CLI-31": "2026-10-12",
    "G-NESNE-22": "2026-10-12", "G-NESNE-23": "2026-10-12", "G-KTIP-6": "2026-10-12", "G-HEDEF-22": "2026-10-12",
    "G-CLI-32": "2026-10-12", "G-CLI-33": "2026-10-12", "G-BELGE-1": "2026-10-12",
    # 2026-10-13 oturumu: yeni ikili (20261013) ile yeniden ölçüm, WASM metin tasarım önerisi
    "G-HEDEF-23": "2026-10-13", "G-HEDEF-24": "2026-10-13", "G-TIP-14": "2026-10-13", "G-DIL-15": "2026-10-13", "G-VERI-12": "2026-10-13",
    "G-NESNE-24": "2026-10-13", "G-NESNE-25": "2026-10-13", "G-NESNE-26": "2026-10-13", "G-NESNE-27": "2026-10-13", "G-NESNE-28": "2026-10-13",
    "G-HEDEF-25": "2026-10-13", "G-KUT-23": "2026-10-13", "G-HEDEF-26": "2026-10-13", "G-DIS-12": "2026-10-13", "G-HEDEF-27": "2026-10-13", "G-ARAC-5": "2026-10-13", "G-DOSYA-6": "2026-10-13", "G-HEDEF-28": "2026-10-13", "G-HEDEF-29": "2026-10-13", "G-ISLEC-7": "2026-10-13",
    "G-HATA-11": "2026-10-13", "G-HATA-12": "2026-10-13", "G-HATA-13": "2026-10-13", "G-KTIP-7": "2026-10-13",
    "G-TIP-15": "2026-10-13", "G-TIP-16": "2026-10-13", "G-ISLEC-8": "2026-10-13", "G-ISLEC-9": "2026-10-13", "G-TIP-17": "2026-10-13", "G-KTIP-8": "2026-10-13", "G-TIP-18": "2026-10-13", "G-TIP-19": "2026-10-13", "G-TIP-20": "2026-10-14", "G-TIP-21": "2026-10-14", "G-TIP-22": "2026-10-14", "G-WASM-21": "2026-10-14", "G-WASM-22": "2026-10-14", "G-TIP-23": "2026-10-14", "G-TIP-24": "2026-10-14", "G-TIP-25": "2026-10-14", "G-TIP-26": "2026-10-14", "G-TIP-27": "2026-10-14", "G-ISLEC-10": "2026-10-14", "G-HEDEF-30": "2026-10-14", "G-NESNE-29": "2026-10-14", "G-DIL-16": "2026-10-14",
    # 2026-10-14 öğleden sonra: eski AST-x64 ölçümü, model testleri (AST gerilemeleri), GOSUB/RETURN
    "G-ISLEC-11": "2026-10-14", "G-ISLEC-12": "2026-10-14", "G-ISLEC-13": "2026-10-14", "G-TIP-28": "2026-10-14", "G-YORDAM-7": "2026-10-14", "G-METIN-6": "2026-10-14", "G-VERI-13": "2026-10-14", "G-AKIS-3": "2026-10-14", "G-MODUL-5": "2026-10-14", "G-HATA-14": "2026-10-14", "G-DOSYA-7": "2026-10-14", "G-DOSYA-8": "2026-10-14", "G-AKIS-4": "2026-10-14", "G-AKIS-5": "2026-10-14", "G-MODUL-6": "2026-10-14", "G-DIL-17": "2026-10-14", "G-DIS-13": "2026-10-14", "G-MODUL-7": "2026-10-14",
    "G-ARAC-6": "2026-10-14",
    "G-YORDAM-8": "2026-10-14",
    "G-YORDAM-9": "2026-10-15",
    "G-WASM-23": "2026-10-15",
    "G-DOSYA-9": "2026-10-15",
    "G-DOSYA-10": "2026-10-15",
    "G-VERI-14": "2026-10-15",
    "G-VERI-15": "2026-10-15",
    "G-VERI-16": "2026-10-15",
    "G-VERI-17": "2026-10-15",
    "G-TIP-29": "2026-10-15",
    "G-TIP-30": "2026-10-15",
    "G-NESNE-30": "2026-10-15",
    "G-NESNE-31": "2026-10-15",
    "G-NESNE-32": "2026-10-15",
    "G-NESNE-33": "2026-10-15",
    "G-NESNE-34": "2026-10-15",
    "G-NESNE-35": "2026-10-15",
    "G-NESNE-36": "2026-10-15",
    "G-YORDAM-10": "2026-10-15",
    "G-DIL-18": "2026-10-15",
    "G-WASM-24": "2026-10-15",
    "G-TIP-31": "2026-10-15",
    "G-AKIS-6": "2026-10-15",
    "G-AKIS-7": "2026-10-15",
    "G-WASM-25": "2026-10-15",
    "G-VERI-18": "2026-10-15",
    "G-KOLEKSIYON-7": "2026-10-15",
}
DENENEN_VARSAYILAN = "bin\\uxb_kilavuz_20261007.exe"
DENENEN = {  # kaydın bulunduğu ikili, varsayılandan farklıysa
    "G-HEDEF-23": "bin\\uxb_kilavuz_20261013.exe", "G-HEDEF-24": "bin\\uxb_kilavuz_20261013.exe",
    "G-HATA-11": "bin\\uxb_kilavuz_20261013_1704.exe (20261007'de aynı)", "G-HATA-12": "bin\\uxb_kilavuz_20261013_1704.exe",
    "G-HATA-13": "bin\\uxb_kilavuz_20261013_1704.exe", "G-TIP-15": "bin\\uxb_kilavuz_20261013_1704.exe (20261007 ile karşılaştırıldı)",
    "G-TIP-16": "bin\\uxb_kilavuz_20261013_1704.exe (20261007'de aynı)", "G-ISLEC-8": "bin\\uxb_kilavuz_20261013_1704.exe (1808'de aynı; 1614 ve öncesi doğru)",
    "G-ISLEC-9": "bin\\uxb_kilavuz_20261007.exe (1704'te ondalık durum aynı)", "G-TIP-17": "bin\\uxb_kilavuz_20261013_1704.exe (20261007 ile karşılaştırıldı)", "G-KTIP-8": "bin\\uxb_kilavuz_20261013_1704.exe (20261007'de derleme kapısında reddedilirdi)", "G-KTIP-7":"bin\\uxb_kilavuz_20261013_1704.exe (1341, 1514, 1614'te aynı; 20261007 ve 12:37 derlemesi reddederdi)",
    "G-TIP-19": "bin\\uxb_kilavuz_20261013_2333.exe (20261013_2306'da doğruydu)",
    "G-TIP-20": "bin\\uxb_kilavuz_20261013_2333.exe (20261007, 1704 ve 2224 ile karşılaştırıldı; MIR hep aynı)", "G-TIP-21": "bin\\uxb_kilavuz_20261013_2333.exe (20261007 ile aynı)", "G-TIP-22": "bin\\uxb_kilavuz_20261013_2333.exe (20261007 ve 2224 ile aynı)", "G-WASM-21": "bin\\uxb_kilavuz_20261014_0253.exe (U8 için 20261007 ve 2224 ile aynı)", "G-WASM-22": "bin\\uxb_kilavuz_20261014_0253.exe (U8 için 20261007 ve 2224 ile aynı)",
    "G-TIP-23": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ve 2224 ile karşılaştırıldı; MIR hep aynı)", "G-TIP-24": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ile aynı)", "G-TIP-25": "bin\\uxb_kilavuz_20261014_0253.exe (MIR-x64 ve JS 20261007 ve 2224 ile aynı)", "G-TIP-26": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ve 2224 ile aynı)", "G-TIP-27": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ve 2224 ile aynı)", "G-ISLEC-10": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ve 2224 ile aynı)", "G-DIL-16": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ile karşılaştırıldı)", "G-NESNE-29": "bin\\uxb_kilavuz_20261014_0253.exe (20261013 12:37 ve sonrası; 20261007'de doğruydu)",
    "G-ISLEC-11": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007, 20261013, 1341, 1704, 2052, 2224 ve 2333 ile aynı)", "G-ISLEC-12": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-ISLEC-13": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-TIP-28": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-YORDAM-7": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-METIN-6": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-VERI-13": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-AKIS-3": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-MODUL-5": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-HATA-14": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-DOSYA-7": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-DOSYA-8": "bin\\uxb_kilavuz_20261014_0253.exe (eski AST-x64; 20261007 ile aynı)", "G-MODUL-6": "bin\\uxb_kilavuz_20261014_0253.exe (20261013 12:37 ve sonrası; 20261007'de doğruydu)", "G-DIL-17": "bin\\uxb_kilavuz_20261014_0253.exe (20261013 12:37 ve sonrası; 20261007'de doğruydu)", "G-DIS-13": "bin\\uxb_kilavuz_20261014_0253.exe (20261013 12:37 ve sonrası; 20261007'de doğruydu)", "G-AKIS-4": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ile aynı)", "G-AKIS-5": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ile aynı)", "G-MODUL-7": "bin\\uxb_kilavuz_20261014_0253.exe (20261007 ile aynı)",
    "G-ARAC-6": "bin\\uxb_kilavuz_20261014_0253.exe (tests\\run_all_model_tests.ps1, 46 paket)",
    "G-YORDAM-8": "bin\\uxb_kilavuz_20261014_0253.exe (20261013_2333 ve öncesinde Aborting : stack overflow, çıkış 4)",
    "G-YORDAM-9": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-WASM-23": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-DOSYA-9": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-DOSYA-10": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-VERI-14": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-VERI-15": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-VERI-16": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-VERI-17": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-TIP-29": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-TIP-30": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-30": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-31": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-32": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-33": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-34": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-35": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-NESNE-36": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-YORDAM-10": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-DIL-18": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-WASM-24": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-TIP-31": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; soru partisi 2026-10-15)",
    "G-AKIS-6": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; karar turu yoklaması 2026-10-15)",
    "G-AKIS-7": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; karar turu yoklaması 2026-10-15)",
    "G-WASM-25": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; karar turu yoklaması 2026-10-15)",
    "G-VERI-18": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; karar turu yoklaması 2026-10-15)",
    "G-KOLEKSIYON-7": "bin\\uxb_kilavuz_20261014_0253.exe (altı yol; karar turu yoklaması 2026-10-15)",
}
KIMLIK = re.compile(r"G-([A-ZÇĞİÖŞÜ]+)-(\d+)")


def katalog_oku():
    kayit = {}
    sira = []
    for s in open(SINIRLAR, encoding="utf-8").read().splitlines():
        if not s.strip() or s.startswith("#"):
            continue
        p = [x.strip() for x in s.split(" :: ")]
        if len(p) != 5 or not KIMLIK.fullmatch(p[0]):
            print("UYARI: bozuk katalog satırı atlandı:", s[:70])
            continue
        kayit[p[0]] = tuple(p[1:])
        sira.append(p[0])
    return kayit, sira


def esleme_oku():
    e = {}
    if os.path.exists(ESLEME):
        for s in open(ESLEME, encoding="utf-8").read().splitlines():
            m = re.fullmatch(r"\s*(G-[A-ZÇĞİÖŞÜ]+-\d+)\s*=\s*(S-\d+)\s*", s)
            if m:
                e[m.group(1)] = m.group(2)
    return e


def kisa_baslik(olur, sinir=118):
    """Açıklamanın ilk cümlesi (ters tırnak içindeki noktalar sayılmaz), tek satır."""
    kes = len(olur)
    ters = False
    for i, c in enumerate(olur):
        if c == "`":
            ters = not ters
        if not ters and c == "." and i + 1 < len(olur) and olur[i + 1] == " ":
            kes = i
            break
    t = olur[:kes].strip()
    if len(t) > sinir:
        t = t[:sinir].rsplit(" ", 1)[0] + " …"
    if t.count("`") % 2:
        t += "`"
    return t


def kayit_metni(no, kimlik, v, satir_sonu):
    etk, tur, olur, yap = v
    tarih = BULUNDU.get(kimlik, VARSAYILAN_TARIH)
    oncelik = TUR_SIRASI.index(tur) + 1 if tur in TUR_SIRASI else 9
    baslik = kisa_baslik(olur)
    s = [
        f"## S-{no} — [{kimlik}] {baslik} ({etk})",
        f"**Bulundu:** {tarih} (Claude, Kılavuz V2 örnek doğrulaması ve yoklama koşuları) · **Durum:** `ACIK` · **Tür:** {tur} (öncelik {oncelik}/6) · **Etkilenen:** {etk} · **Kılavuz kaydı:** {kimlik} · Denenen derleyici: `{DENENEN.get(kimlik, DENENEN_VARSAYILAN)}`",
        olur,
        f"**Geçici çözüm (kılavuzda önerilen, sorunu ÇÖZMEZ):** {yap}",
        f"**Hedef:** {TUR_HEDEF.get(tur, '')}",
        "**Kök neden:** araştırılmadı; gözlem kılavuz yazımı sırasında yapıldı. En küçük yeniden üretim, Kılavuz V2'nin ilgili bölümündeki örnek ve Ek G satırıdır "
        "(`docs/tasarim/uXBasic_Hedeflenen_Sistem_ve_Kullanma_Kilavuzu_V2_TR.md`).",
        "**Düzeltme:** yok. Kabul ölçütü: kayıttaki program AST, MIR, x64 ve JS'te (WASM destekliyorsa onda da) hedef davranışı verir; bu program yeni bir model "
        "testi olarak eklenir. Testi geçecek biçimde değiştirmek ya da beklentiyi gevşetmek çözüm sayılmaz.",
        "",
    ]
    return satir_sonu.join(s) + satir_sonu


def dizin_metni(kayit, esleme):
    sira = sorted(kayit, key=lambda k: (TUR_SIRASI.index(kayit[k][1]) if kayit[k][1] in TUR_SIRASI else 9, k))
    sat = ["# Kılavuz V2 sorun dizini (önerilen düzeltme sırası)", "",
           "Bu dosya `python tools/kitap/kilavuz_v2/sorun_takibe_isle.py` ile üretilir; kaynağı `tools/kitap/kilavuz_v2/veri/sinirlar.txt` kataloğudur.",
           "Her satırın ayrıntısı `SORUN_TAKIP.md` içindeki S-numaralı kayıttadır. Sıra: önce yanlış sonuç veren (SESSİZ), sonra çökme, motorlar arası fark, açık ret, eksik özellik, yavaşlık.",
           "", "| Tür | Kayıt sayısı | Anlamı |", "|---|---|---|"]
    for t in TUR_SIRASI:
        n = sum(1 for k in kayit if kayit[k][1] == t)
        sat.append(f"| {t} | {n} | {TUR_ACIKLAMA[t]} |")
    sat += ["", "| Sıra | Sorun | Kılavuz kaydı | Tür | Etkilenen | Belirti |", "|---|---|---|---|---|---|"]
    for i, k in enumerate(sira, 1):
        etk, tur, olur, _ = kayit[k]
        sat.append(f"| {i} | {esleme.get(k, '—')} | {k} | {tur} | {etk} | {kisa_baslik(olur, 90).replace('|', '/')} |")
    sat.append("")
    return "\n".join(sat)


# Aynı davranış ailesindeki ESKİ SORUN_TAKIP kayıtları (yüksek güvenli eşleşmeler). Kopya karışıklığı olmasın diye kayda 'İlgili eski kayıtlar' satırı eklenir.
ILGILI = {
    "G-CLI-2": ["S-170"], "G-CLI-7": ["S-116"], "G-DIL-6": ["S-171"], "G-DIL-9": ["S-128"],
    "G-TIP-2": ["S-085"], "G-TIP-3": ["S-077", "S-088"], "G-TIP-5": ["S-007", "S-176"], "G-TIP-6": ["S-005", "S-010", "S-018"],
    "G-METIN-2": ["S-179"], "G-METIN-3": ["S-183"], "G-KOLEKSIYON-1": ["S-019"],
    "G-YORDAM-1": ["S-187"], "G-YORDAM-2": ["S-166"], "G-YORDAM-3": ["S-001"], "G-YORDAM-4": ["S-001"], "G-YORDAM-5": ["S-118"],
    "G-VERI-2": ["S-051", "S-122", "S-167"], "G-VERI-4": ["S-159"],
    "G-NESNE-1": ["S-186"], "G-NESNE-3": ["S-186"], "G-NESNE-9": ["S-198"],
    "G-HATA-1": ["S-160"], "G-HATA-2": ["S-160", "S-097"], "G-HATA-3": ["S-160"],
    "G-DOSYA-1": ["S-165"], "G-DOSYA-3": ["S-165"],
    "G-GOREV-1": ["S-030"], "G-GOREV-2": ["S-030"], "G-GOREV-3": ["S-012", "S-030"], "G-GOREV-4": ["S-146"], "G-GOREV-5": ["S-030"],
    "G-GOREV-6": ["S-030"], "G-GOREV-7": ["S-030"], "G-GOREV-8": ["S-030"], "G-GOREV-10": ["S-149"], "G-GOREV-11": ["S-030"],
    "G-JS-1": ["S-178"], "G-JS-2": ["S-160"], "G-JS-4": ["S-085"], "G-JS-5": ["S-046", "S-152"], "G-JS-7": ["S-153", "S-118"], "G-JS-8": ["S-180"],
    "G-WASM-2": ["S-180"], "G-WASM-6": ["S-198"], "G-WASM-7": ["S-150"], "G-WASM-9": ["S-150", "S-085"],
    "G-KUT-4": ["S-201"], "G-KUT-10": ["S-075"],
    "G-KTIP-1": ["S-112", "S-114", "S-134"], "G-KTIP-2": ["S-112"], "G-KTIP-5": ["S-134"],
    "G-MODUL-1": ["S-140"], "G-MODUL-2": ["S-141", "S-162"], "G-DIS-7": ["S-144"], "G-DIS-8": ["S-076"],
    "G-ONISLEM-14": ["S-136"], "G-ONISLEM-15": ["S-136"], "G-META-1": ["S-136"],
    "G-HIZ-1": ["S-090", "S-109", "S-110"], "G-HIZ-2": ["S-191"], "G-HIZ-3": ["S-111"],
    "G-TIP-7": ["S-113"], "G-TIP-8": ["S-154"], "G-TIP-9": ["S-091", "S-092", "S-085"], "G-KOLEKSIYON-6": ["S-135"], "G-DIL-11": ["S-094"],
    "G-HEDEF-1": ["S-113"], "G-HEDEF-5": ["S-030"], "G-HEDEF-6": ["S-030"], "G-HEDEF-7": ["S-147"], "G-HEDEF-8": ["S-146"], "G-HEDEF-9": ["S-146", "S-134"],
    "G-HEDEF-10": ["S-146"], "G-HEDEF-11": ["S-146", "S-094"], "G-HEDEF-12": ["S-030", "S-146"], "G-HEDEF-13": ["S-115"], "G-HEDEF-14": ["S-112", "S-114", "S-134"],
    "G-HEDEF-15": ["S-136"], "G-HEDEF-16": ["S-136"], "G-HEDEF-17": ["S-153", "S-118", "S-170"], "G-HEDEF-18": ["S-085", "S-150", "S-122", "S-123", "S-114"],
    "G-HEDEF-19": ["S-004"], "G-HEDEF-20": ["S-193"], "G-NESNE-18": ["S-186"], "G-NESNE-19": ["S-119"], "G-JS-13": ["S-119", "S-130"],
    "G-HATA-11": ["S-193", "S-410"], "G-HATA-12": ["S-193"], "G-HATA-13": ["S-193", "S-410"], "G-KTIP-7": ["S-112", "S-114", "S-443"],
    "G-TIP-15": ["S-446"], "G-TIP-16": ["S-064"], "G-ISLEC-8": ["S-446"], "G-TIP-17": ["S-480"], "G-KTIP-8": ["S-112", "S-114"], "G-TIP-19": ["S-503", "S-502"], "G-TIP-20": ["S-446", "S-503"], "G-TIP-21": ["S-446"], "G-TIP-22": ["S-446"], "G-WASM-21": ["S-216", "S-418"], "G-WASM-22": ["S-219", "S-418"], "G-TIP-23": ["S-510"], "G-TIP-24": ["S-511", "S-510"], "G-TIP-25": ["S-510", "S-503"], "G-TIP-26": ["S-510"], "G-TIP-27": ["S-510"], "G-ISLEC-10": ["S-219"], "G-HEDEF-30": ["S-134", "S-193"], "G-NESNE-29": ["S-480"], "G-DIL-16": ["S-459", "S-460"],
    "G-ISLEC-12": ["S-086"], "G-METIN-6": ["S-157", "S-157-L"], "G-HATA-14": ["S-091", "S-461"], "G-MODUL-6": ["S-480"], "G-DIL-17": ["S-480"], "G-DIS-13": ["S-145", "S-480"],
    "G-YORDAM-9": ["S-329", "S-395"],
    "G-WASM-23": ["S-329", "S-391"],
    "G-DOSYA-10": ["S-386"],
    "G-NESNE-30": ["S-360", "S-394", "S-488"],
    "G-NESNE-34": ["S-394"],
    "G-TIP-29": ["S-437"],
    "G-TIP-30": ["S-386"],
    "G-VERI-15": ["S-394"],
    "G-WASM-25": ["S-326"],
}


def capraz_basvuru(esleme, satir_sonu_zorla=None):
    """Eşlemesi olan kayıtlara 'İlgili eski kayıtlar' satırı ekler (zaten varsa dokunmaz)."""
    ham = open(TAKIP, "rb").read().decode("utf-8")
    sonu = "\r\n" if "\r\n" in ham else "\n"
    satirlar = ham.split(sonu)
    eklenen = 0
    for kimlik, eskiler in ILGILI.items():
        s_no = esleme.get(kimlik)
        if not s_no:
            continue
        bas = next((i for i, s in enumerate(satirlar) if s.startswith(f"## {s_no} — [{kimlik}]")), None)
        if bas is None:
            continue
        son = next((i for i in range(bas + 1, len(satirlar)) if satirlar[i].startswith("## ")), len(satirlar))
        if any(satirlar[i].startswith("**İlgili eski kayıtlar:**") for i in range(bas, son)):
            continue
        yer = next((i for i in range(bas + 1, son) if satirlar[i].startswith("**Bulundu:**")), None)
        if yer is None:
            continue
        satirlar.insert(yer + 1, "**İlgili eski kayıtlar:** " + ", ".join(eskiler) + " (aynı davranış ailesi; durumları ayrı doğrulanmalı, kopya sayılıp kapatılmamalı)")
        eklenen += 1
    if eklenen:
        once = os.path.getmtime(TAKIP)
        if os.path.getmtime(TAKIP) != once:
            print("HATA: SORUN_TAKIP.md değişti")
            sys.exit(1)
        open(TAKIP, "wb").write(sonu.join(satirlar).encode("utf-8"))
    return eklenen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dene", action="store_true", help="dosyaya yazmadan ne yapılacağını göster")
    a = ap.parse_args()
    kayit, katalog_sirasi = katalog_oku()
    esleme = esleme_oku()
    yeni = [k for k in katalog_sirasi if k not in esleme]
    print(f"katalog: {len(kayit)} kayıt · eşlemesi olan: {len(esleme)} · yeni: {len(yeni)}")
    if not yeni:
        open(DIZIN, "w", encoding="utf-8", newline="\n").write(dizin_metni(kayit, esleme))
        n = 0 if a.dene else capraz_basvuru(esleme)
        print(f"yeni kayıt yok; dizin yenilendi; çapraz başvuru eklenen kayıt: {n}")
        return
    ham = open(TAKIP, "rb").read()
    metin = ham.decode("utf-8")
    satir_sonu = "\r\n" if "\r\n" in metin else "\n"
    satirlar = metin.split(satir_sonu)
    numaralar = [int(m.group(1)) for s in satirlar for m in [re.match(r"^## S-(\d+)\b", s)] if m]
    en_buyuk = max(numaralar)
    son_s = max(i for i, s in enumerate(satirlar) if re.match(r"^## S-\d+\b", s))
    ekleme_yeri = next((i for i in range(son_s + 1, len(satirlar)) if satirlar[i].startswith("## ")), len(satirlar))
    print(f"SORUN_TAKIP: en büyük S-{en_buyuk}, ekleme satırı {ekleme_yeri + 1}")
    # Önerilen sıraya göre numara ver (düzeltme sırası = numara sırası)
    sirali = sorted(yeni, key=lambda k: (TUR_SIRASI.index(kayit[k][1]) if kayit[k][1] in TUR_SIRASI else 9, katalog_sirasi.index(k)))
    ilk = en_buyuk + 1
    dizin_no = ilk
    # Özet kayıt yalnız ilk toplu işlemede açılır; sonraki artımlı çalıştırmalarda yalnız tek tek kayıtlar eklenir (sıra tablosu dizin dosyasındadır).
    ozet_yaz = len(esleme) <= 1
    atanan = {}
    for i, k in enumerate(sirali):
        atanan[k] = ilk + (1 if ozet_yaz else 0) + i
    sayilar = {t: sum(1 for k in sirali if kayit[k][1] == t) for t in TUR_SIRASI}
    ozet = [
        f"## S-{dizin_no} — Kılavuz V2 sınır kataloğu: {len(sirali)} kusur ayrı kayıt olarak sıraya alındı (S-{ilk + 1} … S-{ilk + len(sirali)})",
        f"**Bulundu:** 2026-10-11 (Claude, Kılavuz V2 hazırlığı) · **Durum:** `ACIK` · Kaynak: `tools/kitap/kilavuz_v2/veri/sinirlar.txt` (Ek G)",
        "Kılavuz V2'nin hazırlığı sırasında gerçek derleyiciyle (`bin\\uxb_kilavuz_20261007.exe`) bulunan kusur ve sınırların TAMAMI burada ayrı ayrı kayıtlanmıştır. "
        "Numara sırası önerilen düzeltme sırasıdır: " + ", ".join(f"{t} {sayilar[t]}" for t in TUR_SIRASI) + ". "
        "Eşleme ve sıra tablosu: `ai_koordinasyon/KILAVUZ_V2_SORUN_DIZINI.md` (G-kaydı ↔ S-numarası); eşleme dosyası `tools/kitap/kilavuz_v2/veri/sorun_eslemesi.txt`.",
        "Kural (Mete, 2026-10-11): bu kayıtlar testi geçecek biçimde değiştirilerek kapatılmaz; kılavuzdaki geçici çözümler yalnız okuyucuya yol göstermek içindir ve "
        "sorunu çözmez. Gerçek çalışmada olması gereken davranış ve planlanan hedef her kayıtta yazılıdır.",
        "",
    ]
    blok = satir_sonu.join(ozet) + satir_sonu if ozet_yaz else ""
    for k in sirali:
        blok += kayit_metni(atanan[k], k, kayit[k], satir_sonu)
    if a.dene:
        print(blok[:3500])
        print(f"... toplam {len(blok)} karakter, {len(sirali)} kayıt (S-{ilk}…S-{ilk + len(sirali)})")
        return
    # yaz: aradan başkası dosyayı değiştirdiyse vazgeç
    once = os.path.getmtime(TAKIP)
    yeni_satirlar = satirlar[:ekleme_yeri] + blok.rstrip(satir_sonu).split(satir_sonu) + [""] + satirlar[ekleme_yeri:]
    if os.path.getmtime(TAKIP) != once:
        print("HATA: SORUN_TAKIP.md okurken değişti; yeniden çalıştırın")
        sys.exit(1)
    open(TAKIP, "wb").write(satir_sonu.join(yeni_satirlar).encode("utf-8"))
    with open(ESLEME, "a", encoding="utf-8", newline="\n") as f:
        for k in sirali:
            f.write(f"{k} = S-{atanan[k]}\n")
    esleme.update({k: f"S-{n}" for k, n in atanan.items()})
    open(DIZIN, "w", encoding="utf-8", newline="\n").write(dizin_metni(kayit, esleme))
    n = capraz_basvuru(esleme)
    print(f"yazıldı: S-{min(atanan.values())}…S-{max(atanan.values())} ({len(sirali)} kayıt{', özet S-' + str(dizin_no) if ozet_yaz else ''}); eşleme ve dizin güncellendi; çapraz başvuru: {n}")


main()
