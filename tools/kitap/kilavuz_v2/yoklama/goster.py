# -*- coding: utf-8 -*-
"""vaka_kos anlık görüntüsünü vaka başına motor sütunlarıyla özetler:  goster.py dosya.json [süz]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
D = json.load(open(sys.argv[1], encoding="utf-8"))
suz = sys.argv[2] if len(sys.argv) > 2 else ""
print(D["ikili"].split("\\")[-1], D["sha256"][:12], D["zaman"], "vaka:", len(D["vakalar"]))
for k, v in D["vakalar"].items():
    if suz and suz not in k:
        continue
    print("\n##", k.split("::", 1)[1])
    for m in ("AST", "MIR", "x64", "JS"):
        if m not in v:
            continue
        rc, c = v[m]
        c = " | ".join(str(x)[:110] for x in c[:4])
        print(f"  {m:<4} rc={rc!s:<10} {c}")
