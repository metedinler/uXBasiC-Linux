# -*- coding: utf-8 -*-
"""uxb_dead_code_scan.py -- FreeBASIC kaynak agacinda "tohum" dosyadan baslayarak yalniz olu koda bagli dosyalari bulur.

Amac : Bir dosya cagrilmiyorsa (tohum), ona bagli olup BASKA HICBIR canli kod tarafindan kullanilmayan dosyalari kanitla
       (sembol duzeyinde cagri grafi, sabit noktaya kadar). Tasima/silme karari icin DOGRULAMA aracidir; dosyaya yazmaz.
Girdi: --seed src/backend/backend_pipeline.fbs  (birden fazla verilebilir)   --root <depo koku, varsayilan cwd>
Cikti: stdout raporu (olu dosya kumesi, her dosya icin kanit, canli kalanlar ve nedenleri, include eden dosyalar,
       betik/belge adlari). --json yol verilirse ayni bilgi JSON.
Yontem: FreeBASIC buyuk/kucuk harf duyarsiz. Yorum ve metin sabitleri atilir. Ad -> tanimlayan dosya ve her ad icin
       kullanan dosyalar cikarilir. Bir dosya, tanimladigi HER adin kullanicilari (Declare satirlari haric) olu kume ya da
       kendisi icindeyse olu sayilir. Yalniz tohumun bagimliliklari (include ettigi ya da adini kullandigi dosyalar)
       aday olur; boylece ilgisiz yetim dosyalar karismaz.
Sinir : Ad temelli (bir ad baska anlamda baska dosyada gecerse "canli" sayilir: muhafazakar). Ust duzey calisan deyimler
       "uyari" olarak listelenir; elle bakilmali. Makro ile uretilen adlar ve dinamik ad olusturma bulunamaz.
Ornek : python tools/maintenance/uxb_dead_code_scan.py --seed src/backend/backend_pipeline.fbs --skip uxbasic_hamle3
Secenekler: --seed DOSYA (zorunlu, tekrarlanir)  --root KOK  --src KLASOR (src)  --also KLASOR... (tests compiler tools; canli kullanici
       sayilan ek klasorler)  --skip PARCA (yolunda parca gecen dosyalari atlar; arsiv yama klasorleri icin)  --json YOL
Cikis kodu: 1 = olu kumenin bir adi olu kume disindan kullaniliyor (tasima guvenli degil), 0 = temiz.
"""
import argparse, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
EXT = (".fbs", ".bas", ".bi")
SKIP_DIRS = {"_retired", "out", ".git", "node_modules"}
RE_ROUTINE = re.compile(r"^\s*(?:private\s+|public\s+)?(?:static\s+)?(function|sub|property)\s+([a-z_]\w*)", re.I)
RE_DECLARE = re.compile(r"^\s*declare\s+(?:function|sub|property)\s+([a-z_]\w*)", re.I)
RE_END_ROUTINE = re.compile(r"^\s*end\s+(function|sub|property)\b", re.I)
RE_TYPE = re.compile(r"^\s*type\s+([a-z_]\w*)", re.I)
RE_END_TYPE = re.compile(r"^\s*end\s+type\b", re.I)
RE_ENUM = re.compile(r"^\s*enum\s*([a-z_]\w*)?", re.I)
RE_END_ENUM = re.compile(r"^\s*end\s+enum\b", re.I)
RE_CONST = re.compile(r"^\s*(?:private\s+|public\s+)?const\s+([a-z_]\w*)", re.I)
RE_SHARED = re.compile(r"^\s*(?:private\s+|public\s+)?dim\s+shared\s+(?:as\s+[\w\s]+?\s+)?([a-z_]\w*)", re.I)
RE_DEFINE = re.compile(r"^\s*#\s*(?:define|macro)\s+([a-z_]\w*)", re.I)
RE_INCLUDE = re.compile(r'^\s*#\s*include\s+(?:once\s+)?"([^"]+)"', re.I)
RE_TOKEN = re.compile(r"[A-Za-z_]\w*")
KEYWORD_OK_TOP = ("#", "declare", "dim shared", "private dim shared", "const", "private const", "type", "end type", "enum",
                  "end enum", "extern", "end extern", "union", "end union", "public", "private", "function", "sub",
                  "property", "static function", "static sub", "end function", "end sub", "end property", "randomize")


def strip_line(s):
    out, i, q = [], 0, False
    while i < len(s):
        c = s[i]
        if q:
            if c == '"':
                if i + 1 < len(s) and s[i + 1] == '"':
                    i += 1
                else:
                    q = False
        elif c == '"':
            q = True
        elif c == "'":
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def walk_sources(root, dirs):
    for d in dirs:
        base = os.path.join(root, d)
        if os.path.isfile(base):
            yield base
            continue
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x.lower() not in SKIP_DIRS]
            for f in fn:
                if f.lower().endswith(EXT):
                    yield os.path.join(dp, f)


def parse(path):
    """-> dict(defs={ad:[satir]}, refs={ad:set(sahip)}, includes=[yol], top=[satir], text)"""
    info = {"defs": {}, "refs": {}, "includes": [], "top": [], "lines": 0}
    try:
        raw = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return info
    info["lines"] = len(raw)
    owner, in_type, in_enum, cont = None, False, False, False
    for no, line in enumerate(raw, 1):
        code = strip_line(line)
        if cont:                       # onceki satirin devami: tanim satiri sayilmaz, yalniz basvuru
            cont = code.rstrip().endswith(" _")
            for t in RE_TOKEN.findall(code):
                info["refs"].setdefault(t.lower(), set()).add(owner or "<ust>")
            continue
        cont = code.rstrip().endswith(" _")
        s = code.strip()
        m = RE_INCLUDE.match(line)
        if m:
            info["includes"].append(m.group(1))
            continue
        defname = None
        if not in_type and not in_enum and owner is None:
            m = RE_DECLARE.match(code)
            if m:
                info["decl"] = info.get("decl", set()) | {m.group(1).lower()}
                continue
        if owner is None and not in_type and not in_enum:
            m = RE_ROUTINE.match(code)
            if m:
                defname = m.group(2).lower(); owner = defname
            else:
                m = RE_TYPE.match(code)
                if m and not RE_END_TYPE.match(code):
                    defname = m.group(1).lower(); in_type = True
                else:
                    m = RE_ENUM.match(code)
                    if m and not RE_END_ENUM.match(code) and s.lower().startswith("enum"):
                        defname = (m.group(1) or "").lower() or None; in_enum = True
                    else:
                        for rx in (RE_CONST, RE_SHARED, RE_DEFINE):
                            m = rx.match(code)
                            if m:
                                defname = m.group(1).lower(); break
        elif in_enum and s and not RE_END_ENUM.match(code):
            first = RE_TOKEN.findall(code)
            if first:
                info["defs"].setdefault(first[0].lower(), []).append(no)
        if defname:
            info["defs"].setdefault(defname, []).append(no)
        toks = [t.lower() for t in RE_TOKEN.findall(code)]
        for t in toks:
            if t == defname:
                continue
            info["refs"].setdefault(t, set()).add(owner or ("<tip>" if in_type else "<ust>"))
        if RE_END_ROUTINE.match(code):
            owner = None
        if RE_END_TYPE.match(code):
            in_type = False
        if RE_END_ENUM.match(code):
            in_enum = False
        low = s.lower()
        if owner is None and not in_type and not in_enum and s and defname is None and not low.startswith(KEYWORD_OK_TOP) \
                and not RE_END_ROUTINE.match(code):
            info["top"].append((no, s[:90]))
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", action="append", required=True, help="tohum dosya (kokten goreli); tekrar edilebilir")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--src", default="src", help="ana kaynak klasoru (varsayilan src)")
    ap.add_argument("--also", nargs="*", default=["tests", "compiler", "tools"], help="canli kullanici sayilan ek klasorler")
    ap.add_argument("--json", help="sonucu JSON olarak yaz")
    ap.add_argument("--skip", action="append", default=[], help="yolunda bu parca gecen dosyalari atla (arsiv yama klasorleri); tekrar edilebilir")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    rel = lambda p: os.path.relpath(p, root).replace("\\", "/")
    skipped = lambda p: any(s.lower() in rel(p).lower() for s in a.skip)
    files = {rel(p): parse(p) for p in walk_sources(root, [a.src]) if not skipped(p)}
    extra = {rel(p): parse(p) for p in walk_sources(root, [d for d in a.also if os.path.exists(os.path.join(root, d))]) if not skipped(p)}
    seeds = [s.replace("\\", "/") for s in a.seed]
    for s in seeds:
        if s not in files:
            sys.exit(f"tohum bulunamadi: {s}")
    definers = {}
    for f, inf in files.items():
        for ad in inf["defs"]:
            definers.setdefault(ad, set()).add(f)
    users = {}                         # ad -> {dosya}
    for f, inf in list(files.items()) + list(extra.items()):
        for ad, owners in inf["refs"].items():
            users.setdefault(ad, set()).add(f)

    def resolve_inc(f, inc):
        p = os.path.normpath(os.path.join(os.path.dirname(f), inc)).replace("\\", "/")
        return p if p in files else None

    dead, why = set(seeds), {s: "tohum (cagrilmiyor)" for s in seeds}
    live_reason = {}
    changed = True
    while changed:
        changed = False
        deps = set()
        for f in dead:
            inf = files[f]
            for inc in inf["includes"]:
                r = resolve_inc(f, inc)
                if r:
                    deps.add(r)
            for ad in inf["refs"]:
                for d in definers.get(ad, ()):
                    deps.add(d)
        for c in sorted(deps - dead):
            inf = files[c]
            if not inf["defs"]:
                live_reason[c] = ["tanim yok (yalniz include/deyim); elle bak"]
                continue
            blockers = []
            for ad in inf["defs"]:
                if len(definers.get(ad, ())) > 1:
                    pass
                for u in sorted(users.get(ad, ())):
                    if u != c and u not in dead:
                        blockers.append(f"{ad} <- {u}")
            if blockers:
                live_reason[c] = blockers
            else:
                dead.add(c); why[c] = "tum adlarinin kullanicilari olu kume icinde"; changed = True
                live_reason.pop(c, None)
    # --- rapor
    rep = {"seeds": seeds, "dead": {}, "live_dependencies": {}, "includers": {}, "name_refs_outside": {}}
    print("== OLU KUME (tasima adayi) ==")
    for f in sorted(dead):
        inf = files[f]
        rep["dead"][f] = {"neden": why[f], "satir": inf["lines"], "ad_sayisi": len(inf["defs"]), "ust_duzey_deyim": inf["top"][:5]}
        print(f"  {f}  ({inf['lines']} satir, {len(inf['defs'])} ad)  [{why[f]}]")
        for no, t in inf["top"][:5]:
            print(f"      UYARI ust duzey deyim satir {no}: {t}")
    print("\n== CANLI KALANLAR (olu kumeye bagli ama baska canli kullanicisi var) ==")
    for f in sorted(live_reason):
        rep["live_dependencies"][f] = live_reason[f][:8]
        print(f"  {f}")
        for b in live_reason[f][:8]:
            print(f"      {b}")
    print("\n== INCLUDE EDENLER (duzenlenecek dosyalar) ==")
    for f, inf in list(files.items()) + list(extra.items()):
        for inc in inf["includes"]:
            r = resolve_inc(f, inc) if f in files else None
            if r is None:                # ek klasorlerde: dosya adina gore
                b = os.path.basename(inc).lower()
                r = next((d for d in dead if os.path.basename(d).lower() == b), None)
            if r in dead and f not in dead:
                rep["includers"].setdefault(f, []).append(inc)
    for f in sorted(rep["includers"]):
        print(f"  {f}: " + ", ".join(rep["includers"][f]))
    if not rep["includers"]:
        print("  (yok)")
    # Dolayli include tehlikesi: olu dosyanin getirdigi canli dosyanin baska include edeni kalmazsa tasimadan sonra pakete girmez.
    inc_by = {}
    for f, inf in files.items():
        for inc in inf["includes"]:
            r = resolve_inc(f, inc)
            if r:
                inc_by.setdefault(r, set()).add(f)
    hazards = {}
    for f in sorted(dead):
        for inc in files[f]["includes"]:
            r = resolve_inc(f, inc)
            if r and r not in dead and not (inc_by.get(r, set()) - dead):
                hazards.setdefault(r, []).append(f)
    rep["orphaned_includes"] = hazards
    print("\n== DOLAYLI INCLUDE TEHLIKESI (olu dosyanin getirdigi, baska include edeni KALMAYACAK dosyalar) ==")
    for r in sorted(hazards):
        print(f"  {r}  <- {', '.join(hazards[r])}   => tasimadan sonra paketlere DOGRUDAN include edilmeli")
    if not hazards:
        print("  (yok)")
    # Sira uyarisi: "include once" ilk konumda yukler; olu dosya bir dosyayi ilk kez yukluyor olabilir. Bu, bir dosya ya da
    # ona bagli dosyalar sirasi varsayiyorsa (ileri bildirim yoksa) derlemeyi kirar (S-688'de js/wasm/x64 boyle kirildi).
    order = {}
    for f in sorted(dead):
        for inc in files[f]["includes"]:
            r = resolve_inc(f, inc)
            if r and r not in dead and (inc_by.get(r, set()) - dead):
                order.setdefault(r, []).append(f)
    rep["order_warnings"] = order
    print("\n== INCLUDE SIRASI UYARISI (olu dosyanin getirdigi, baska include edeni de olan dosyalar) ==")
    print("  Tasimadan sonra bu dosyalarin ILK yuklenme konumu degisebilir; derleme ile dogrulayin, gerekirse eski konumda dogrudan include edin.")
    for r in sorted(order):
        print(f"  {r}  <- {', '.join(order[r])}   (diger include edenler: {', '.join(sorted(inc_by[r] - dead))[:140]})")
    if not order:
        print("  (yok)")
    print("\n== OLU KUMENIN ADLARINI KULLANAN CANLI KOD (olmamali) ==")
    bad = 0
    for f in sorted(dead):
        for ad in files[f]["defs"]:
            outside = sorted(u for u in users.get(ad, ()) if u not in dead and u != f)
            if outside:
                bad += 1; rep["name_refs_outside"][f"{f}:{ad}"] = outside
                print(f"  {ad} ({f}) <- {', '.join(outside[:4])}")
    if not bad:
        print("  (yok)")
    # betik/belge adlari
    names = {os.path.basename(f).lower() for f in dead}
    name_rx = {n: re.compile(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])") for n in names}   # kelime siniri: x64_codegen.fbs != mir_x64_codegen.fbs
    hits = []
    for d in ("compiler", "tools", "tests", "tool_py", "."):
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        walker = os.walk(base) if d != "." else [(root, [], os.listdir(root))]
        for dp, dn, fn in walker:
            dn[:] = [x for x in dn if x.lower() not in SKIP_DIRS and x.lower() not in {"out", "reports", "build", "bin", "dist"}]
            for f in fn:
                if f.lower().endswith((".ps1", ".bat", ".cmd", ".py", ".json", ".csv", ".txt")):
                    p = os.path.join(dp, f)
                    try:
                        if os.path.getsize(p) > 2_000_000:
                            continue
                        t = open(p, encoding="utf-8", errors="replace").read().lower()
                    except OSError:
                        continue
                    for n in names:
                        if name_rx[n].search(t):
                            hits.append((rel(p), n))
    rep["script_mentions"] = hits
    print("\n== BETIK/VERI DOSYALARINDA ADLARI GECEN (elle bak) ==")
    for p, n in hits[:40]:
        print(f"  {p}: {n}")
    if not hits:
        print("  (yok)")
    if a.json:
        json.dump(rep, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=list)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
