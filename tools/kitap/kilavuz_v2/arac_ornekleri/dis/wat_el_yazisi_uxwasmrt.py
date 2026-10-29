# KONU: Elle yazılmış WAT modülünü wat2wasm ile derleyip uxwasmrt (wasmtime) üzerinden uXBasic'ten çağırmak
# KOMUTLAR: wat2wasm · uxwasmrt.WasmOpenFile · WasmCallI32_1 · WasmCallI32_2 · WasmLastError · uxb wat --emit-wasm · uxb run · uxb bld
# ACIKLAMA: Üç tamsayı işlevi (EBOB, FIB, COLLATZ) WebAssembly metin biçiminde (WAT) elle yazılır, wat2wasm ile ikiliye çevrilir ve uXBasic programı uxwasmrt ile yükleyip çağırır. Aynı algoritmalar uXBasic'te de yazılmıştır; program iki sonucu 1600 + 41 girdide karşılaştırır. İkinci bölüm bir sınırı gösterir: uXBasic'in kendi ürettiği WASM modülü her zaman dört "ux" içe aktarması taşır ve uxwasmrt (yalnız çekirdek i32 modülleri) onu açıkça reddeder (G-WASM-10). Aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır.
#= saglayici: wasmtime-wasm-c-api/core-i32
#= el yazisi WAT: gecerli=1
#= EBOB(48, 18) = 6
#= FIB(30) = 832040
#= COLLATZ(27) = 111
#= EBOB: 1..40 x 1..40 uyumsuz 0
#= FIB: 0..40 uyumsuz 0
#= uXBasic'in urettigi WASM: gecerli=0 (Unsupported WASM import: ux.host_call16)
#= motorlar ayni: evet (AST, MIR, x64)
import os, shutil, subprocess, sys, tempfile

UXB = os.path.abspath(os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe")))
BIN = os.path.dirname(UXB)
KOK = os.path.dirname(BIN)
RUNTIME_DLL = os.path.join(BIN, "uxb_runtime.dll")
WAT2WASM = os.path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe")

WAT = r'''(module
  ;; En buyuk ortak bolen (Oklid): (a, b) -> ebob
  (func $ebob (export "EBOB") (param $a i32) (param $b i32) (result i32)
    (local $t i32)
    (block $son
      (loop $dongu
        (br_if $son (i32.eqz (local.get $b)))
        (local.set $t (i32.rem_u (local.get $a) (local.get $b)))
        (local.set $a (local.get $b))
        (local.set $b (local.get $t))
        (br $dongu)))
    (local.get $a))

  ;; n. Fibonacci sayisi (dongu ile): FIB(0)=0, FIB(1)=1
  (func $fib (export "FIB") (param $n i32) (result i32)
    (local $a i32) (local $b i32) (local $t i32) (local $i i32)
    (local.set $b (i32.const 1))
    (block $son
      (loop $dongu
        (br_if $son (i32.ge_s (local.get $i) (local.get $n)))
        (local.set $t (i32.add (local.get $a) (local.get $b)))
        (local.set $a (local.get $b))
        (local.set $b (local.get $t))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $dongu)))
    (local.get $a))

  ;; Collatz adim sayisi: tekse 3n+1, ciftse n/2; 1'e ulasana kadar
  (func $collatz (export "COLLATZ") (param $n i32) (result i32)
    (local $adim i32)
    (block $son
      (loop $dongu
        (br_if $son (i32.le_u (local.get $n) (i32.const 1)))
        (if (i32.and (local.get $n) (i32.const 1))
          (then (local.set $n (i32.add (i32.mul (local.get $n) (i32.const 3)) (i32.const 1))))
          (else (local.set $n (i32.shr_u (local.get $n) (i32.const 1)))))
        (local.set $adim (i32.add (local.get $adim) (i32.const 1)))
        (br $dongu)))
    (local.get $adim))
)
'''

UXB_KUTUPHANE = '''FUNCTION Topla(a AS I32, b AS I32) AS I32
    RETURN a + b
END FUNCTION

FUNCTION Fib(n AS I32) AS I32
    IF n < 2 THEN RETURN n
    RETURN Fib(n - 1) + Fib(n - 2)
END FUNCTION

MAIN
    DIM s AS I32 = Topla(2, 3)
END MAIN
'''

UXB_ISTEMCI = '''INCLUDE "include/modules/uxwasmrt.uxmh"

FUNCTION EbobUx(a AS I32, b AS I32) AS I32
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

FUNCTION FibUx(n AS I32) AS I32
    DIM a AS I32 = 0
    DIM b AS I32 = 1
    DIM t AS I32
    DIM i AS I32
    FOR i = 1 TO n
        t = a + b
        a = b
        b = t
    NEXT
    RETURN a
END FUNCTION

MAIN
    DIM oturum AS I32
    DIM sonuc AS I32
    DIM beklenen AS I32
    DIM ok AS I32
    DIM a AS I32
    DIM b AS I32
    DIM uyumsuz AS I32
    DIM saglayici AS STRING
    DIM hata AS STRING

    saglayici = WasmProvider()
    PRINT "saglayici: "; saglayici
    ok = WasmValidateFile("@EL@")
    PRINT "el yazisi WAT: gecerli="; ok
    oturum = WasmOpenFile("@EL@")
    ASSERT oturum <> 0, "WASM modulu acilamadi"

    sonuc = WasmCallI32_2(oturum, "EBOB", 48, 18)
    PRINT "EBOB(48, 18) = "; sonuc
    sonuc = WasmCallI32_1(oturum, "FIB", 30)
    PRINT "FIB(30) = "; sonuc
    sonuc = WasmCallI32_1(oturum, "COLLATZ", 27)
    PRINT "COLLATZ(27) = "; sonuc

    uyumsuz = 0
    FOR a = 1 TO 40
        FOR b = 1 TO 40
            sonuc = WasmCallI32_2(oturum, "EBOB", a, b)
            beklenen = EbobUx(a, b)
            IF sonuc <> beklenen THEN uyumsuz += 1
        NEXT
    NEXT
    PRINT "EBOB: 1..40 x 1..40 uyumsuz "; uyumsuz

    uyumsuz = 0
    FOR a = 0 TO 40
        sonuc = WasmCallI32_1(oturum, "FIB", a)
        beklenen = FibUx(a)
        IF sonuc <> beklenen THEN uyumsuz += 1
    NEXT
    PRINT "FIB: 0..40 uyumsuz "; uyumsuz
    ok = WasmClose(oturum)

    ok = WasmValidateFile("@UXB@")
    hata = WasmLastError(0)
    PRINT "uXBasic'in urettigi WASM: gecerli="; ok; " ("; hata; ")"
END MAIN
'''


def calistir(komut, cwd):
    ortam = dict(os.environ)
    ortam["PATH"] = BIN + os.pathsep + ortam["PATH"]
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=ortam, timeout=300)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]


if not os.path.exists(WAT2WASM):
    print("wat2wasm bulunamadi:", WAT2WASM)
    sys.exit(3)

with tempfile.TemporaryDirectory() as klasor:
    el_wat = os.path.join(klasor, "el.wat")
    el_wasm = os.path.join(klasor, "el.wasm")
    open(el_wat, "w", encoding="utf-8").write(WAT)
    rc, cikti = calistir([WAT2WASM, el_wat, "-o", el_wasm], klasor)
    if rc != 0:
        print("wat2wasm basarisiz:", cikti[-300:])
        sys.exit(4)

    kutuphane = os.path.join(klasor, "kutuphane.uxb")
    ux_wasm = os.path.join(klasor, "ux.wasm")
    open(kutuphane, "w", encoding="utf-8").write(UXB_KUTUPHANE)
    rc, cikti = calistir([UXB, "wat", kutuphane, "--emit-wasm", "--wasm-out", ux_wasm, "--wat-out", os.path.join(klasor, "ux.wat"),
                          "--wat2wasm=" + WAT2WASM, "--out-root", os.path.join(klasor, "w")], KOK)
    if not os.path.exists(ux_wasm):
        print("uXBasic WASM uretilemedi:", cikti[-300:])
        sys.exit(5)

    kaynak = UXB_ISTEMCI.replace("@EL@", el_wasm.replace("\\", "/")).replace("@UXB@", ux_wasm.replace("\\", "/"))
    istemci = os.path.join(klasor, "istemci.uxb")
    open(istemci, "w", encoding="utf-8").write(kaynak)

    sonuclar = {}
    rc, cikti = calistir([UXB, "run", istemci, "--out-root", os.path.join(klasor, "a")], KOK)
    sonuclar["AST"] = sonuc_satirlari(cikti)
    rc, cikti = calistir([UXB, "run", istemci, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], KOK)
    sonuclar["MIR"] = sonuc_satirlari(cikti)
    exe = os.path.join(klasor, "istemci.exe")
    calistir([UXB, "bld", istemci, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], KOK)
    if os.path.exists(exe):
        if os.path.exists(RUNTIME_DLL):
            shutil.copy(RUNTIME_DLL, klasor)
        rc, cikti = calistir([exe], KOK)
        sonuclar["x64"] = sonuc_satirlari(cikti)
    else:
        sonuclar["x64"] = ["x64 derlenemedi"]

for satir in sonuclar["AST"]:
    print(satir)
ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 8
print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
