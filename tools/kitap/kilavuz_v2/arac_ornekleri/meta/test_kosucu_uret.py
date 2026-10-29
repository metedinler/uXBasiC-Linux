# KONU: AST'den sınama işlevlerini bulup sınama koşucusu üretmek (meta üretim)
# KOMUTLAR: uxb ast --ast-json-out · uxb run --interpreter-backend MIR
# ACIKLAMA: Adı Test_ ile başlayan ve BOOLEAN döndüren her işlev bulunur; her biri için çağrı yazan bir koşucu üretilir ve MIR yorumlayıcısıyla çalıştırılır. Elle liste tutmak gerekmez.
#= bulunan sinamalar: Test_Toplama, Test_Carpma, Test_Hatali
#= Test_Toplama: gecti
#= Test_Carpma: gecti
#= Test_Hatali: KALDI
#= ozet: 2 gecti, 1 kaldi
import json, os, subprocess, sys, tempfile

UXB = os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe"))
KAYNAK = '''FUNCTION Topla(a AS I32, b AS I32) AS I32
    RETURN a + b
END FUNCTION

FUNCTION Test_Toplama() AS BOOLEAN
    RETURN BOOLEAN(Topla(2, 3) = 5)
END FUNCTION

FUNCTION Test_Carpma() AS BOOLEAN
    RETURN BOOLEAN(6 * 7 = 42)
END FUNCTION

FUNCTION Test_Hatali() AS BOOLEAN
    RETURN BOOLEAN(Topla(1, 1) = 3)
END FUNCTION
'''


def calistir(*arg):
    return subprocess.run([UXB, *arg], capture_output=True)


with tempfile.TemporaryDirectory() as klasor:
    yol = os.path.join(klasor, "p.uxb")
    open(yol, "w", encoding="utf-8").write(KAYNAK)
    ast_yol = os.path.join(klasor, "ast.json")
    calistir("ast", yol, "--ast-json-out", ast_yol, "--out-root", os.path.join(klasor, "r1"))
    kok = json.load(open(ast_yol, encoding="utf-8"))["root"]
    # AST adları küçük harfle tutar; özgün yazım için kaynak satırına bakılır
    satirlar = KAYNAK.splitlines()
    sinamalar = []
    for d in kok["children"]:
        if d["kind"] == "FUNCTION_STMT" and d["value"].startswith("test_"):
            donus = [c["value"] for c in d["children"] if c["kind"] == "RETURN_TYPE"]
            if donus == ["BOOLEAN"]:
                ozgun = satirlar[d["line"] - 1].split("FUNCTION", 1)[1].split("(")[0].strip()
                sinamalar.append(ozgun)
    print("bulunan sinamalar:", ", ".join(sinamalar))
    kosucu = KAYNAK + "\n"
    for ad in sinamalar:
        kosucu += f'IF {ad}() THEN PRINT "{ad}: gecti" ELSE PRINT "{ad}: KALDI"\n'
    kos_yol = os.path.join(klasor, "kosucu.uxb")
    open(kos_yol, "w", encoding="utf-8").write(kosucu)
    sonuc = calistir("run", kos_yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "r2"))
    satir = [s for s in sonuc.stdout.decode("utf-8", "replace").splitlines() if ": " in s and not s.startswith("INFO")]
    for s in satir:
        print(s.strip())
    print(f"ozet: {sum(1 for s in satir if s.endswith('gecti'))} gecti, {sum(1 for s in satir if s.endswith('KALDI'))} kaldi")
