# -*- coding: utf-8 -*-
"""uXBasic dil yüzeyi tarayıcısı (kitaplar için ortak "gerçek kaynak").

`uxb mtx` matrisleri eksik/tek dosya ürettiği için yüzey DOĞRUDAN kaynaktan çıkarılır:
her katmandaki `Case "AD", ...` satırları ve `x = "AD"` karşılaştırmaları toplanır; bir adın hangi
katmanda (lexer, parser, AST yorumlayıcı, MIR yorumlayıcı, native x64, legacy x64, JS, WASM) geçtiği tabloya dökülür.
"Geçiyor" = o katmanın kaynağında adla eşleşen bir dal var (davranışın doğru olduğu ayrıca testle doğrulanır).

Çıktı: docs/kitaplar/_ortak/dil_yuzeyi.json, dil_yuzeyi.md, dil_yuzeyi.tsv
Kullanım: python tools/kitap/yuzey_tara.py
"""
import json
import os
import re
from collections import defaultdict

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(KOK, "src")
CIKTI = os.path.join(KOK, "docs", "kitaplar", "_ortak")

# katman -> yol desenleri (src'ye göre, '/' ile)
KATMAN = [
    ("lexer", [r"^parser/lexer/"]),
    ("parser", [r"^parser/(?!lexer/)"]),
    ("semantik", [r"^semantic/(?!semantic_to_canonical)", r"^mir/"]),
    ("ast_yorum", [r"^runtime/exec/", r"^interpreter/ast/", r"^runtime/[^/]+\.fbs$"]),
    ("mir_yorum", [r"^interpreter/mir/", r"^semantic/semantic_to_canonical"]),
    ("native_x64", [r"^codegen/x64/mir_x64", r"^codegen/x64/runtime/"]),
    ("legacy_x64", [r"^codegen/x64/(?!mir_x64|runtime/)"]),
    ("js", [r"^codegen/js/"]),
    ("wasm", [r"^codegen/wasm/"]),
    ("yuzey_kaydi", [r"^surface/"]),
]
# sözleşme/yüzey tablosu dosyaları davranış değil beyan içerir: ayrı sayılır
BEYAN = re.compile(r"(surface_contract|keyword_surface|capability|_registry|contract)\.fbs$")

AD = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*\$?)"')
CASE = re.compile(r'(?i)^\s*case\s+(.+)$')
KARS = re.compile(r'(?i)(?:=|<>)\s*"([A-Za-z_][A-Za-z0-9_]*\$?)"')
YORUM = re.compile(r"'.*$")


def katman_bul(rel):
    for ad, desen in KATMAN:
        if any(re.search(d, rel) for d in desen):
            return ad
    return None


def dosyalar():
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            if f.lower().endswith((".fbs", ".bas", ".bi")):
                p = os.path.join(dp, f)
                yield p, os.path.relpath(p, SRC).replace("\\", "/")


def satir_adlari(s):
    s2 = s.split("'", 1)[0] if s.count('"') % 2 == 0 else s
    m = CASE.match(s2)
    if m:
        return AD.findall(m.group(1))
    return KARS.findall(s2)


# lexer anahtar kelimeleri (IsKeyword) ayrı ve kesin liste
def lexer_anahtar():
    p = os.path.join(SRC, "parser", "lexer", "lexer_keyword_table.fbs")
    t = open(p, encoding="utf-8", errors="replace").read()
    return {a.upper() for a in AD.findall(t)}


GURULTU = re.compile(r"^(?:[A-Z]|OK|FAIL|PASS|TRUE_|NULL_|E|X|Y|N|ID|ERR|TMP|TEMP)$")
# derleyicinin iç düğüm/opcode adları (kullanıcı yazmaz) -> sistem programlama kitabına ayrı bölüm
IC_AD = re.compile(r"^(MIR_|OP_|RT_|UXB_|AST_|HIR_|X64_|JS_|WASM_|MODE_|PRINT_SEP|MAGIC_)|"
                   r"_(STMT|DECL|EXPR|PART|BEGIN|END|ITEM|ITEMS|BODY|LIST|REF|NODE|INIT|TARGET|ARGS|ASSIGN|SEQUENCE)$")


IC_OPCODE = re.compile(r"^(LOAD|STORE|JMP|JZ|JNZ|BR|BR_IF|RET|MOV|NOP|R\d+|RAX|RBX|RCX|RDX|RSI|RDI|RSP|RBP|"
                       r"FADD|FSUB|FMUL|FDIV|FNEG|IDIV|UIDIV|UMOD|USHR|UGE|UGT|ULE|ULT|LNOT|NEG|EQ|NE|LT|LE|GT|GE|"
                       r"CALL_[A-Z_]+|LOCK_[A-Z_]+|SYNC_[A-Z_]+|SLOT_BIND[A-Z_]*|CLASS_[A-Z_]+|TYPE_F\d+|"
                       r"(LOAD|STORE|FIELD|ARRAY|MEM|MEMORY|STR|OBJECT|DICT|LIST|SET|TASK|TASK_GROUP|MUTEX)_[A-Z_]+)$")


def uxb_kullanim():
    """tests/ ve örnek klasörlerindeki .uxb programlarında her kelimenin kaç DOSYADA geçtiği."""
    say = defaultdict(int)
    kel = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\$?")
    for alt in ("tests", "examples", "ornekler", "samples", "libsx"):
        kok = os.path.join(KOK, alt)
        for dp, dn, fn in os.walk(kok):
            for f in fn:
                if not f.lower().endswith((".uxb", ".bas")) or f.lower().endswith(".fbs"):
                    continue
                try:
                    t = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                t = "\n".join(s.split("'", 1)[0] for s in t.splitlines() if not s.lstrip().upper().startswith("REM"))
                for w in {w.upper() for w in kel.findall(t)}:
                    say[w] += 1
    return say


def main():
    oz = defaultdict(lambda: defaultdict(set))   # AD -> katman -> {dosya:satır}
    beyan = defaultdict(set)
    for p, rel in dosyalar():
        k = katman_bul(rel)
        if not k:
            continue
        try:
            satirlar = open(p, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for i, s in enumerate(satirlar, 1):
            if '"' not in s:
                continue
            for a in satir_adlari(s):
                A = a.upper()
                if len(A) < 2 or GURULTU.match(A) or A.startswith("__"):
                    continue
                if BEYAN.search(rel):
                    beyan[A].add(f"{rel}:{i}")
                else:
                    oz[A][k].add(f"{rel}:{i}")
    lex = lexer_anahtar()
    kullanim = uxb_kullanim()
    motor = ["ast_yorum", "mir_yorum", "native_x64", "legacy_x64", "js", "wasm"]
    tum = sorted(set(oz) | lex | set(beyan))
    kayit = []
    for A in tum:
        katmanlar = {k: sorted(v)[:6] for k, v in oz.get(A, {}).items()}
        # kullanıcı adı: lexer anahtarı, ya da parser/AST yorumlayıcı onu adıyla tanıyor ve iç ad desenine uymuyor
        on_yuz = "parser" in katmanlar or "ast_yorum" in katmanlar
        ic = A not in lex and (bool(IC_AD.search(A)) or bool(IC_OPCODE.match(A)) or not on_yuz)
        kayit.append({
            "ad": A,
            "anahtar_kelime": A in lex,
            "sinif": "ic" if ic else ("anahtar" if A in lex else "yerlesik"),
            "katmanlar": katmanlar,
            "beyan": sorted(beyan.get(A, []))[:6],
            "motor_sayisi": sum(1 for m in motor if m in katmanlar),
            "uxb_dosya": kullanim.get(A, 0),
        })
    # yalnız dil yüzeyiyle ilgili olanlar: anahtar kelime, ya da en az bir motor + parser/semantik/beyan
    ilgili = [r for r in kayit if r["anahtar_kelime"] or (r["motor_sayisi"] >= 2) or
              (r["motor_sayisi"] >= 1 and (r["beyan"] or "parser" in r["katmanlar"]))]
    os.makedirs(CIKTI, exist_ok=True)
    json.dump(ilgili, open(os.path.join(CIKTI, "dil_yuzeyi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kol = ["lexer", "parser", "semantik", "ast_yorum", "mir_yorum", "native_x64", "legacy_x64", "js", "wasm"]
    with open(os.path.join(CIKTI, "dil_yuzeyi.tsv"), "w", encoding="utf-8") as f:
        f.write("ad\tsinif\tuxb_dosya\t" + "\t".join(kol) + "\tbeyan\n")
        for r in ilgili:
            f.write(r["ad"] + "\t" + r["sinif"] + "\t" + str(r["uxb_dosya"]) + "\t" +
                    "\t".join("+" if k in r["katmanlar"] or (k == "lexer" and r["anahtar_kelime"]) else "" for k in kol) +
                    "\t" + ("+" if r["beyan"] else "") + "\n")
    kisa = {"lexer": "Lx", "parser": "Pr", "semantik": "Sm", "ast_yorum": "AST", "mir_yorum": "MIR",
            "native_x64": "x64", "legacy_x64": "Lg", "js": "JS", "wasm": "WA"}
    def tablo(satirlar):
        T = ["| Ad | Test/örnek dosya | " + " | ".join(kisa[k] for k in kol) + " | Beyan |",
             "|---|---|" + "---|" * len(kol) + "---|"]
        for r in satirlar:
            T.append(f"| `{r['ad']}` | {r['uxb_dosya'] or ''} | " +
                     " | ".join("✓" if k in r["katmanlar"] or (k == "lexer" and r["anahtar_kelime"]) else "" for k in kol) +
                     f" | {'✓' if r['beyan'] else ''} |")
        return T

    gruplar = [
        ("anahtar", "1. Anahtar kelimeler (lexer `IsKeyword`)"),
        ("yerlesik", "2. Yerleşik fonksiyonlar / komutlar / seçenekler (anahtar kelime olmayan, katmanlarda dalı olan)"),
        ("ic", "3. Derleyici iç adları (AST düğümü, MIR opcode, runtime çağrısı — kullanıcı yazmaz; sistem kitabı için)"),
    ]
    L = ["# uXBasic dil yüzeyi — kaynaktan otomatik tarama\n",
         "`tools/kitap/yuzey_tara.py` üretir (`uxb mtx` matrisleri eksik olduğu için). Hücrede ✓ = o katmanın kaynağında "
         "bu adla eşleşen dal var (`Case \"AD\"` ya da `= \"AD\"`). **Beyan** = sözleşme/yüzey tablosunda geçiyor. "
         "**Test/örnek dosya** = `tests/`, `examples/`, `libsx/` altındaki kaç .uxb/.bas programında geçtiği "
         "(0 ise hiç denenmemiş olabilir). Davranış doğruluğu ayrıca `uxb_run3.ps1` ile test edilir.\n",
         "Katmanlar: Lx lexer · Pr parser · Sm semantik · AST AST yorumlayıcı · MIR MIR yorumlayıcı · "
         "x64 native (MIR→x64) · Lg legacy AST-x64 · JS · WA WASM\n",
         "| Sınıf | Ad | 4 motorun hepsinde (AST+MIR+x64+Lg) | Hiç testte yok |", "|---|---|---|---|"]
    for g, bas in gruplar:
        s = [r for r in ilgili if r["sinif"] == g]
        L.append(f"| {bas.split(' (')[0]} | {len(s)} | "
                 f"{sum(1 for r in s if all(m in r['katmanlar'] for m in motor[:4]))} | "
                 f"{sum(1 for r in s if not r['uxb_dosya'])} |")
    for g, bas in gruplar:
        L += ["", f"## {bas}", ""] + tablo([r for r in ilgili if r["sinif"] == g])
    open(os.path.join(CIKTI, "dil_yuzeyi.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"ad {len(ilgili)} (ham {len(kayit)}), anahtar {len(lex)}")
    for g, _ in gruplar:
        s = [r for r in ilgili if r["sinif"] == g]
        print(f"  {g:9} {len(s):4}  4motor {sum(1 for r in s if all(m in r['katmanlar'] for m in motor[:4])):4}"
              f"  testsiz {sum(1 for r in s if not r['uxb_dosya']):4}")
    for m in motor:
        print(f"  {m:11} {sum(1 for r in ilgili if m in r['katmanlar'])}")


IMZA = re.compile(r"(?i)^\s*(?:public\s+|private\s+)?(function|sub)\s+([A-Za-z_][A-Za-z0-9_]*\$?)\s*(\([^)]*\))?\s*(?:as\s+([A-Za-z0-9_]+))?")
NS = re.compile(r"(?i)^\s*namespace\s+([A-Za-z_][A-Za-z0-9_.]*)")
KONST = re.compile(r"(?i)^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)")


def kutuphaneler():
    """libsx/<kütüphane>/*.bas: namespace, fonksiyon/sub imzaları, sabitler; testlerde çağrılıyor mu."""
    lib = os.path.join(KOK, "libsx")
    tm = set()   # testlerde geçen (noktalı) adlar
    noktali = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\$?")
    for alt in ("tests", "examples"):
        for dp, dn, fn in os.walk(os.path.join(KOK, alt)):
            for f in fn:
                if f.lower().endswith((".uxb", ".bas")):
                    try:
                        tm.update(w.upper() for w in noktali.findall(open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()))
                    except OSError:
                        pass
    sonuc = []
    for ad in sorted(os.listdir(lib)):
        d = os.path.join(lib, ad)
        if not os.path.isdir(d):
            continue
        fonk, sabit, nsler, dosya = [], 0, set(), []
        for dp, dn, fn in os.walk(d):
            for f in fn:
                if not f.lower().endswith((".bas", ".uxb")):
                    continue
                p = os.path.join(dp, f)
                dosya.append(os.path.relpath(p, KOK).replace("\\", "/"))
                ns = ""
                for i, s in enumerate(open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
                    m = NS.match(s)
                    if m:
                        ns = m.group(1)
                        nsler.add(ns)
                        continue
                    if KONST.match(s):
                        sabit += 1
                        continue
                    m = IMZA.match(s)
                    if m:
                        tam = (ns + "." if ns else "") + m.group(2)
                        fonk.append({"ad": tam, "tur": m.group(1).upper(), "param": (m.group(3) or "()").strip(),
                                     "donus": (m.group(4) or "").upper(), "yer": f"{os.path.relpath(p, KOK).replace(chr(92), '/')}:{i}",
                                     "testte": tam.upper() in tm})
        sonuc.append({"kutuphane": ad, "namespace": sorted(nsler), "dosya": dosya, "sabit": sabit, "fonksiyon": fonk})
    return sonuc


def kutuphane_raporu():
    K = kutuphaneler()
    json.dump(K, open(os.path.join(CIKTI, "kutuphane_yuzeyi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = ["# uXBasic kütüphane yüzeyi (libsx) — kaynaktan otomatik tarama\n",
         "`tools/kitap/yuzey_tara.py` üretir. **Testte** = fonksiyonun tam adı (`namespace.Ad`) `tests/` ya da `examples/` "
         "altındaki bir programda geçiyor.\n",
         "| Kütüphane | Namespace | Fonksiyon | Sub | Sabit | Testte çağrılan |", "|---|---|---|---|---|---|"]
    for k in K:
        f = k["fonksiyon"]
        L.append(f"| {k['kutuphane']} | {', '.join(k['namespace'])} | {sum(1 for x in f if x['tur'] == 'FUNCTION')} | "
                 f"{sum(1 for x in f if x['tur'] == 'SUB')} | {k['sabit']} | {sum(1 for x in f if x['testte'])}/{len(f)} |")
    toplam = sum(len(k["fonksiyon"]) for k in K)
    L.insert(2, f"Toplam: **{len(K)} kütüphane, {toplam} fonksiyon/sub, {sum(k['sabit'] for k in K)} sabit**; "
                f"testte çağrılan: **{sum(1 for k in K for x in k['fonksiyon'] if x['testte'])}**\n")
    for k in K:
        if not k["fonksiyon"]:
            continue
        L += ["", f"## {k['kutuphane']}", "", "| Ad | Parametreler | Dönüş | Testte | Yer |", "|---|---|---|---|---|"]
        for x in k["fonksiyon"]:
            L.append(f"| `{x['ad']}` | `{x['param']}` | {x['donus']} | {'✓' if x['testte'] else ''} | `{x['yer']}` |")
    open(os.path.join(CIKTI, "kutuphane_yuzeyi.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"kütüphane {len(K)}, fonksiyon/sub {toplam}, testte {sum(1 for k in K for x in k['fonksiyon'] if x['testte'])}")


if __name__ == "__main__":
    main()
    kutuphane_raporu()
