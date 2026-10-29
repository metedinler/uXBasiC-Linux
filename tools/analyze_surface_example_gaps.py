#!/usr/bin/env python3
"""Compare lexer/preprocessor surfaces with existing executable examples."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = ROOT / "src/parser/lexer/lexer_keyword_table.fbs"
PREPROCESSOR = ROOT / "src/preprocessor"
CORPUS_ROOTS = (ROOT / "tests", ROOT / "docs/uxbasic kitap")
OUT_JSON = ROOT / "reports/surface_example_gaps.json"
OUT_MD = ROOT / "reports/surface_example_gaps.md"


def lexer_keywords() -> set[str]:
    text = KEYWORDS.read_text(encoding="utf-8-sig", errors="replace")
    words: set[str] = set()
    for line in text.splitlines():
        if "Case " not in line:
            continue
        words.update(x.upper() for x in re.findall(r'"([A-Za-z][A-Za-z0-9_]*)"', line))
    return words


def preprocess_commands() -> set[str]:
    words: set[str] = set()
    for path in PREPROCESSOR.rglob("*.fbs"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        words.update(
            x.upper()
            for x in re.findall(r"%%([A-Z][A-Z0-9_]*)", text, re.I)
            if not x.endswith("_")
        )
    return words


def source_files() -> list[Path]:
    result: list[Path] = []
    for base in CORPUS_ROOTS:
        if not base.exists():
            continue
        result.extend(p for p in base.rglob("*") if p.suffix.lower() in {".uxb", ".bas", ".uxm", ".md"})
    return result


def main() -> int:
    kws = lexer_keywords()
    pps = preprocess_commands()
    keyword_hits: dict[str, set[str]] = defaultdict(set)
    pp_hits: dict[str, set[str]] = defaultdict(set)

    for path in source_files():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if path.suffix.lower() == ".md":
            # Prose mentioning a keyword is not an example. Count fenced code only.
            text = "\n".join(re.findall(r"```[^\n]*\n(.*?)```", text, re.S))
        rel = path.relative_to(ROOT).as_posix()
        upper = text.upper()
        for word in set(re.findall(r"\b[A-Z][A-Z0-9_]*\b", upper)):
            if word in kws:
                keyword_hits[word].add(rel)
        for word in set(re.findall(r"%%([A-Z][A-Z0-9_]*)", upper)):
            if word in pps:
                pp_hits[word].add(rel)

    library_test_files: list[Path] = []
    for test_dir in (ROOT / "tests").glob("ux*"):
        if test_dir.is_dir():
            library_test_files.extend(
                p for p in test_dir.rglob("*")
                if p.suffix.lower() in {".uxb", ".bas", ".uxm"}
            )
    test_text = "\n".join(
        p.read_text(encoding="utf-8-sig", errors="replace")
        for p in library_test_files
    )
    generated_dir = ROOT / "tests/library_surface_gaps"
    generated_text = "\n".join(
        p.read_text(encoding="utf-8-sig", errors="replace")
        for p in generated_dir.glob("*_missing_surface.uxb")
    ) if generated_dir.exists() else ""
    libraries: dict[str, dict[str, object]] = {}
    for lib_file in sorted((ROOT / "libsx").glob("ux*/ux*.bas")):
        library = lib_file.parent.name
        declared = {
            name
            for name in re.findall(
                r"(?im)^\s*(?:PUBLIC\s+|PRIVATE\s+)?(?:FUNCTION|SUB)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                lib_file.read_text(encoding="utf-8-sig", errors="replace"),
            )
        }
        covered = {
            name for name in declared
            if re.search(rf"(?i)(?:\b{re.escape(library)}\s*\.\s*)?\b{re.escape(name)}\s*\(", test_text)
        }
        generated_covered = {
            name for name in declared
            if re.search(rf"(?i)\b{re.escape(name)}\s*\(", generated_text)
        }
        effective = covered | generated_covered
        libraries[library] = {
            "source": lib_file.relative_to(ROOT).as_posix(),
            "total": len(declared),
            "covered": len(covered),
            "generated_covered": len(generated_covered - covered),
            "effective_covered": len(effective),
            "missing": sorted(declared - covered),
            "remaining_after_generated": sorted(declared - effective),
        }

    payload = {
        "schema": "uxbasic.surface-example-gap.v1",
        "corpus_roots": [p.relative_to(ROOT).as_posix() for p in CORPUS_ROOTS],
        "lexer": {
            "total": len(kws),
            "covered": len(keyword_hits),
            "missing": sorted(kws - keyword_hits.keys()),
            "examples": {k: sorted(v)[:10] for k, v in sorted(keyword_hits.items())},
        },
        "preprocessor": {
            "total": len(pps),
            "covered": len(pp_hits),
            "missing": sorted(pps - pp_hits.keys()),
            "examples": {k: sorted(v)[:10] for k, v in sorted(pp_hits.items())},
        },
        "libraries": libraries,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# uXBasic lexer/preprocessor örnek boşlukları",
        "",
        "Bu rapor lexer tablosu ve preprocessor kaynaklarından çıkarılmış yüzeyi,",
        "`tests` ile `docs/uxbasic kitap` içindeki mevcut örneklerle karşılaştırır.",
        "",
        f"- Lexer: {len(keyword_hits)}/{len(kws)} öğe örneklerde geçiyor.",
        f"- Preprocessor: {len(pp_hits)}/{len(pps)} komut örneklerde geçiyor.",
        "",
        "## Örneği bulunmayan lexer öğeleri",
        "",
        ", ".join(sorted(kws - keyword_hits.keys())) or "Yok.",
        "",
        "## Örneği bulunmayan preprocess komutları",
        "",
        ", ".join(sorted(pps - pp_hits.keys())) or "Yok.",
        "",
        "Not: Bu bir sözcüksel kapsam ön taramasıdır. Yeni testler parser ve runtime",
        "tarafında ayrıca çalıştırılmalıdır.",
        "",
        "## Kütüphane fonksiyon kapsamı",
        "",
    ]
    for library, row in libraries.items():
        missing = row["remaining_after_generated"]
        lines.append(
            f"- `{library}`: mevcut={row['covered']}, üretilen={row['generated_covered']}, "
            f"toplam={row['effective_covered']}/{row['total']}; "
            f"eksik: {', '.join(missing) if missing else 'yok'}"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"lexer={len(keyword_hits)}/{len(kws)} missing={len(kws-keyword_hits.keys())}")
    print(f"preprocessor={len(pp_hits)}/{len(pps)} missing={len(pps-pp_hits.keys())}")
    print(OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
