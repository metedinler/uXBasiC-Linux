# KONU: Derleyicinin AST raporundan işlev ve sınıf belgesi çıkarmak
# KOMUTLAR: uxb ast --ast-json-out
# ACIKLAMA: Derleyici kaynağı çözümler ve AST'yi JSON olarak yazar. Bu betik o JSON'u okuyup işlev, yordam ve sınıf imzalarını listeler; kaynağı kendisi ayrıştırmaz.
#= FUNCTION Topla(a AS I32, b AS I32) AS I32   [satir 1]
#= SUB Selam(ad AS STRING)   [satir 5]
#= CLASS Nokta { x AS I32, y AS I32 }   [satir 9]
import json, os, subprocess, sys, tempfile

UXB = os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe"))
KAYNAK = '''FUNCTION Topla(a AS I32, b AS I32) AS I32
    RETURN a + b
END FUNCTION

SUB Selam(ad AS STRING)
    PRINT "merhaba "; ad
END SUB

CLASS Nokta
    PUBLIC
    DIM x AS I32
    DIM y AS I32
END CLASS
'''


def ast_al(yol_kaynak, klasor):
    cikti = os.path.join(klasor, "ast.json")
    subprocess.run([UXB, "ast", yol_kaynak, "--ast-json-out", cikti, "--out-root", os.path.join(klasor, "r")],
                   capture_output=True, check=True)
    return json.load(open(cikti, encoding="utf-8"))["root"]


def parametreler(dugum):
    return ", ".join(f"{c['value']} AS {c['type']}" for c in dugum["children"] if c["kind"] == "PARAM_DECL")


def donus_tipi(dugum):
    for c in dugum["children"]:
        if c["kind"] == "RETURN_TYPE":
            return c["value"]
    return None


with tempfile.TemporaryDirectory() as klasor:
    yol = os.path.join(klasor, "p.uxb")
    open(yol, "w", encoding="utf-8").write(KAYNAK)
    kok = ast_al(yol, klasor)
    for d in kok["children"]:
        ad = d["value"].capitalize()  # AST ad büyük/küçük harf duyarsız tutar; okunaklılık için baş harf büyütülür
        if d["kind"] == "FUNCTION_STMT":
            print(f"FUNCTION {ad}({parametreler(d)}) AS {donus_tipi(d)}   [satir {d['line']}]")
        elif d["kind"] == "SUB_STMT":
            print(f"SUB {ad}({parametreler(d)})   [satir {d['line']}]")
        elif d["kind"] == "CLASS_STMT":
            alanlar = ", ".join(f"{c['value']} AS {c['children'][0]['value']}" for c in d["children"] if c["kind"] == "CLASS_FIELD")
            print(f"CLASS {ad} {{ {alanlar} }}   [satir {d['line']}]")
