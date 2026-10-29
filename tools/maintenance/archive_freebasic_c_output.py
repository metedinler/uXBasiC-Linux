#!/usr/bin/env python3
"""Move generated FreeBASIC C outputs out of canonical source directories."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
    root=Path(args.root).resolve(); candidates=[]
    for path in (root/'src').rglob('*.c'):
        if path.name.lower()=='main.c' or path.stat().st_size > 1024*1024: candidates.append(path)
    destination=root/'build/generated/freebasic_c'
    rows=[]
    for src in candidates:
        rel=src.relative_to(root/'src'); dst=destination/rel; digest=hashlib.sha256(src.read_bytes()).hexdigest()
        rows.append({'source':src.relative_to(root).as_posix(),'destination':dst.relative_to(root).as_posix(),'bytes':src.stat().st_size,'sha256':digest})
        if args.apply:
            dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(src),str(dst))
    report={'schema':'uxb.freebasic_c_archive.v1','generated_at':datetime.now(timezone.utc).isoformat(),'applied':args.apply,'files':rows}
    destination.mkdir(parents=True,exist_ok=True); (destination/'archive_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"FREEBASIC_C_ARCHIVE candidates={len(rows)} applied={int(args.apply)}")
    return 0
if __name__=='__main__': raise SystemExit(main())
