# KONU: Kendi C kütüphanenizi derleyip uXBasic'ten çağırmak (üç yerel motorda aynı sonuç)
# KOMUTLAR: gcc -shared · CALL(DLL) · VARPTR · uxb run · uxb bld
# ACIKLAMA: C ile küçük bir DLL yazılıp derlenir; uXBasic programı onu CALL(DLL, ...) ile çağırır (tamsayı, ondalıklı, metin ve dizi göstericisi). Aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır. DLL adı yalnız dosya adıdır; DLL, programın çalıştığı klasörde bulunmalıdır.
#= topla = 5
#= harf = 3
#= kare = 2.25
#= ortalama = 3
#= buyuk = 5000000000
#= motorlar ayni: evet (AST, MIR, x64)
import os, shutil, subprocess, sys, tempfile

UXB = os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe"))
GCC = os.environ.get("UXB_GCC", r"C:\msys64\ucrt64\bin\gcc.exe")
RUNTIME_DLL = os.path.join(os.path.dirname(os.path.abspath(UXB)), "uxb_runtime.dll")

C_KAYNAK = r'''
__declspec(dllexport) int mini_topla(int a, int b) { return a + b; }
__declspec(dllexport) int mini_harf_say(const char *s, int c) { int n = 0; for (; *s; s++) if (*s == c) n++; return n; }
__declspec(dllexport) double mini_kare(double x) { return x * x; }
__declspec(dllexport) double mini_ortalama(const double *v, int n) { double t = 0; for (int i = 0; i < n; i++) t += v[i]; return n ? t / n : 0; }
__declspec(dllexport) long long mini_buyuk(long long x) { return x * 1000000000LL; }
'''

UXB_KAYNAK = '''DIM v(2) AS F64
DIM a AS I32
DIM h AS I32
DIM k AS F64
DIM o AS F64
DIM b AS I64
v(0) = 1.0: v(1) = 2.0: v(2) = 6.0
a = CALL(DLL, "mini.dll", "mini_topla", I32, CDECL, "I32,I32", 2, 3)
h = CALL(DLL, "mini.dll", "mini_harf_say", I32, CDECL, "STRPTR,I32", "banana", ASC("a"))
k = CALL(DLL, "mini.dll", "mini_kare", F64, CDECL, "F64", 1.5)
o = CALL(DLL, "mini.dll", "mini_ortalama", F64, CDECL, "PTR,I32", VARPTR(v(0)), 3)
b = CALL(DLL, "mini.dll", "mini_buyuk", I64, CDECL, "I64", 5)
PRINT "topla = "; a
PRINT "harf = "; h
PRINT "kare = "; k
PRINT "ortalama = "; o
PRINT "buyuk = "; b
'''


def calistir(komut, cwd, env=None):
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=env)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if " = " in s and not s.startswith(("INFO", "WARN"))]


if not os.path.exists(GCC):
    print("gcc bulunamadi: UXB_GCC ortam degiskenine MinGW gcc yolunu yazin")
    sys.exit(3)

with tempfile.TemporaryDirectory() as klasor:
    open(os.path.join(klasor, "mini.c"), "w").write(C_KAYNAK)
    open(os.path.join(klasor, "p.uxb"), "w", encoding="utf-8").write(UXB_KAYNAK)
    ortam = dict(os.environ)
    ortam["PATH"] = os.path.dirname(GCC) + os.pathsep + ortam["PATH"]
    rc, cikti = calistir([GCC, "-shared", "-O2", "-o", os.path.join(klasor, "mini.dll"), os.path.join(klasor, "mini.c")], klasor, ortam)
    if rc != 0:
        print("DLL derlenemedi:", cikti[-300:])
        sys.exit(4)

    sonuclar = {}
    rc, cikti = calistir([UXB, "run", "p.uxb", "--out-root", os.path.join(klasor, "a")], klasor)
    sonuclar["AST"] = sonuc_satirlari(cikti)
    rc, cikti = calistir([UXB, "run", "p.uxb", "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], klasor)
    sonuclar["MIR"] = sonuc_satirlari(cikti)
    exe = os.path.join(klasor, "p.exe")
    calistir([UXB, "bld", "p.uxb", "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], klasor)
    if os.path.exists(exe):
        if os.path.exists(RUNTIME_DLL):
            shutil.copy(RUNTIME_DLL, klasor)
        rc, cikti = calistir([exe], klasor)
        sonuclar["x64"] = sonuc_satirlari(cikti)
    else:
        sonuclar["x64"] = ["x64 derlenemedi"]

    for satir in sonuclar["AST"]:
        print(satir)
    ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 5
    print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
