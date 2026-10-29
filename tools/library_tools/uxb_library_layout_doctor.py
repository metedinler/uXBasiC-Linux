#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os
from pathlib import Path

def resolve_root(v:str)->Path:
 p=Path(v).resolve()
 if (p/'runtime_ext').is_dir() and (p/'src').is_dir(): return p
 if (p/'uxb'/'runtime_ext').is_dir(): return p/'uxb'
 raise SystemExit(f'uXBasic root not found: {p}')

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--strict',action='store_true'); args=ap.parse_args()
 root=resolve_root(args.root); manifest=json.loads((root/'manifests/uxb_library_system.json').read_text(encoding='utf-8'))
 checks=[]
 def add(name,ok,message='',severity='ERROR'):
  checks.append({'name':name,'ok':bool(ok),'severity':severity,'message':message})
 for key,rel in manifest['paths'].items():
  if key in {'build','distribution','distribution_bin','distribution_dependencies','distribution_import_libraries','reports','legacy_runtime_output'}:
   continue
  add('path:'+key,(root/rel).exists(),rel)
 for lib in manifest['libraries']:
  add(f"native:{lib['name']}",(root/lib['native_dir']).is_dir(),lib['native_dir'])
  if lib.get('wrapper'): add(f"wrapper:{lib['name']}",(root/lib['wrapper']).is_file(),lib['wrapper'])
  if lib.get('public_header'): add(f"header:{lib['name']}",(root/lib['public_header']).is_file(),lib['public_header'])
  for script in lib.get('build',[]): add(f"build-script:{lib['name']}",(root/script).is_file(),script)
 # Produced binaries must not live in compiler/wrapper/include source trees.
 forbidden=[]
 for rel in ('src','libsx','include'):
  folder=root/rel
  if folder.is_dir():
   forbidden += [str(p.relative_to(root)).replace('\\','/') for ext in ('*.dll','*.exe','*.obj','*.o','*.a','*.lib') for p in folder.rglob(ext)]
 # runtime_ext is native source; old in-place products are warned, not fatal unless strict.
 runtime_products=[str(p.relative_to(root)).replace('\\','/') for ext in ('*.dll','*.exe','*.obj','*.o','*.a','*.lib') for p in (root/'runtime_ext').rglob(ext)]
 add('source-tree-binaries',not forbidden,';'.join(forbidden))
 add('runtime_ext-products',not runtime_products,';'.join(runtime_products),'WARN')
 add('tests-outside-src',not (root/'src/tests').exists(),'tests must be under tests/libraries, not src/tests')
 add('runtime-bin', (root/'bin').is_dir(),'bin')
 add('compiler-exe',(root/'bin/uxb.exe').is_file(),'bin/uxb.exe')
 errors=sum((not c['ok']) and (c['severity']=='ERROR' or args.strict) for c in checks)
 status='PASS' if errors==0 else 'FAIL'
 out=root/'reports/libraries/layout'; out.mkdir(parents=True,exist_ok=True)
 payload={'schema':'uxb.library_layout_doctor.v1','status':status,'error_count':errors,'checks':checks}
 (out/'layout_doctor.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 lines=['# uXBasic Library Layout Doctor','',f'Status: **{status}**','', '| Check | Status | Severity | Message |','|---|---|---|---|']
 for c in checks: lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} | {c['severity']} | {c['message'].replace('|','/')} |")
 (out/'layout_doctor.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Library layout status={status} errors={errors} checks={len(checks)}')
 return 0 if errors==0 else 1
if __name__=='__main__': raise SystemExit(main())
