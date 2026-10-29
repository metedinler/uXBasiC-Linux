# KONU: ZIP arşivini uxarchive ile açıp içeriği SHA-256 ile doğrulamak ve zip-slip saldırısına karşı korumayı sınamak (üç yerel motorda aynı sonuç)
# KOMUTLAR: python zipfile · uxarchive.EntryCount · ExtractAll · ErrorText · uxfs.ReadAllText · uxfs.DirectoryExists · uxfs.FileExists · uxcrypto.Sha256Text · uxb run · uxb bld
# ACIKLAMA: Python iki ZIP üretir: düzgün bir arşiv (iç içe klasör ve boş klasör dahil) ve içinde "../kacak.txt" adlı hileli bir giriş bulunan arşiv (zip-slip saldırısı). uXBasic programı uxarchive (libarchive tabanlı) ile ikisini de açar; düzgün arşivde her dosyanın SHA-256 özetini Python'un hesapladığı özetle karşılaştırır, hileli arşivde kütüphanenin girişi reddettiğini ve hedef klasörün dışına hiçbir dosya yazılmadığını doğrular. Dikkat (G-KUT-18): reddedilen girişten önceki dosyalar açılmış kalır (kısmi çıkarma) ve Latin-1 dışındaki harfler (ğ, ı, ş, Ğ, İ, Ş) dosya adında geçerse arşiv "(null)" iletisiyle reddedilir; bu örnekte yalnız ASCII adlar kullanılır. Aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır.
#= arsiv: 3 giris, 3 giris acildi
#= merhaba.txt: ozet dogru
#= alt/klasor/veri.csv: ozet dogru
#= bos_klasor: klasor olusturuldu
#= zip-slip arsivi: reddedildi (unsafe archive entry rejected: ../kacak.txt)
#= hedefin disina dosya yazildi mi: HAYIR
#= reddedilen arsivden onceki dosya acildi mi: EVET
#= motorlar ayni: evet (AST, MIR, x64)
import hashlib, os, shutil, subprocess, sys, tempfile, zipfile

UXB = os.path.abspath(os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe")))
BIN = os.path.dirname(UXB)
KOK = os.path.dirname(BIN)
RUNTIME_DLL = os.path.join(BIN, "uxb_runtime.dll")

MERHABA = "merhaba dunya\n"
VERI = "a,b\n1,2\n"

UXB_KAYNAK = '''INCLUDE "include/modules/uxarchive.uxmh"
INCLUDE "include/modules/uxfs.uxmh"
INCLUDE "include/modules/uxcrypto.uxmh"

' Dosyanın SHA-256 özetini beklenen değerle karşılaştırır
SUB Kontrol(ad AS STRING, yol AS STRING, beklenen AS STRING)
    DIM icerik AS STRING = uxfs.ReadAllText(yol)
    DIM ozet AS STRING = uxcrypto.Sha256Text(icerik)
    IF ozet = beklenen THEN
        PRINT ad; ": ozet dogru"
    ELSE
        PRINT ad; ": OZET YANLIS"
    END IF
END SUB

MAIN
    DIM n AS I64
    DIM c AS I64
    DIM hata AS STRING
    DIM var AS I32

    n = uxarchive.EntryCount("@IYI@")
    c = uxarchive.ExtractAll("@IYI@", "@HEDEF1@")
    PRINT "arsiv: "; n; " giris, "; c; " giris acildi"
    Kontrol("merhaba.txt", "@HEDEF1@/merhaba.txt", "@H1@")
    Kontrol("alt/klasor/veri.csv", "@HEDEF1@/alt/klasor/veri.csv", "@H2@")
    var = uxfs.DirectoryExists("@HEDEF1@/bos_klasor")
    IF var = 1 THEN PRINT "bos_klasor: klasor olusturuldu"

    c = uxarchive.ExtractAll("@KOTU@", "@HEDEF2@/ic")
    hata = uxarchive.ErrorText()
    IF c = -1 THEN PRINT "zip-slip arsivi: reddedildi ("; hata; ")"
    var = uxfs.FileExists("@HEDEF2@/kacak.txt")
    IF var = 1 THEN
        PRINT "hedefin disina dosya yazildi mi: EVET"
    ELSE
        PRINT "hedefin disina dosya yazildi mi: HAYIR"
    END IF
    var = uxfs.FileExists("@HEDEF2@/ic/ok.txt")
    IF var = 1 THEN
        PRINT "reddedilen arsivden onceki dosya acildi mi: EVET"
    ELSE
        PRINT "reddedilen arsivden onceki dosya acildi mi: HAYIR"
    END IF
END MAIN
'''


def calistir(komut, cwd):
    ortam = dict(os.environ)
    ortam["PATH"] = BIN + os.pathsep + ortam["PATH"]  # libarchive ve bagimliliklari icin
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=ortam, timeout=300)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]


def sha(metin):
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


with tempfile.TemporaryDirectory() as klasor:
    iyi = os.path.join(klasor, "iyi.zip")
    with zipfile.ZipFile(iyi, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("merhaba.txt", MERHABA)
        z.writestr("alt/klasor/veri.csv", VERI)
        z.writestr("bos_klasor/", "")  # sonu "/" ile biten giriş boş klasördür
    kotu = os.path.join(klasor, "kotu.zip")
    with zipfile.ZipFile(kotu, "w") as z:
        z.writestr("ok.txt", "tamam\n")
        z.writestr("../kacak.txt", "disari kactim\n")

    sonuclar = {}
    for motor in ("AST", "MIR", "x64"):
        hedef1 = os.path.join(klasor, "cikti_" + motor + "_iyi").replace("\\", "/")
        hedef2 = os.path.join(klasor, "cikti_" + motor + "_kotu").replace("\\", "/")
        os.makedirs(hedef2, exist_ok=True)
        kaynak = (UXB_KAYNAK.replace("@IYI@", iyi.replace("\\", "/")).replace("@KOTU@", kotu.replace("\\", "/"))
                  .replace("@HEDEF1@", hedef1).replace("@HEDEF2@", hedef2).replace("@H1@", sha(MERHABA)).replace("@H2@", sha(VERI)))
        yol = os.path.join(klasor, "arsiv_" + motor + ".uxb")
        open(yol, "w", encoding="utf-8").write(kaynak)
        if motor == "AST":
            rc, cikti = calistir([UXB, "run", yol, "--out-root", os.path.join(klasor, "a")], KOK)
        elif motor == "MIR":
            rc, cikti = calistir([UXB, "run", yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], KOK)
        else:
            exe = os.path.join(klasor, "arsiv.exe")
            calistir([UXB, "bld", yol, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], KOK)
            if not os.path.exists(exe):
                sonuclar[motor] = ["x64 derlenemedi"]
                continue
            if os.path.exists(RUNTIME_DLL):
                shutil.copy(RUNTIME_DLL, klasor)
            rc, cikti = calistir([exe], KOK)
        sonuclar[motor] = sonuc_satirlari(cikti)

for satir in sonuclar["AST"]:
    print(satir)
ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 7
print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
