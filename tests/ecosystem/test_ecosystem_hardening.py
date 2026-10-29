#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def load(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module); return module

def main() -> int:
    manifest=json.loads((ROOT/'manifests/uxb_library_system.json').read_text(encoding='utf-8'))
    build=load(ROOT/'tools/library_tools/uxb_library_build.py','uxb_library_build_test')
    assert len(build.select_libraries(manifest,'all',set()))==len(manifest['libraries'])
    assert all(x.get('required') for x in build.select_libraries(manifest,'minimal',set()))
    assert any(x['name']=='uxwasmrt' for x in manifest['libraries'])
    assert next(x for x in manifest['libraries'] if x['name']=='uxcapi')['public_header']=='include/modules/uxcapi.uxmh'
    bad=[]
    for p in (ROOT/'include').rglob('*.uxmh'):
        text=p.read_text(encoding='utf-8',errors='replace')
        if '#ifndef' in text or '#define' in text or '#endif' in text: bad.append(str(p))
    assert not bad,bad
    run=subprocess.run([sys.executable,str(ROOT/'tools/library_tools/uxb_ecosystem_doctor.py'),'--root',str(ROOT)],cwd=ROOT)
    assert run.returncode==0
    print('PASS: ecosystem hardening static tests')
    return 0
if __name__=='__main__': raise SystemExit(main())
