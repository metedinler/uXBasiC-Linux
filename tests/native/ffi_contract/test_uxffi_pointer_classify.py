#!/usr/bin/env python3
"""S-653: uxffi.dll ayirimi -- gercek adres (VARPTR, heap) ile 32 bitlik tutamac belirteci.

Belirtecler 32 bitliktir (I32/U32 degiskene sigsin diye) ve 0x40000000..0x7FFFFFFF bandini kullanir; ayni bantta
gercek kullanici adresleri de bulunabilir. Eski kural "banttaki her deger belirectir" idi ve gercek bir adresi
"stale or invalid pointer handle token" diye reddederdi. Yeni kural: CANLI belirtec -> belirtec; canli degil ve adres
bellekte ayrilmissa -> gercek isaretci; ne canli ne ayrilmis ama eskiden dagitilmis bir yuvaya uyuyorsa -> bayat.

Kullanim: python test_uxffi_pointer_classify.py --dll <uxffi.dll yolu>   (varsayilan: <kok>\\bin\\uxffi.dll)
"""
from __future__ import annotations
import argparse, ctypes, json, sys
from ctypes import wintypes
from pathlib import Path

VOID, I32, U32, I64, U64, F64, PTR, STRPTR = range(8)
MEM_COMMIT, MEM_RESERVE, PAGE_READWRITE = 0x1000, 0x2000, 0x04


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--dll', default=None)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    dll_path = Path(ns.dll) if ns.dll else root / 'bin' / 'uxffi.dll'
    dll = ctypes.CDLL(str(dll_path))
    invoke = dll.uxffi_invoke10
    invoke.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
                       ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_double),
                       ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_double), ctypes.c_char_p, ctypes.c_int]
    invoke.restype = ctypes.c_int

    def call(dll_name, name, ret, kinds=(), u64=()):
        n = len(kinds)
        ka = (ctypes.c_int * max(1, n))(*list(kinds or [0]))
        ua = (ctypes.c_uint64 * max(1, n))(*list(u64 or [0]))
        fa = (ctypes.c_double * max(1, n))(*([0.0] * max(1, n)))
        ru, rf, err = ctypes.c_uint64(), ctypes.c_double(), ctypes.create_string_buffer(512)
        ok = invoke(dll_name.encode(), name.encode(), ret, n, ka if n else None, ua if n else None, fa if n else None,
                    ctypes.byref(ru), ctypes.byref(rf), err, 512)
        return ok, ru.value, err.value.decode(errors='replace')

    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.VirtualAlloc.restype = ctypes.c_void_p
    k32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]

    # 1) Belirtec bandinda (0x40000000..0x7FFFFFFF) gercek, ayrilmis bir adres ac.
    band = None
    for cand in (0x43000000, 0x44000000, 0x45000000, 0x46000000, 0x47000000, 0x50000000, 0x60000000, 0x70000000):
        got = k32.VirtualAlloc(cand, 65536, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
        if got and 0x40000000 <= got <= 0x7FFFFFFF:
            band = got
            break
    assert band, 'bantta (0x40000000..0x7FFFFFFF) bellek ayrilamadi; testi baska bir kosuda yineleyin'
    # VirtualAlloc tabanlari 64 KB hizalidir (alt 16 bit = 0 = belirtec indeksi 0: zaten belirtec sayilmaz); gercek
    # VARPTR/heap adresleri boyle hizali degildir. Eski kuralin yakaladigi adres: alt 16 bit ve 16..29. bitler sifirdan farkli.
    band += 0x1234
    buf = (ctypes.c_ubyte * 16).from_address(band)

    # gercek adres, bantta olmasina ragmen memset'e ham isaretci olarak gecer
    ok, _, err = call('msvcrt.dll', 'memset', PTR, (PTR, I32, U64), (band, 0x5A, 16))
    assert ok, f'bantta gercek adres reddedildi: {err}'
    assert bytes(buf) == b'\x5a' * 16, 'memset gercek adrese yazmadi'

    # 2) Canli belirtec hala belirtectir: malloc -> belirtec -> memset -> free (belirteci tuketir)
    ok, token, err = call('msvcrt.dll', 'malloc', PTR, (U64,), (32,))
    assert ok and token, err
    assert 0x40000000 <= token <= 0x7FFFFFFF, hex(token)
    ok, _, err = call('msvcrt.dll', 'memset', PTR, (PTR, I32, U64), (token, 0x11, 32))
    assert ok, f'canli belirtec cozulemedi: {err}'
    ok, _, err = call('msvcrt.dll', 'free', VOID, (PTR,), (token,))
    assert ok, err

    # 3) Serbest birakilmis belirtec bayat sayilir (adres bellekte ayrilmadiysa)
    class MBI(ctypes.Structure):
        _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p), ('AllocationProtect', wintypes.DWORD),
                    ('PartitionId', wintypes.WORD), ('RegionSize', ctypes.c_size_t), ('State', wintypes.DWORD),
                    ('Protect', wintypes.DWORD), ('Type', wintypes.DWORD)]
    mbi = MBI()
    k32.VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
    k32.VirtualQuery(token, ctypes.byref(mbi), ctypes.sizeof(mbi))
    stale_checked = False
    if mbi.State != MEM_COMMIT:
        ok, _, err = call('msvcrt.dll', 'memset', PTR, (PTR, I32, U64), (token, 0x22, 32))
        assert not ok and 'stale' in err.lower(), f'bayat belirtec kabul edildi: ok={ok} err={err}'
        stale_checked = True

    print(json.dumps({'marker': 'UXFFI_POINTER_CLASSIFY_PASS', 'dll': str(dll_path), 'band_address': hex(band),
                      'token': hex(token), 'stale_checked': stale_checked}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
