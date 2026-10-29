#!/usr/bin/env python3
"""Cross-check the canonical uXBasic compiler/library ecosystem.

The doctor is intentionally cross-platform. It verifies metadata, wrappers,
source layout and tool contracts without pretending to replace Windows builds.
"""
from __future__ import annotations
import argparse, importlib.util, json, re, subprocess, sys
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Check:
    name: str
    ok: bool
    severity: str
    path: str
    message: str

def resolve_root(value: str) -> Path:
    p=Path(value).resolve()
    if (p/'src').is_dir() and (p/'runtime_ext').is_dir(): return p
    if (p/'uxb/src').is_dir(): return p/'uxb'
    raise SystemExit(f'uXBasic root not found: {p}')

def load_build_tool(root: Path):
    path=root/'tools/library_tools/uxb_library_build.py'
    spec=importlib.util.spec_from_file_location('uxb_library_build',path)
    if not spec or not spec.loader: raise RuntimeError(f'cannot load {path}')
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    return module

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--strict-source',action='store_true'); ap.add_argument('--report-dir',default='reports/libraries/ecosystem_doctor'); args=ap.parse_args()
    root=resolve_root(args.root); out=root/args.report_dir; out.mkdir(parents=True,exist_ok=True); checks=[]
    def add(name,ok,path='',message='',severity='ERROR'):
        checks.append(Check(name,bool(ok),severity,str(path).replace('\\','/'),message))

    manifest_path=root/'manifests/uxb_library_system.json'
    try: manifest=json.loads(manifest_path.read_text(encoding='utf-8')); add('manifest-json',True,manifest_path.relative_to(root),'valid JSON')
    except Exception as exc: manifest={}; add('manifest-json',False,manifest_path.relative_to(root),str(exc))
    libraries=manifest.get('libraries',[]); names=[str(x.get('name','')).lower() for x in libraries]
    add('manifest-unique-names',len(names)==len(set(names)),manifest_path.relative_to(root),f'libraries={len(names)} unique={len(set(names))}')
    if manifest:
        try:
            build=load_build_tool(root)
            all_selected=build.select_libraries(manifest,'all',set())
            minimal=build.select_libraries(manifest,'minimal',set())
            core=build.select_libraries(manifest,'core',set())
            add('build-set-all-complete',len(all_selected)==len(libraries),'tools/library_tools/uxb_library_build.py',f'all={len(all_selected)} manifest={len(libraries)}')
            add('build-set-minimal-required',all(x.get('required') for x in minimal),'tools/library_tools/uxb_library_build.py',f'minimal={len(minimal)}')
            add('build-set-core-required',all(x in core for x in minimal),'tools/library_tools/uxb_library_build.py',f'core={len(core)}')
        except Exception as exc: add('build-set-resolution',False,'tools/library_tools/uxb_library_build.py',str(exc))
        for lib in libraries:
            name=lib.get('name','?')
            for key in ('native_dir','wrapper','public_header'):
                rel=lib.get(key)
                if rel: add(f'{key}:{name}',(root/rel).exists(),rel,'exists' if (root/rel).exists() else 'missing')
            if lib.get('native_header'):
                rel=lib['native_header']; add(f'native_header:{name}',(root/rel).is_file(),rel,'exists' if (root/rel).is_file() else 'missing')
        uxcapi=next((x for x in libraries if x.get('name')=='uxcapi'),{})
        add('uxcapi-public-forwarder',uxcapi.get('public_header')=='include/modules/uxcapi.uxmh',manifest_path.relative_to(root),str(uxcapi.get('public_header')))
        add('uxcapi-native-header',uxcapi.get('native_header')=='runtime_ext/uxcapi/uxcapi.h',manifest_path.relative_to(root),str(uxcapi.get('native_header')))
        add('uxwasmrt-canonical',any(x.get('name')=='uxwasmrt' for x in libraries),manifest_path.relative_to(root),'runtime must be in canonical manifest')
        multimedia=[x for x in libraries if x.get('name') in {'uxraylib','uxsdl3'}]
        add('multimedia-shared-build-group',len(multimedia)==2 and len({x.get('build_group') for x in multimedia})==1 and multimedia[0].get('build_group'),manifest_path.relative_to(root),str([x.get('build_group') for x in multimedia]))

    bad_headers=[]
    for p in (root/'include').rglob('*.uxmh'):
        if re.search(r'(?im)^\s*#(?:ifndef|define|endif)\b',p.read_text(encoding='utf-8',errors='replace')): bad_headers.append(p.relative_to(root).as_posix())
    add('uxmh-no-c-guards',not bad_headers,'include',','.join(bad_headers[:20]))

    required_root=['build_64.bat','build_64.ps1','build_libraries.bat','build_libraries.ps1','BUILD_UXB_LIBRARY_SYSTEM.bat','BUILD_UXB_LIBRARY_SYSTEM.ps1','RUN_UXB_ECOSYSTEM_DOCTOR.bat']
    for rel in required_root: add('root-entrypoint:'+rel,(root/rel).is_file(),rel,'exists' if (root/rel).is_file() else 'missing')

    personal=[]
    for base in ('runtime_ext','compiler/scripts','tools/maintenance','tool_py'):
        folder=root/base
        if not folder.exists(): continue
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.c','.h','.bat','.ps1','.py'}:
                text=p.read_text(encoding='utf-8',errors='replace')
                if re.search(r'(?i)C:\\Users\\[^\\]+\\',text): personal.append(p.relative_to(root).as_posix())
    add('no-user-specific-tool-paths',not personal,'runtime_ext;compiler/scripts;tools/maintenance;tool_py',','.join(personal[:20]))

    embedded=[]
    secret_pattern=re.compile(r'(?i)(?:api[_-]?key|gemini_key|groq_key|openrouter_key|secret|access[_-]?token)\s*=\s*[\"\'][A-Za-z0-9._-]{16,}[\"\']|(?:AIza|sk-or-v1-|gsk_|AQ\.)[A-Za-z0-9._-]{16,}')
    for base in ('tool_py','tools','runtime_ext','compiler'):
        folder=root/base
        if not folder.exists(): continue
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.py','.ps1','.bat','.c','.h','.js','.json'}:
                if secret_pattern.search(path.read_text(encoding='utf-8',errors='replace')): embedded.append(path.relative_to(root).as_posix())
    add('no-embedded-api-keys',not embedded,'tool_py;tools;runtime_ext;compiler',','.join(embedded[:20]))

    generated=(root/'src/main.c')
    add('generated-c-outside-src',not generated.exists(),'src/main.c','use tools/maintenance/archive_freebasic_c_output.py', 'ERROR' if args.strict_source else 'WARN')

    inventory=root/'manifests/uxb_dll_inventory.json'
    if inventory.is_file():
        try:
            inv=json.loads(inventory.read_text(encoding='utf-8'))
            bad=[e for dll in inv.get('dlls',[]) for e in dll.get('exports',[]) if e.startswith('+base[')]
            add('inventory-export-parser',not bad,inventory.relative_to(root),f'bad_exports={len(bad)}')
        except Exception as exc: add('inventory-export-parser',False,inventory.relative_to(root),str(exc))
    else: add('inventory-export-parser',False,inventory.relative_to(root),'inventory missing','WARN')

    abi_report=out/'abi'
    abi=subprocess.run([sys.executable,str(root/'tools/library_tools/uxb_library_abi.py'),'--root',str(root),'--report-dir',str(abi_report)],cwd=root,capture_output=True,text=True)
    add('wrapper-native-abi',abi.returncode==0,'tools/library_tools/uxb_library_abi.py',(abi.stdout+abi.stderr).strip()[-1000:])

    failures=[c for c in checks if not c.ok and (c.severity=='ERROR' or args.strict_source)]
    payload={'schema':'uxb.ecosystem_doctor.v1','status':'PASS' if not failures else 'FAIL','summary':{'checks':len(checks),'pass':sum(c.ok for c in checks),'fail':len(failures)},'checks':[asdict(c) for c in checks]}
    (out/'ecosystem_doctor.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# uXBasic Ecosystem Doctor','',f"Status: **{payload['status']}**",'',f"Checks: {len(checks)}; failures: {len(failures)}",'','| Check | Status | Severity | Path | Message |','|---|---|---|---|---|']
    for c in checks: lines.append(f"| {c.name} | {'PASS' if c.ok else 'FAIL'} | {c.severity} | `{c.path}` | {c.message.replace('|','/')} |")
    (out/'ecosystem_doctor.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f"ECOSYSTEM_DOCTOR status={payload['status']} checks={len(checks)} failures={len(failures)}")
    for c in failures[:30]: print(f'FAIL {c.name}: {c.path}: {c.message}')
    return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
