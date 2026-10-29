#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yama-2 task AST denetleyicisi.
Bir veya birden fazla ast.json dosyasini birlikte okur.
EVENT/PIPE/THREAD/PARALEL node turlerinin tumunu ayni tek dosyada aramaz;
run_yama2_task_tests.bat tarafindan uretilen tum AST dosyalarini birlikte denetler.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

REQUIRED_KINDS = {"EVENT_STMT", "PIPE_STMT", "THREAD_STMT", "PARALEL_STMT"}

def walk(node: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(node, dict):
        if "kind" in node:
            yield node
        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                yield from walk(child)
        # Bazı eski AST alanlarında left/right doğrudan dict olabilir.
        for side in ("left", "right"):
            val = node.get(side)
            if isinstance(val, dict):
                yield from walk(val)
            elif isinstance(val, list):
                for child in val:
                    yield from walk(child)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)

def load_nodes(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"ERROR: AST JSON okunamadi: {path} :: {exc}")
    root = data.get("root", data)
    return list(walk(root))

def norm(text: Any) -> str:
    return str(text or "").strip().upper()

def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Kullanim: python tools/tests/check_yama2_task_ast_json.py <ast1.json> [ast2.json ...]")
        return 2

    all_nodes: List[Tuple[Path, Dict[str, Any]]] = []
    for arg in argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"ERROR: AST JSON yok: {p}")
            return 2
        for n in load_nodes(p):
            all_nodes.append((p, n))

    kinds: Set[str] = {norm(n.get("kind")) for _, n in all_nodes}
    missing = sorted(REQUIRED_KINDS - kinds)
    if missing:
        print("ERROR: Beklenen task node turleri eksik: " + ", ".join(missing))
        print("Gorulen task node turleri: " + ", ".join(sorted(k for k in kinds if k.endswith("_STMT") or k in REQUIRED_KINDS)))
        return 1

    # Qualified name denetimi: ic ice task testinde en az bir task sembolu nokta tasimali.
    dotted_symbols = []
    for _, n in all_nodes:
        k = norm(n.get("kind"))
        if k in REQUIRED_KINDS:
            sym = str(n.get("symbol") or "").strip()
            if "." in sym:
                dotted_symbols.append(sym)
    if not dotted_symbols:
        print("ERROR: Ic ice task tanimlari icin qualified symbol bulunamadi.")
        return 1

    # PIPE input denetimi: PIPE_STMT altinda PARAM_DECL bulunmali.
    pipe_has_param = False
    for _, n in all_nodes:
        if norm(n.get("kind")) == "PIPE_STMT":
            for child in n.get("children", []) or []:
                if norm(child.get("kind")) == "PARAM_DECL":
                    pipe_has_param = True
                    break
    if not pipe_has_param:
        print("ERROR: PIPE_STMT altinda PARAM_DECL bulunamadi.")
        return 1

    print("OK: Yama-2 task AST denetimi gecti.")
    print("OK: node turleri: " + ", ".join(sorted(REQUIRED_KINDS)))
    print("OK: qualified semboller: " + ", ".join(sorted(set(dotted_symbols))))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
