#!/usr/bin/env bash
# run_*_tests.ps1 mantiginin bash karsiligi: AST, MIR ve JS (node) motorlari; x64/AST-x64 Linux'ta yoktur.
# Kullanim: linux/run_tests.sh tests/array_params [tests/iterators ...]
# expected/<ad>.txt birebir; <ad>.contains.txt "MOTOR=alt dize" icerme; <ad>.engines.txt motor secimi (varsayilan hepsi).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LD_PRELOAD="$ROOT/linux/out/libpathfix.so"
U="${UXB:-$ROOT/linux/out/uxbasic}"
WORK="$(mktemp -d)"; cd "$WORK"
norm() { grep -vE '^(INFO|WARN)|^sh: .*cmd: not found|^[[:space:]]*$' | sed 's/\r$//'; }
pass=0; fail=0
for dir in "$@"; do
  dir="$(cd "$ROOT/$dir" 2>/dev/null && pwd || echo "$dir")"
  for f in "$dir"/*.uxb; do
    b="$(basename "$f" .uxb)"; exp="$dir/expected/$b.txt"; eng="$dir/expected/$b.engines.txt"; con="$dir/expected/$b.contains.txt"
    engines="AST MIR JS"
    # .ps1 koşucusu JS'i çalıştırmıyorsa (ör. array_params) JS de atlanır
    grep -qs '"JS"' "$dir"/run_*_tests.ps1 || engines="AST MIR"
    [ -f "$eng" ] && engines="$(tr -s '[:space:]' ' ' < "$eng")"
    want="$([ -f "$exp" ] && norm < "$exp")"
    for e in AST MIR JS; do
      case " $engines " in *" $e "*) ;; *) continue;; esac
      case $e in
        AST) out="$(timeout 60 "$U" run "$f" 2>&1 | norm)";;
        MIR) out="$(timeout 60 "$U" run "$f" --interpreter-backend MIR 2>&1 | norm)";;
        JS)  rm -rf js; mkdir js; timeout 60 "$U" jsw "$f" --js-out js/p.js >/dev/null 2>&1
             out="$([ -f js/p.js ] && timeout 30 node js/p.js 2>&1 | norm || echo BUILDFAIL)";;
      esac
      if [ -f "$con" ] && grep -q "^$e=" "$con"; then
        sub="$(grep "^$e=" "$con" | head -1 | cut -d= -f2-)"; case "$out" in *"$sub"*) ok=1;; *) ok=0;; esac
      else [ "$out" = "$want" ] && ok=1 || ok=0; fi
      if [ $ok = 1 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL $(basename "$dir")/$b [$e]"; echo "  beklenen: $(echo "$want"|head -3|tr '\n' '|')"; echo "  alinan:   $(echo "$out"|head -3|tr '\n' '|')"; fi
    done
  done
done
echo "PASS=$pass FAIL=$fail"
rm -rf "$WORK"
