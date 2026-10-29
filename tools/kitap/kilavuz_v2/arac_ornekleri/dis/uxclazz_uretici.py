# KONU: UXClazz kaynak üreticisi: CLAZZ bildiriminden sınıf kodu üretmek
# KOMUTLAR: tools/uxclazz/uxclazz.py · CLAZZ DATA · DERIVE EQ, HASH, CLONE, TOSTRING · uxb run · uxb bld
# ACIKLAMA: UXClazz derleyicinin bir parçası değil, derleyiciden önce çalışan bir Python aracıdır: .uxclz dosyasındaki CLAZZ bildirimini okur ve normal uXBasic CLASS koduna (kurucu, Get/Set metotları, Equals, MAGIC HASH/CLONE/TOSTRING) dönüştürür. Bu betik küçük bir CLAZZ DATA bildirimi yazar, aracı çalıştırır, çıktının başına/sonuna bir MAIN ekler ve üretilen sınıfı AST, MIR ve x64 motorlarında çalıştırıp çıktıları karşılaştırır. Üretici bugünkü derleyiciyle iki yerde uyuşmaz: farklı tipli alanlar için yazdığı Set<Alan>(value AS T) metotlarının parametre adları aynı sınıfta çakışır (G-NESNE-16) ve DERIVE JSON için C tarzı kaçışlı metin yazar (G-ARAC-2). Bu betik DERIVE JSON kullanmaz ve setter parametre adlarını tekilleştirir.
#= kod = A1
#= boy = 4.5
#= metin = Balik(Kod=A1, Boy=4.5)
#= esit = -1
#= motorlar ayni: evet (AST, MIR, x64)
import os, re, shutil, subprocess, sys, tempfile

UXB = os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe"))
KOK = os.getcwd()
RUNTIME_DLL = os.path.join(os.path.dirname(os.path.abspath(UXB)), "uxb_runtime.dll")

CLAZZ = '''CLAZZ DATA Balik
    DERIVE EQ, HASH, CLONE, TOSTRING
    Kod AS STRING
    Boy AS F64
END CLAZZ
'''

ANA = '''
MAIN
    DIM f AS Balik = NEW Balik("A1", 2.5)
    DIM k AS Balik = NEW Balik("A1", 2.5)
    DIM kod AS STRING
    DIM boy AS F64
    DIM metin AS STRING
    DIM esit AS I32
    f.SetBoy(4.5)
    k = f
    kod = f.GetKod()
    boy = f.GetBoy()
    metin = STR(f)
    esit = f.Equals(k)
    PRINT "kod = "; kod
    PRINT "boy = "; boy
    PRINT "metin = "; metin
    PRINT "esit = "; esit
END MAIN
'''


def calistir(komut, cwd, env=None):
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=env)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if " = " in s and not s.startswith(("INFO", "WARN"))]


with tempfile.TemporaryDirectory() as klasor:
    girdi = os.path.join(klasor, "balik.uxclz")
    uretilen = os.path.join(klasor, "balik_uretilen.uxb")
    open(girdi, "w", encoding="utf-8").write(CLAZZ)
    rc, cikti = calistir([sys.executable, os.path.join("tools", "uxclazz", "uxclazz.py"), girdi, "-o", uretilen,
                          "--manifest", os.path.join(klasor, "balik.metadata.json")], KOK)
    if rc != 0 or not os.path.exists(uretilen):
        print("uxclazz basarisiz:", cikti[-300:])
        sys.exit(3)
    kod = open(uretilen, encoding="utf-8").read()
    # G-NESNE-16: aynı sınıfta farklı tipli aynı adlı parametre -> her setter'a tekil ad ver
    kod = re.sub(r"METHOD Set(\w+)\(value AS (\w+)\)\n(\s+)THIS\.(\w+) = value", r"METHOD Set\1(v\1 AS \2)\n\3THIS.\4 = v\1", kod)
    # AST'de nesne atamasi referanstir; k = f ayni nesneyi gosterir, Equals(k) -1 verir
    program = os.path.join(klasor, "p.uxb")
    open(program, "w", encoding="utf-8").write(kod + ANA)

    sonuclar = {}
    rc, cikti = calistir([UXB, "run", program, "--out-root", os.path.join(klasor, "a")], KOK)
    sonuclar["AST"] = sonuc_satirlari(cikti)
    rc, cikti = calistir([UXB, "run", program, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], KOK)
    sonuclar["MIR"] = sonuc_satirlari(cikti)
    exe = os.path.join(klasor, "p.exe")
    calistir([UXB, "bld", program, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], KOK)
    if os.path.exists(exe):
        if os.path.exists(RUNTIME_DLL):
            shutil.copy(RUNTIME_DLL, klasor)
        rc, cikti = calistir([exe], klasor)
        sonuclar["x64"] = sonuc_satirlari(cikti)
    else:
        sonuclar["x64"] = ["x64 derlenemedi"]

    for satir in sonuclar["AST"]:
        print(satir)
    ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 4
    print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
