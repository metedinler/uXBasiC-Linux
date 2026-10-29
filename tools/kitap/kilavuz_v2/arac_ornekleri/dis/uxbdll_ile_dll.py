# KONU: uXBasic kodunu DLL ürününe dönüştürmek (uxbdll aracı) ve o DLL'i uXBasic'ten çağırmak
# KOMUTLAR: uxb bld --x64-mode MIR · tools/uxbdll/uxbdll.py · CALL(DLL) · INCLUDE · CLASS · DELETE
# ACIKLAMA: examples/uxbdll/uxoop_module.uxb, iki sınıf (Counter, Dog:Animal) ve dışarıya açılan düz köprü işlevleri içerir. Önce derleyici bu modülü MIR yolundan x64 yapıtlarına (program.asm, obj, bağlama dosyası) derler. Sonra uxbdll aracı, manifestte (uxoop_module.uxdll.json) sayılan işlevleri DLL'e dışa aktarır, bir .def dosyası, bir uXBasic sarmalayıcısı (.bas) ve dışa aktarım denetimi üretir. Son olarak ayrı bir uXBasic programı sarmalayıcıyı INCLUDE eder ve DLL'in içindeki nesneleri (sayaç, köpek) yaratır, kullanır ve yok eder; aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır. Nesneyi yaratan DLL onu serbest bırakmalıdır; bu yüzden dışarıya sınıf değil, create/add/release köprüleri açılır. Bugünkü derleyici rutin etiketlerini uxb_fn_ önekiyle yazdığı için araç manifestindeki iç adlar bu önekle verilir ve build_program açık olmalıdır (G-ARAC-1).
#= sayac = 42
#= kopek = 42
#= modul = 1 1
#= motorlar ayni: evet (AST, MIR, x64)
import json, os, re, shutil, subprocess, sys, tempfile

UXB = os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe"))
KOK = os.getcwd()
RUNTIME_DLL = os.path.join(os.path.dirname(os.path.abspath(UXB)), "uxb_runtime.dll")

UXB_KAYNAK = '''INCLUDE "uxoop_module.bas"
DIM sayac AS U64
DIM kopek AS U64
DIM a AS I32
DIM g AS I32
DIM r AS I32
DIM k AS I32
DIM d AS I32
r = uxoop_module.uxoop_module_init()
sayac = uxoop_module.uxoop_counter_create(10)
a = uxoop_module.uxoop_counter_add(sayac, 32)
g = uxoop_module.uxoop_counter_get(sayac)
PRINT "sayac = "; g
uxoop_module.uxoop_counter_release(sayac)
kopek = uxoop_module.uxoop_dog_create()
k = uxoop_module.uxoop_animal_speak(kopek)
PRINT "kopek = "; k
uxoop_module.uxoop_animal_release(kopek)
d = uxoop_module.uxoop_module_shutdown()
PRINT "modul = "; r; " "; d
'''


def calistir(komut, cwd, env=None):
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=env)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if " = " in s and not s.startswith(("INFO", "WARN"))]


def ileri(yol):
    return yol.replace("\\", "/")


with tempfile.TemporaryDirectory() as klasor:
    # Bugünkü derleyici, hiçbir yerde başvurulmayan ve parametreden kopyalanan bir nesneyi DELETE eden rutinli bir modülü x64'e
    # derlemez ("ADIM25 AST->MIR coverage failed: DELETE_STMT", G-ARAC-4). DLL'de üst düzey deyim hiç çalışmadığı için, rutinlere
    # hiç çalışmayacak koşullu çağrılarla başvuru eklenir.
    kaynak = os.path.join(klasor, "uxoop_module.uxb")
    # Ayrıca modüldeki `PROPERTY value AS I32` (PRIVATE kısa özellik) sınıf içinde çıplak adla alan gibi kullanılınca MIR ve x64'te
    # değer saklamaz (G-NESNE-18); düz `DIM value AS I32` alanıyla değiştirilir.
    orijinal = open(os.path.join(KOK, "examples", "uxbdll", "uxoop_module.uxb"), encoding="utf-8").read()
    orijinal = orijinal.replace("PROPERTY value AS I32", "DIM value AS I32")
    ek = "\nDIM yedekSayac AS Counter = NEW Counter(0)\nIF 1 = 2 THEN UXOOP_COUNTER_RELEASE(yedekSayac)\nDIM yedekHayvan AS Animal = NEW Animal()\nIF 1 = 2 THEN UXOOP_ANIMAL_RELEASE(yedekHayvan)\n"
    open(kaynak, "w", encoding="utf-8").write(orijinal + ek)
    yapi = os.path.join(klasor, "yapi")
    calistir([UXB, "bld", kaynak, "--build-x64", "--x64-mode", "MIR", "--build-x64-out", yapi, "--out-root", os.path.join(klasor, "o")], KOK)
    asm_yolu = os.path.join(yapi, "program.asm")
    if not os.path.exists(asm_yolu):
        print("x64 yapitlari uretilemedi")
        sys.exit(3)
    asm = open(asm_yolu, encoding="utf-8", errors="replace").read()
    etiketler = set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", asm, re.M))

    m = json.load(open(os.path.join(KOK, "examples", "uxbdll", "uxoop_module.uxdll.json"), encoding="utf-8"))
    m["project_root"] = ileri(KOK)
    m["build_dir"] = ileri(yapi)
    m["output_dir"] = ileri(os.path.join(klasor, "dll"))
    m["wrapper_bas"] = ileri(os.path.join(klasor, "uxoop_module.bas"))
    m["wrapper_uxmh"] = ileri(os.path.join(klasor, "uxoop_module.uxmh"))
    m["build_program"] = True
    for e in m["exports"]:
        for aday in (e["internal"], "uxb_fn_" + e["internal"]):
            if aday in etiketler:
                e["internal"] = aday
                break
    manifest = os.path.join(klasor, "uxoop_module.uxdll.json")
    json.dump(m, open(manifest, "w", encoding="utf-8"), indent=1)

    rc, cikti = calistir([sys.executable, os.path.join("tools", "uxbdll", "uxbdll.py"), "--manifest", manifest, "--force", "--run"], KOK)
    if rc != 0 or "PASS DLL build and export audit" not in cikti:
        print("uxbdll basarisiz:", cikti[-400:])
        sys.exit(4)

    for ad in os.listdir(os.path.join(klasor, "dll")):
        shutil.copy(os.path.join(klasor, "dll", ad), klasor)
    open(os.path.join(klasor, "p.uxb"), "w", encoding="utf-8").write(UXB_KAYNAK)

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
    ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 3
    print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
