# -*- coding: utf-8 -*-
"""K-06 / S-582 yoklaması: MemoryRef tablosu (4096 yuva) dolunca bayat-işaretçi koruması sessizce kapanıyor mu?

N ayrı dizi (DIM a0(3) AS I32 ... a{N-1}) tanımlar, sonuncunun adresini alır, dizi REDIM edilir ve eski işaretçiyle PEEKD okunur.
Beklenen: «MemoryRef: stale pointer» hatası. N > 4096'da MIR hatasız `11` yazar (koruma kapalı).
Kullanım (depo kökünden):
  python tools/kitap/kilavuz_v2/yoklama/memref_dolu_yoklama.py [ikili] [N ...]
Varsayılan ikili bin/uxb_kilavuz_20261014_0253.exe, varsayılan N: 10 4000 4200 5000 (AST ve MIR; 4000+ dizi için birkaç dakika sürer).
Geçici dosyalar sistem geçici klasörüne yazılır."""
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
UXB = os.path.join(KOK, sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].isdigit() else os.path.join("bin", "uxb_kilavuz_20261014_0253.exe"))
SAYILAR = [int(x) for x in sys.argv[1:] if x.isdigit()] or [10, 4000, 4200, 5000]


def kur(n):
    s = [f"DIM a{i}(3) AS I32" for i in range(n)]
    son = f"a{n - 1}"
    s += ["DIM p AS PTR", f"{son}(0) = 11", f"p = VARPTR({son})", f"REDIM {son}(99) AS I32", "PRINT PEEKD(p)", 'PRINT "unreachable"']
    return "\n".join(s) + "\n"


with tempfile.TemporaryDirectory(prefix="memref_") as d:
    for n in SAYILAR:
        yol = os.path.join(d, f"memref_{n}.uxb")
        open(yol, "w", encoding="utf-8", newline="\r\n").write(kur(n))
        for motor in ("AST", "MIR"):
            k = [UXB, "run", yol, "--out-root", os.path.join(d, "o_" + motor)]
            if motor == "MIR":
                k += ["--interpreter-backend", "MIR"]
            try:
                r = subprocess.run(k, cwd=KOK, capture_output=True, timeout=900, stdin=subprocess.DEVNULL)
                c = [x.strip() for x in (r.stdout + r.stderr).decode("utf-8", "replace").splitlines() if x.strip() and not x.startswith(("INFO", "WARN"))]
                print(f"N={n:5d} {motor:3s} rc={r.returncode} {' | '.join(c[:3])[:160]}")
            except subprocess.TimeoutExpired:
                print(f"N={n:5d} {motor:3s} ZAMAN_ASIMI")
