#!/usr/bin/env bash
# uXBasic Linux derleme betigi (FreeBASIC Linux surumu + kernel32 shim).
# Kullanim:  linux/build_linux.sh [cikti_yolu]
# Ortam:     FBC_PREFIX  FreeBASIC kurulum dizini (bin/, lib/, include/ icerir). fbc PATH'te ise gerekmez.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/linux/out/uxbasic}"
SHIM_DIR="$ROOT/linux/out/shim"
mkdir -p "$SHIM_DIR" "$(dirname "$OUT")"

FBC=fbc
PFX=()
if [ -n "${FBC_PREFIX:-}" ]; then FBC="$FBC_PREFIX/bin/fbc"; PFX=(-prefix "$FBC_PREFIX"); fi
command -v "$FBC" >/dev/null || { echo "fbc bulunamadi (FBC_PREFIX ayarlayin)"; exit 1; }

# 1) Windows kernel32 -> dlopen/dlsym shim (yalniz LoadLibraryA, GetProcAddress, FreeLibrary, GetModuleFileNameA)
gcc -c -fPIC "$ROOT/linux/shim/kernel32_shim.c" -o "$SHIM_DIR/k32.o"
ar rcs "$SHIM_DIR/libkernel32.a" "$SHIM_DIR/k32.o"
cp "$SHIM_DIR/libkernel32.a" "$SHIM_DIR/libkernel32.dll.a"   # bazi bildirimler -lkernel32.dll ister

# 2) Derleyici (uzun surer, ~15-20 dk). fbc src/main.c ve src/main.asm ara dosyalarini birakir.
cd "$ROOT"
# Once nesneye derle (-c -m main), baglama hatasinda 17 dk tekrar harcanmasin diye main.o korunur.
"$FBC" "${PFX[@]}" -m main -c src/main.bas -o "$ROOT/linux/out/main.o"
"$FBC" "${PFX[@]}" -m main -p "$SHIM_DIR" -l dl "$ROOT/linux/out/main.o" -x "$OUT"
rm -f src/main.c src/main.asm
echo "tamam: $OUT"
