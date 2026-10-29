#!/usr/bin/env python3
"""Build, verify, stage and deploy the canonical uXBasic Windows x64 DLL set."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class BuildRow:
    name: str
    tier: str
    required: bool
    status: str
    build_script: str
    used_fallback: bool
    dll: str
    deployed_dist: bool
    deployed_bin: bool
    elapsed_seconds: float
    message: str


def resolve_root(value: str) -> Path:
    p=Path(value).resolve()
    if (p/'runtime_ext').is_dir() and (p/'libsx').is_dir(): return p
    if (p/'uxb'/'runtime_ext').is_dir(): return p/'uxb'
    raise SystemExit(f'uXBasic root not found: {p}')

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def pe_machine(path: Path) -> str:
    try:
        data=path.read_bytes()
        if data[:2]!=b'MZ': return 'not-pe'
        pe=int.from_bytes(data[0x3c:0x40],'little')
        if data[pe:pe+4]!=b'PE\0\0': return 'not-pe'
        m=int.from_bytes(data[pe+4:pe+6],'little')
        return {0x14c:'x86',0x8664:'x64',0xaa64:'arm64'}.get(m,f'0x{m:04x}')
    except Exception as e: return f'error:{e}'

def run_logged(command: list[str], cwd: Path, log: Path, env: dict[str,str]|None=None) -> tuple[int,str]:
    log.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    with log.open('w',encoding='utf-8',errors='replace') as out:
        out.write('COMMAND: '+' '.join(command)+'\n')
        out.write('CWD: '+str(cwd)+'\n\n'); out.flush()
        p=subprocess.run(command,cwd=str(cwd),stdout=out,stderr=subprocess.STDOUT,text=True,env=env)
    return p.returncode,f'{time.monotonic()-started:.2f}'

def run_bat(root: Path, rel: str, log: Path) -> tuple[int,float,str]:
    script=root/rel
    if not script.is_file(): return 127,0.0,f'script missing: {rel}'
    if os.name!='nt': return 126,0.0,'Windows cmd.exe is required to build DLLs'
    started=time.monotonic()
    rc,_=run_logged(['cmd.exe','/d','/c',str(script)],root.parent,log)
    message='' if rc==0 else f'build failed rc={rc}; log={log.relative_to(root)}'
    return rc,time.monotonic()-started,message


def run_script(root: Path, rel: str, log: Path) -> tuple[int,float,str]:
    script=root/rel
    if not script.is_file(): return 127,0.0,f'script missing: {rel}'
    if script.suffix.lower()=='.bat': return run_bat(root,rel,log)
    if script.suffix.lower()=='.ps1':
        if os.name!='nt': return 126,0.0,'Windows PowerShell is required to run .ps1 dependency/build scripts'
        powershell=shutil.which('pwsh.exe') or shutil.which('powershell.exe')
        if not powershell: return 9009,0.0,'pwsh.exe/powershell.exe not found'
        started=time.monotonic()
        rc,_=run_logged([powershell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],root,log)
        return rc,time.monotonic()-started,'' if rc==0 else f'script failed rc={rc}; log={log.relative_to(root)}'
    return 125,0.0,f'unsupported script type: {rel}'


def build_compiler_x64(root: Path, log: Path) -> tuple[int,str]:
    if os.name != 'nt':
        return 21, 'Windows PowerShell is required to build the compiler'
    script = root / 'compiler/scripts/build_uxb_main_64.ps1'
    if not script.is_file():
        return 127, f'compiler build script missing: {script}'
    powershell = shutil.which('powershell.exe') or shutil.which('pwsh.exe')
    if not powershell:
        return 9009, 'powershell.exe/pwsh.exe not found'
    command = [powershell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), '-Root', str(root), '-Force', '-SkipX86']
    rc, elapsed = run_logged(command, root, log)
    exe = root / 'bin/uxb.exe'
    if rc == 0 and (not exe.is_file() or pe_machine(exe) != 'x64'):
        return 22, f'compiler output missing or not x64 after {elapsed}s'
    return rc, f'elapsed={elapsed}s'

def copy_if_different(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and src.stat().st_size==dst.stat().st_size and sha256(src)==sha256(dst): return False
    shutil.copy2(src,dst); return True

def build_output_candidates(root: Path, dll: str) -> list[Path]:
    return [
        root/'dist/libraries/bin'/dll,
        root/'dist/runtime_ext'/dll,
        *root.glob(f'runtime_ext/*/{dll}'),
        root/'native/uxb_runtime/build'/dll,
    ]

def find_expected_dll(root: Path, dll: str, not_older_than: float|None=None) -> Path|None:
    for candidate in build_output_candidates(root,dll):
        if not candidate.is_file():
            continue
        if not_older_than is not None and candidate.stat().st_mtime + 2.0 < not_older_than:
            continue
        return candidate
    return None

def remove_stale_build_outputs(root: Path, dll: str) -> None:
    # Keep bin/<dll> as last-known-good runtime copy. Build outputs are removed so
    # a successful BAT cannot be falsely credited to a stale artifact.
    for candidate in build_output_candidates(root,dll):
        try:
            if candidate.is_file(): candidate.unlink()
        except OSError:
            pass



def select_libraries(manifest: dict, set_name: str, names: set[str]) -> list[dict]:
    """Resolve a build set without silently omitting custom ecosystem tiers."""
    libraries = list(manifest.get("libraries", []))
    if names:
        return [lib for lib in libraries if str(lib.get("name", "")).lower() in names]
    if set_name == "minimal":
        return [lib for lib in libraries if bool(lib.get("required"))]
    if set_name == "core":
        return [lib for lib in libraries if bool(lib.get("required")) or lib.get("tier") in {"core", "bridge"}]
    if set_name == "all":
        return libraries
    raise ValueError(f"unknown library set: {set_name}")

def stage_all(root: Path, manifest: dict) -> dict:
    paths=manifest['paths']
    dist=root/paths['distribution']; dist_bin=root/paths['distribution_bin']; deps=root/paths['distribution_dependencies']; implib=root/paths['distribution_import_libraries']; runtime_bin=root/paths['runtime_bin']
    for p in (dist_bin,deps,implib,runtime_bin,dist/'sdk/include/modules',dist/'sdk/libsx',dist/'sdk/native'): p.mkdir(parents=True,exist_ok=True)
    first_party={x['dll'].lower() for x in manifest['libraries']}
    first_party |= {'libuxb_fp80.dll','libuxb_fp128.dll','libuxb_bigfp.dll'}
    candidates=[]
    for folder in (root/'dist/runtime_ext',root/'dist/libraries/bin',root/'dist/libraries/deps'):
        if folder.is_dir(): candidates += list(folder.glob('*.dll'))
    legacy_deps=root/'dist/runtime_ext/deps'
    if legacy_deps.is_dir(): candidates += list(legacy_deps.rglob('*.dll'))
    for module in (root/'runtime_ext').iterdir():
        if module.is_dir(): candidates += list(module.glob('*.dll'))
    # A messy historical tree may contain the same DLL in several locations.
    # Stage the newest copy instead of letting legacy folder order win.
    newest_by_name={}
    for src in candidates:
        key=src.name.lower()
        current=newest_by_name.get(key)
        if current is None or src.stat().st_mtime > current.stat().st_mtime:
            newest_by_name[key]=src
    deployed=[]
    for key,src in sorted(newest_by_name.items()):
        target_dir=dist_bin if key in first_party else deps
        copy_if_different(src,target_dir/src.name)
        copy_if_different(src,runtime_bin/src.name)
        deployed.append({'name':src.name,'class':'first-party' if key in first_party else 'dependency','source':str(src.relative_to(root)).replace('\\','/')})
    # Import libraries from legacy output/module folders.
    for pattern in ('*.a','*.dll.a','*.lib'):
        for src in list((root/'dist/runtime_ext').glob(pattern)) if (root/'dist/runtime_ext').is_dir() else []:
            copy_if_different(src,implib/src.name)
        for src in (root/'runtime_ext').glob(f'*/{pattern}'):
            copy_if_different(src,implib/src.name)
    # SDK snapshot: public uXBasic headers, wrappers and native C headers.
    for src in (root/'include/modules').glob('*.uxmh'):
        copy_if_different(src,dist/'sdk/include/modules'/src.name)
    if (root/'include/libs.uxmh').is_file(): copy_if_different(root/'include/libs.uxmh',dist/'sdk/include/libs.uxmh')
    for src in (root/'libsx').glob('*/*.bas'):
        copy_if_different(src,dist/'sdk/libsx'/src.parent.name/src.name)
    for src in (root/'runtime_ext').glob('*/*.h'):
        copy_if_different(src,dist/'sdk/native'/src.parent.name/src.name)
    native_runtime = root/'native/uxb_runtime'
    if native_runtime.is_dir():
        for src in native_runtime.rglob('*.h'):
            copy_if_different(src,dist/'sdk/native/uxb_runtime'/src.relative_to(native_runtime))
    return {'deployed':deployed,'dist_bin':str(dist_bin),'runtime_bin':str(runtime_bin)}

def write_runtime_manifest(root: Path, manifest: dict, build_rows: list[BuildRow], stage: dict) -> Path:
    dist=root/manifest['paths']['distribution']; out=dist/'manifests/runtime_manifest.json'; out.parent.mkdir(parents=True,exist_ok=True)
    files=[]
    for relroot in (manifest['paths']['distribution_bin'],manifest['paths']['distribution_dependencies'],manifest['paths']['distribution_import_libraries']):
        folder=root/relroot
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if p.is_file(): files.append({'path':str(p.relative_to(root)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha256(p),'machine':pe_machine(p) if p.suffix.lower()=='.dll' else ''})
    payload={'schema':'uxb.library_runtime_manifest.v2','generated_at_epoch':int(time.time()),'abi':manifest['abi'],'build_rows':[asdict(r) for r in build_rows],'files':files,'stage':stage}
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def main() -> int:
    ap=argparse.ArgumentParser(description='Build and deploy uXBasic native libraries')
    ap.add_argument('--root',default='.')
    ap.add_argument('--set',choices=['minimal','core','all'],default='core')
    ap.add_argument('--library',action='append',default=[],help='build only named library; repeatable')
    ap.add_argument('--audit-only',action='store_true')
    ap.add_argument('--deploy-only',action='store_true')
    ap.add_argument('--fetch-deps',action='store_true')
    ap.add_argument('--clean',action='store_true')
    ap.add_argument('--strict-all',action='store_true')
    ap.add_argument('--strict-runtime',action='store_true',help='require x64 bin/uxb.exe and x64 DLLs')
    ap.add_argument('--build-compiler',action='store_true')
    args=ap.parse_args()
    root=resolve_root(args.root)
    manifest=json.loads((root/'manifests/uxb_library_system.json').read_text(encoding='utf-8'))
    report=root/manifest['paths']['reports']; logs=report/'logs'; report.mkdir(parents=True,exist_ok=True); logs.mkdir(parents=True,exist_ok=True)
    failures=0

    # Mandatory patch/source-integrity gate, followed by wrapper/C ABI gate.
    source_gate_cmd=[sys.executable,str(root/'tools/library_tools/uxb_library_source_gate.py'),'--root',str(root),'--report-dir',manifest['paths']['reports']+'/source_gate']
    source_gate=subprocess.run(source_gate_cmd,cwd=str(root))
    if source_gate.returncode!=0:
        print('ERROR: library source-integrity gate failed; build stopped.',file=sys.stderr); return 19

    abi_cmd=[sys.executable,str(root/'tools/library_tools/uxb_library_abi.py'),'--root',str(root),'--report-dir',manifest['paths']['reports']+'/abi']
    abi=subprocess.run(abi_cmd,cwd=str(root))
    if abi.returncode!=0:
        print('ERROR: wrapper/C ABI audit failed; build stopped.',file=sys.stderr); return 20

    if args.audit_only:
        print('OK: source ABI audit passed.'); return 0

    if args.clean:
        for rel in ('build/libraries','dist/libraries'):
            p=root/rel
            if p.exists(): shutil.rmtree(p)

    names=set(x.lower() for x in args.library)
    selected=select_libraries(manifest,args.set,names)
    unknown=names-{x['name'].lower() for x in manifest['libraries']}
    if unknown:
        print('ERROR: unknown libraries: '+', '.join(sorted(unknown)),file=sys.stderr); return 23

    if args.fetch_deps:
        os.environ['UXB_LIBRARY_FETCH_DEPS']='1'
    else:
        os.environ.pop('UXB_LIBRARY_FETCH_DEPS',None)

    rows=[]
    group_runs: dict[str, dict] = {}
    if not args.deploy_only:
        selected_groups: dict[str, list[dict]] = {}
        for item in selected:
            group=str(item.get('build_group') or item.get('name'))
            selected_groups.setdefault(group,[]).append(item)
        for lib in selected:
            name=lib['name']; started=time.monotonic(); used_fallback=False; message=''; used_script=''; rc=1
            group=str(lib.get('build_group') or name)
            if group not in group_runs:
                wall_started=time.time()
                for grouped in selected_groups[group]:
                    remove_stale_build_outputs(root,grouped['dll'])
                if args.fetch_deps:
                    seen_fetch=set()
                    for grouped in selected_groups[group]:
                        for rel in grouped.get('fetch_dependencies',[]):
                            if rel in seen_fetch: continue
                            seen_fetch.add(rel)
                            frc,_,fmsg=run_script(root,rel,logs/f'{group}_fetch.log')
                            if frc!=0: message+=f'fetch failed({frc}) {rel}; '
                scripts=[]
                for grouped in selected_groups[group]:
                    for rel in grouped.get('build',[]):
                        if rel not in scripts: scripts.append(rel)
                for rel in scripts:
                    used_script=rel; rc,_,msg=run_script(root,rel,logs/f'{group}_build.log'); message+=msg
                    if rc==0: break
                if rc!=0 and lib.get('fallback'):
                    used_fallback=True
                    for rel in lib['fallback']:
                        used_script=rel; rc,_,msg=run_script(root,rel,logs/f'{group}_fallback.log'); message+=msg
                        if rc==0: break
                if rc==0:
                    seen_copy=set()
                    for grouped in selected_groups[group]:
                        for rel in grouped.get('copy_dependencies',[]):
                            if rel in seen_copy: continue
                            seen_copy.add(rel)
                            drc,_,dmsg=run_script(root,rel,logs/f'{group}_deps.log')
                            if drc!=0: message+=f'dependency copy warning({drc}) {dmsg}; '
                group_runs[group]={'rc':rc,'wall_started':wall_started,'used_script':used_script,'used_fallback':used_fallback,'message':message}
            run=group_runs[group]
            rc=int(run['rc']); wall_started=float(run['wall_started']); used_script=str(run['used_script']); used_fallback=bool(run['used_fallback']); message=str(run['message'])
            dll=find_expected_dll(root,lib['dll'],wall_started)
            if rc==0 and dll is None:
                rc=2; message+=f'build group {group!r} succeeded but expected {lib["dll"]} was not found; '
            fatal=bool(lib.get('required')) or args.strict_all or bool(names)
            status='PASS' if rc==0 else ('FAIL' if fatal else 'SKIP_OPTIONAL')
            if status=='FAIL': failures+=1
            rows.append(BuildRow(name,lib['tier'],bool(lib.get('required')),status,used_script,used_fallback,lib['dll'],False,False,time.monotonic()-started,message.strip()))
            print(f'{name}: {status}')

    stage=stage_all(root,manifest)
    # Mark deployment from actual files after staging.
    for row in rows:
        row.deployed_dist=(root/manifest['paths']['distribution_bin']/row.dll).is_file()
        row.deployed_bin=(root/manifest['paths']['runtime_bin']/row.dll).is_file()
        if row.status=='PASS' and (not row.deployed_dist or not row.deployed_bin):
            row.status='FAIL'; row.message+=' deployment missing'; failures+=1

    runtime_manifest=write_runtime_manifest(root,manifest,rows,stage)

    # The organize/stage pass must not be blocked by stale historical DLLs.
    # Fresh architecture/export verification happens after the selected build set.
    if args.deploy_only:
        print(f"OK: existing DLLs staged by newest timestamp; manifest={runtime_manifest}")
        return 0

    # Audit only the selected set. Unrelated stale optional DLLs cannot poison a
    # core build, while every DLL produced by this invocation remains checked.
    export_cmd=[sys.executable,str(root/'tools/library_tools/uxb_library_export_audit.py'),'--root',str(root),'--report-dir',manifest['paths']['reports']+'/exports']
    for lib in selected: export_cmd.extend(['--only-dll',lib['dll']])
    if args.strict_runtime: export_cmd.extend(['--require-x64','--require-required'])
    if args.set=='all' and args.strict_all: export_cmd.append('--require-all')
    export_rc=subprocess.run(export_cmd,cwd=str(root)).returncode
    if export_rc!=0: failures+=1

    # Native DLLs are built and deployed first.  Only then is the x64 compiler
    # rebuilt, so its runtime directory already contains the canonical DLL set.
    required_build_failures=sum(1 for row in rows if row.status=='FAIL' and row.required)
    compiler_message=''
    if args.build_compiler:
        if required_build_failures:
            compiler_message=f'skipped because {required_build_failures} required DLL build(s) failed'
            print('ERROR: x64 compiler build skipped: '+compiler_message,file=sys.stderr)
        else:
            compiler_rc,compiler_message=build_compiler_x64(root,logs/'compiler_x64_build.log')
            if compiler_rc!=0:
                failures+=1
                print(f'ERROR: x64 compiler build failed rc={compiler_rc}: {compiler_message}',file=sys.stderr)
            else:
                print('x64 compiler: PASS')

    exe=root/'bin/uxb.exe'; exe_arch=pe_machine(exe) if exe.is_file() else 'missing'
    if args.strict_runtime and exe_arch!='x64':
        failures+=1; print(f'ERROR: bin/uxb.exe must be x64, found {exe_arch}',file=sys.stderr)
    elif exe_arch!='x64':
        print(f'WARN: bin/uxb.exe is {exe_arch}; x64 DLLs require a rebuilt x64 compiler/interpreter.')

    summary={'schema':'uxb.library_build_summary.v3','status':'PASS' if failures==0 else 'FAIL','failure_count':failures,'set':args.set,'selected':[x['name'] for x in selected],'build_order':['source_gate','abi_gate','native_dlls','deploy','export_audit','x64_compiler'],'compiler_machine':exe_arch,'compiler_message':compiler_message,'runtime_manifest':str(runtime_manifest.relative_to(root)).replace('\\','/'),'rows':[asdict(r) for r in rows]}
    (report/'library_build_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['# uXBasic Library Build Summary','',f"Status: **{summary['status']}**",'',f"Compiler: `{exe_arch}`",'', '| Library | Tier | Status | DLL | bin | Fallback |','|---|---|---|---|---:|---:|']
    for r in rows: md.append(f'| {r.name} | {r.tier} | {r.status} | {r.dll} | {int(r.deployed_bin)} | {int(r.used_fallback)} |')
    (report/'library_build_summary.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(f"Library system status={summary['status']} failures={failures} manifest={runtime_manifest}")
    return 0 if failures==0 else 1

if __name__=='__main__':
    raise SystemExit(main())
