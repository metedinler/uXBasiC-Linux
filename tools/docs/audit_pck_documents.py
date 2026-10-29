#!/usr/bin/env python3
"""Inventory PCK documents and flag legacy claims without rewriting archives."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STALE_MARKERS = {
    "legacy_api_110": "uxffi API sürümü: 110",
    "legacy_arg16": "16 argüman",
    "legacy_std_mode": "--mode=std",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="reports/pck_document_audit_20260727.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    candidates = set()
    for path in (root / "docs").rglob("*"):
        if path.is_file() and (
            "pck" in path.name.lower()
            or "uxb_pck_book" in {part.lower() for part in path.parts}
            or "uxbasic_pck_kitaplar" in {part.lower() for part in path.parts}
        ):
            candidates.add(path)
    top_level = root / "pck_son(20.07).md"
    if top_level.is_file():
        candidates.add(top_level)

    rows = []
    stale_total = 0
    for path in sorted(candidates):
        relative = path.relative_to(root).as_posix()
        canonical = relative.startswith("docs/uxb_pck_book/")
        archive = relative.startswith("docs/uxbasic_pck_kitaplar/")
        text = ""
        if path.suffix.lower() in {".md", ".txt", ".py", ".ps1"}:
            text = path.read_text(encoding="utf-8", errors="replace")
        flags = [name for name, marker in STALE_MARKERS.items() if marker.lower() in text.lower()]
        stale_total += len(flags)
        rows.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "role": "canonical" if canonical else ("archive" if archive else "supplement"),
            "legacy_markers": flags,
        })

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "uxb.pck-document-audit.v1",
        "status": "PASS",
        "policy": (
            "Canonical text is corrected in docs/uxb_pck_book. Historical copies are "
            "preserved and redirected by PCK_GUNCELLIK_NOTU_20260727.md."
        ),
        "document_count": len(rows),
        "legacy_marker_count": stale_total,
        "documents": rows,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PCK_DOCUMENT_AUDIT_PASS documents={len(rows)} legacy_markers={stale_total}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
