# KONU: Aynı uXBasic programını beş motorda çalıştırıp çıktıları karşılaştırmak: AST, MIR, x64, JS ve WASM
# KOMUTLAR: uxb run · uxb run --interpreter-backend MIR · uxb bld --build-x64 · uxb jsw --js-out · uxb wat --emit-wasm --wat2wasm · node
# ACIKLAMA: Tamsayı, döngü, özyineleme ve koşul kullanan küçük bir program (100'e kadar asal sayıların toplamı, Fibonacci, en büyük ortak bölen, Collatz adım sayısı, faktöriyel) beş hedefte çalıştırılır. Program yalnız tamsayı yazdırır, çünkü WASM hedefi henüz metin (G-WASM-8) ve ondalıklı sayı (G-WASM-7) desteklemez. AST ve MIR yorumlayıcı, x64 yerel kod, JS node ile, WASM wat2wasm + node ile çalışır. Beş çıktı satır satır karşılaştırılır; fark varsa hangi motorun ayrıldığı yazılır. Bu, kılavuzun "aynı kaynak, aynı sonuç" ilkesinin tek komutluk sınamasıdır; node ve wat2wasm gerekir.
#= asal toplami, fib(20), ebob(1071, 462), collatz(27), 7!: 1060 6765 21 111 5040
#= AST, MIR, x64, JS ve WASM ayni cikti: evet
import os, shutil, subprocess, sys, tempfile

UXB = os.path.abspath(os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe")))
BIN = os.path.dirname(UXB)
KOK = os.path.dirname(BIN)
RUNTIME_DLL = os.path.join(BIN, "uxb_runtime.dll")
WAT2WASM = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")
NODE = shutil.which("node")

KAYNAK = '''FUNCTION AsalMi(n AS I32) AS I32
    IF n < 2 THEN RETURN 0
    DIM d AS I32 = 2
    DO WHILE d * d <= n
        IF n MOD d = 0 THEN RETURN 0
        d += 1
    LOOP
    RETURN 1
END FUNCTION

FUNCTION Fib(n AS I32) AS I32
    IF n < 2 THEN RETURN n
    RETURN Fib(n - 1) + Fib(n - 2)
END FUNCTION

FUNCTION Ebob(a AS I32, b AS I32) AS I32
    DIM x AS I32 = a
    DIM y AS I32 = b
    DIM t AS I32
    DO WHILE y <> 0
        t = x MOD y
        x = y
        y = t
    LOOP
    RETURN x
END FUNCTION

FUNCTION Collatz(n AS I32) AS I32
    DIM adim AS I32 = 0
    DIM x AS I32 = n
    DO WHILE x > 1
        IF x MOD 2 = 0 THEN
            x = x \\ 2
        ELSE
            x = 3 * x + 1
        END IF
        adim += 1
    LOOP
    RETURN adim
END FUNCTION

FUNCTION Fakt(n AS I32) AS I32
    IF n <= 1 THEN RETURN 1
    RETURN n * Fakt(n - 1)
END FUNCTION

DIM i AS I32
DIM toplam AS I32 = 0
FOR i = 2 TO 100
    IF AsalMi(i) = 1 THEN toplam += i
NEXT
PRINT toplam
PRINT Fib(20)
PRINT Ebob(1071, 462)
PRINT Collatz(27)
PRINT Fakt(7)
'''


def calistir(komut, cwd):
    ortam = dict(os.environ)
    ortam["PATH"] = BIN + os.pathsep + ortam["PATH"]
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=ortam, timeout=300)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def satirlar(metin):
    return [s.strip() for s in metin.splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]


if not NODE:
    print("node bulunamadi: JS ve WASM motorlari icin node gerekir")
    sys.exit(3)
if not os.path.exists(WAT2WASM):
    print("wat2wasm bulunamadi:", WAT2WASM)
    sys.exit(3)

with tempfile.TemporaryDirectory() as klasor:
    yol = os.path.join(klasor, "p.uxb")
    open(yol, "w", encoding="utf-8").write(KAYNAK)
    sonuclar = {}
    rc, c = calistir([UXB, "run", yol, "--out-root", os.path.join(klasor, "a")], KOK)
    sonuclar["AST"] = satirlar(c)
    rc, c = calistir([UXB, "run", yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], KOK)
    sonuclar["MIR"] = satirlar(c)

    exe = os.path.join(klasor, "p.exe")
    calistir([UXB, "bld", yol, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], KOK)
    if os.path.exists(exe):
        if os.path.exists(RUNTIME_DLL):
            shutil.copy(RUNTIME_DLL, klasor)
        rc, c = calistir([exe], klasor)
        sonuclar["x64"] = satirlar(c)
    else:
        sonuclar["x64"] = ["x64 derlenemedi"]

    js = os.path.join(klasor, "p.js")
    calistir([UXB, "jsw", yol, "--js-out", js, "--out-root", os.path.join(klasor, "j")], KOK)
    if os.path.exists(js):
        rc, c = calistir([NODE, js], klasor)
        sonuclar["JS"] = satirlar(c)
    else:
        sonuclar["JS"] = ["JS uretilemedi"]

    wd = os.path.join(klasor, "wasm")
    os.makedirs(wd, exist_ok=True)
    calistir([UXB, "wat", yol, "--emit-wasm", "--wasm-out", os.path.join(wd, "p.wasm"), "--wat-out", os.path.join(wd, "p.wat"),
              "--wat2wasm=" + WAT2WASM, "--out-root", os.path.join(klasor, "w")], KOK)
    if os.path.exists(os.path.join(wd, "p.wasm")) and os.path.exists(os.path.join(wd, "run_wasm.js")):
        rc, c = calistir([NODE, os.path.join(wd, "run_wasm.js")], wd)
        sonuclar["WASM"] = satirlar(c)
    else:
        sonuclar["WASM"] = ["WASM uretilemedi"]

ref = sonuclar["AST"]
print("asal toplami, fib(20), ebob(1071, 462), collatz(27), 7!: " + " ".join(ref))
farkli = [m for m, v in sonuclar.items() if v != ref]
if farkli:
    print("AYRILAN MOTORLAR: " + ", ".join(f"{m} -> {sonuclar[m]}" for m in farkli))
else:
    print("AST, MIR, x64, JS ve WASM ayni cikti: evet")
