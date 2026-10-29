"""Offline, hash-deduplicated document search; uses only Python's standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "context_index"
DB = OUT / "documents.sqlite3"


def connect():
    OUT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, hash TEXT, bytes INTEGER);
        CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, hash TEXT, path TEXT,
            start INTEGER, end INTEGER, heading TEXT, body TEXT);
        CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(
            heading, body, content='chunks', content_rowid='id', tokenize='unicode61');
    """)
    return db


def paths():
    result = set(ROOT.glob("*.md")) | set(ROOT.parent.glob("*.md"))
    for directory in ("docs", "doc", "ai_koordinasyon", "spec"):
        base = ROOT / directory
        if base.exists():
            result.update(p for p in base.rglob("*") if p.is_file()
                          and p.suffix.lower() in (".md", ".txt", ".docx")
                          and not (p.suffix.lower() == ".docx" and p.name.startswith("~$"))
                          and not any(x in (".git", "node_modules", "__pycache__") for x in p.parts))
    # Prefer the live coordination/design files as canonical paths for duplicate content.
    return sorted(result, key=lambda p: (
        0 if "ai_koordinasyon" in p.parts or "tasarim" in p.parts else 1,
        len(p.parts), str(p).casefold()))


def build():
    db = connect()
    inventory = []
    canonical = {}
    problems = []
    document_errors = []
    headings = []
    db.execute("DELETE FROM files")
    db.execute("DELETE FROM chunks")
    for p in paths():
        raw = p.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        path = p.relative_to(ROOT.parent).as_posix()
        inventory.append({"path": path, "sha256": digest, "bytes": len(raw),
                          "canonical": canonical.get(digest, path)})
        db.execute("INSERT INTO files VALUES(?,?,?)", (path, digest, len(raw)))
        if digest in canonical:
            continue
        canonical[digest] = path
        if p.suffix.lower() == ".docx":
            try:
                with zipfile.ZipFile(p) as archive:
                    tree = ET.fromstring(archive.read("word/document.xml"))
            except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError, RuntimeError) as error:
                # One malformed document must not prevent live source/design
                # records from being searchable. Keep its identity and report
                # the omission; never claim it was successfully indexed.
                detail = {"path": path, "sha256": digest,
                          "error": f"{type(error).__name__}: {error}"}
                document_errors.append(detail)
                inventory[-1]["index_error"] = detail["error"]
                continue
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for para in tree.findall(".//w:p", ns):
                value = "".join(node.text or "" for node in para.findall(".//w:t", ns))
                style = para.find("w:pPr/w:pStyle", ns)
                if style is not None and "heading" in style.get("{" + ns["w"] + "}val", "").lower():
                    value = "## " + value
                paragraphs.append(value)
            text = "\n".join(paragraphs)
        else:
            text = raw.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        start = 1
        title = p.stem
        section = []

        def flush(end):
            if section and any(x.strip() for x in section):
                db.execute("INSERT INTO chunks(hash,path,start,end,heading,body) VALUES(?,?,?,?,?,?)",
                           (digest, path, start, end, title, "\n".join(section)))

        for number, line in enumerate(lines, 1):
            heading = re.match(r"^#{1,6}\s+(.+)", line)
            if heading or len(section) >= 65:
                flush(number - 1)
                section = []
                start = number
            if heading:
                title = heading[1]
                headings.append(f"{path}:{number}\t{title}")
                if p.name == "SORUN_TAKIP.md" and re.match(r"S-\d+", title):
                    section_lines = []
                    for next_line in lines[number:number + 8]:
                        if re.match(r"^#{1,3}\s+", next_line):
                            break
                        section_lines.append(next_line)
                    excerpt = "\n".join(section_lines)
                    statuses = re.findall(
                        r"(?:Durum|DURUM|durum)\s*[:*]*\s*`?([^\n]+)", excerpt)
                    problems.append({"heading": title, "line": number, "path": path,
                                     "status_excerpt": statuses[:2], "excerpt": excerpt[:1500]})
            section.append(line)
        flush(len(lines))
    db.execute("INSERT INTO search(search) VALUES('rebuild')")
    db.commit()
    summary = {"schema": "uxb.context.v1", "generated_at": datetime.now(timezone.utc).isoformat(),
               "files": len(inventory), "unique_files": len(canonical),
               "chunks": db.execute("SELECT count(*) FROM chunks").fetchone()[0],
               "indexed_unique_files": len(canonical) - len(document_errors),
               "document_errors": len(document_errors),
               "document_error_report": str(OUT / "document_errors.json"),
               "bytes": sum(x["bytes"] for x in inventory), "issue_sections": len(problems),
               "database": str(DB), "scope": ["uxb/docs", "uxb/doc", "uxb/ai_koordinasyon",
                                                "uxb/spec", "workspace and uxb root markdown"],
               "limitations": "PDF/legacy DOC/ZIP content is not indexed. Word owner (~$) lock files are excluded. Unreadable DOCX files are listed in document_errors.json. DOCX positions are extracted paragraph lines. Issue excerpts are evidence, not resolved statuses."}
    for name, value in (("inventory.json", inventory), ("issues.json", problems),
                        ("summary.json", summary), ("document_errors.json", document_errors)):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "headings.tsv").write_text("\n".join(headings) + "\n", encoding="utf-8")
    db.close()
    if document_errors:
        print(f"WARNING: {len(document_errors)} unreadable DOCX document(s); "
              f"see {OUT / 'document_errors.json'}", file=sys.stderr)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def search(query, limit, budget):
    if not DB.exists():
        raise SystemExit("Run build first.")
    summary_path = OUT / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("document_errors", 0):
            print(f"WARNING: {summary['document_errors']} DOCX document(s) were not indexed; "
                  f"see {OUT / 'document_errors.json'}", file=sys.stderr)
    db = connect()
    # Literal token matching avoids accidental FTS query operators and syntax errors.
    tokens = re.findall(r"[\w]+", query, re.UNICODE)
    if not tokens:
        raise SystemExit("Query must contain words.")
    expr = " AND ".join('"' + x + '"' for x in tokens)
    rows = db.execute("""SELECT c.path,c.start,c.end,c.heading,
        snippet(search,1,'[',']',' ... ',60) FROM search
        JOIN chunks c ON c.id=search.rowid WHERE search MATCH ?
        ORDER BY bm25(search,3.0,1.0) LIMIT ?""", (expr, limit)).fetchall()
    used = 0
    for path, start, end, heading, excerpt in rows:
        block = f"{path}:{start}-{end} | {heading}\n{excerpt}\n"
        remaining = budget - used
        if remaining <= 0:
            break
        print(block[:remaining])
        used += min(len(block), remaining)
    print(f"matches_returned={len(rows)} output_chars={used}")
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    find = sub.add_parser("search")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=6)
    find.add_argument("--chars", type=int, default=6000)
    args = parser.parse_args()
    if args.command == "build":
        build()
    else:
        search(args.query, max(1, min(args.limit, 30)), max(200, min(args.chars, 30000)))
