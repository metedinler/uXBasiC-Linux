#!/usr/bin/env python3
"""Idempotently repair the ADIM36/44 negative-test fail-close runner.

The historical copy of this tool was truncated. This implementation either
verifies that the active runner already contains the ADIM44 contract or copies
the complete fixed runner retained beside it.
"""
from __future__ import annotations
import argparse, json, shutil
from datetime import datetime, timezone
from pathlib import Path

def find_root(value: str) -> Path:
    p=Path(value).resolve()
    if (p/'src').is_dir(): return p
    if (p/'uxb/src').is_dir(): return p/'uxb'
    raise SystemExit(f'uXBasic root not found: {p}')

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',default='.'); ap.add_argument('--patch-root',default='patch_files'); args=ap.parse_args()
    root=find_root(args.repo)
    candidates=[root/'tools/control/uxb_adim36_full_surface_runner.py',root/'tool_py/tools/control/uxb_adim36_full_surface_runner.py']
    target=next((p for p in candidates if p.is_file()),candidates[0])
    fixed_candidates=[root/'tools/control/adim36_full_surface_runner_FIXED.py',root/'tool_py/tools/control/adim36_full_surface_runner_FIXED.py']
    fixed=next((p for p in fixed_candidates if p.is_file()),None)
    marker='ADIM44_NEGATIVE_FAIL_CLOSE'
    current=target.read_text(encoding='utf-8',errors='replace') if target.is_file() else ''
    action='verified'
    backup=''
    if marker not in current:
        if fixed is None: raise SystemExit('ADIM44 fixed runner source not found')
        backup_path=root/'build/patch_backup_adim44'/target.relative_to(root)
        if target.is_file():
            backup_path.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,backup_path); backup=backup_path.relative_to(root).as_posix()
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(fixed,target); action='replaced-with-fixed-runner'
    result={'schema':'uxb.adim44.remaining_gaps.v2','generated_at':datetime.now(timezone.utc).isoformat(),'target':target.relative_to(root).as_posix(),'action':action,'backup':backup,'marker_present':marker in target.read_text(encoding='utf-8',errors='replace')}
    out=root/'reports/adim44/apply_remaining_gaps.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f"ADIM44_REPAIR status=PASS action={action} target={result['target']}")
    return 0
if __name__=='__main__': raise SystemExit(main())
