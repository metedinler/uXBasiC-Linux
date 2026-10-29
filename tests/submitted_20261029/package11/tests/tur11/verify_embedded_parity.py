#!/usr/bin/env python3
"""Recover embedded FreeBASIC JS string literal projection and verify byte parity."""
from pathlib import Path
import re, sys
root=Path(sys.argv[1]).resolve()
source=(root/'runtime/js/common/ux_runtime_core.js').read_bytes()
fb=(root/'src/codegen/js/runtime/js_runtime_embedded_generated.fbs').read_text(encoding='utf-8')
lines=[]
for line in fb.splitlines():
    m=re.fullmatch(r'\s*s &= "((?:[^"]|"")*)" & Chr\(10\)\s*',line)
    if m: lines.append(m.group(1).replace('""','"')+'\n')
joined=''.join(lines).encode('utf-8')
if joined!=source:
    print('FAIL: generated FreeBASIC JS text is out of sync',len(joined),len(source));sys.exit(1)
print(f'PASS: embedded/external byte-identical ({len(source)} bytes; {len(lines)} lines)')
if len(sys.argv)>2:Path(sys.argv[2]).write_bytes(joined)
