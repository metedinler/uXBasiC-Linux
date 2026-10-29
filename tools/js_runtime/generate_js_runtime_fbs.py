#!/usr/bin/env python3
from pathlib import Path
import argparse
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ns=ap.parse_args(); root=Path(ns.root)
src=root/'runtime/js/common/ux_runtime_core.js'; out=root/'src/codegen/js/runtime/js_runtime_embedded_generated.fbs'
lines=['#ifndef UXB_JS_RUNTIME_EMBEDDED_GENERATED_FBS','#define UXB_JS_RUNTIME_EMBEDDED_GENERATED_FBS','',"' GENERATED FILE. Source: runtime/js/common/ux_runtime_core.js","' Regenerate with: python tools/js_runtime/generate_js_runtime_fbs.py --root .",'Function UXBJsEmbeddedRuntimeText() As String','    Dim s As String','    s = ""']
for line in src.read_text(encoding='utf-8').splitlines(): lines.append('    s &= "'+line.replace('"','""')+'" & Chr(10)')
lines += ['    Return s','End Function','','#endif','']
out.parent.mkdir(parents=True,exist_ok=True); out.write_text('\n'.join(lines),encoding='utf-8')
print(out)
