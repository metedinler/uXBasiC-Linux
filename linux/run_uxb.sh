#!/usr/bin/env bash
# uxbasic'i Linux'ta calistirir: '\' -> '/' yol duzeltmesi (LD_PRELOAD) ile. Calisma dizini cikti (build/) yazar.
# Kullanim: linux/run_uxb.sh <verb> <kaynak> [secenekler]     orn: linux/run_uxb.sh run prog.uxb
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LD_PRELOAD="$ROOT/linux/out/libpathfix.so${LD_PRELOAD:+:$LD_PRELOAD}"
exec "${UXB:-$ROOT/linux/out/uxbasic}" "$@"
