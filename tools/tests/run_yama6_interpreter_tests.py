#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path

CASES = [
    ('event_input_yama6.uxb', ['EVENT_INPUT', '42'], []),
    ('tasktable_all_kinds_yama6.uxb', ['PIPE_RUN', '3', 'THREAD_RUN', 'PARALEL_RUN'], []),
    ('slot_off_yama6.uxb', ['DONE'], ['SHOULD_NOT_PRINT']),
    ('shell_capture_yama6.uxb', ['SHELL_OK', '0'], []),
    ('full_stack_native_yama6.uxb',
     ['PIPE_RUN', '3', 'THREAD_RUN', 'PARALEL_RUN', 'EVENT_INPUT', '42',
      'SHELL_OK', '0', 'FULL_STACK_DONE'],
     ['SHOULD_NOT_PRINT']),
]

def find_root(value: str) -> Path:
    start=Path(value).resolve()
    for p in (start,*start.parents):
        if (p/'src').is_dir() and (p/'xtestx').is_dir(): return p
        if (p/'uxb'/'src').is_dir(): return p/'uxb'
    here=Path(__file__).resolve()
    for p in here.parents:
        if (p/'src').is_dir() and (p/'xtestx').is_dir(): return p
    raise SystemExit(f'uXBasic root bulunamadi: {start}')

def find_exe(root: Path, requested: str) -> Path | None:
    req=Path(requested)
    candidates=[]
    if requested:
        candidates.append(req if req.is_absolute() else root/req)
    candidates += [root/'bin/uxb.exe',root/'bin/uxb_x64.exe',root/'uxb.exe',root/'bin/uxb_x86.exe']
    return next((p.resolve() for p in candidates if p.is_file()),None)

def run_one(exe: Path, backend: str, source: Path, cwd: Path) -> dict:
    env=os.environ.copy(); env['PATH']=str(cwd/'bin')+os.pathsep+env.get('PATH','')
    cmd=[str(exe),'run',str(source),'--interpreter-backend',backend]
    proc=subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True,timeout=90)
    combined=(proc.stdout or '')+'\n'+(proc.stderr or '')
    return {'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'combined':combined}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--uxb',default='bin/uxb.exe')
    a=ap.parse_args(); root=find_root(a.root); exe=find_exe(root,a.uxb)
    report={'schema':'uxb.yama6.interpreter.v3','root':str(root),'uxb':str(exe) if exe else '','status':'FAIL','results':[]}
    if exe is None:
        report['error']='uxb executable missing; checked bin/uxb.exe, bin/uxb_x64.exe, root/uxb.exe, bin/uxb_x86.exe'
        print(report['error']); return 2
    test_dir=root/'xtestx/yama6_runtime'
    if not test_dir.is_dir(): test_dir=root/'tests/yama6_runtime'
    failed=0
    for backend in ('AST','MIR'):
        for filename,required,forbidden in CASES:
            source=test_dir/filename
            if not source.is_file():
                result={'command':[],'returncode':-2,'stdout':'','stderr':f'missing {source}','combined':''}
            else:
                try: result=run_one(exe,backend,source,root)
                except Exception as exc:
                    result={
                        'command':[str(exe),'run',str(source),'--interpreter-backend',backend],
                        'returncode':-1,'stdout':'','stderr':repr(exc),'combined':repr(exc)
                    }
            text=result['combined']; checks={f'required:{x}':x in text for x in required}; checks.update({f'forbidden:{x}':x not in text for x in forbidden})
            ok=result['returncode']==0 and all(checks.values())
            if not ok: failed+=1
            result.update({'verb':'run','backend':backend,'source':filename,'checks':checks,'status':'PASS' if ok else 'FAIL'}); result.pop('combined',None); report['results'].append(result)
    report['status']='PASS' if failed==0 else 'FAIL'; report['failed']=failed
    out=root/'reports/yama6_runtime'; out.mkdir(parents=True,exist_ok=True); (out/'interpreter_tests.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f"YAMA6_INTERPRETER status={report['status']} failed={failed} exe={exe}")
    print(f"REPORT={out/'interpreter_tests.json'}")
    # UXB_BAT_VISIBLE_FAILURES_20260711: .bat sadece tek satir ozet basinca
    # hangi dosya/verb/check koptu gorunmuyor. Basarisiz vakalari terminale de yaz.
    if failed:
        print("FAILED CASES:")
        for r in report['results']:
            if r.get('status') != 'FAIL':
                continue
            print(f"- verb={r.get('verb')} backend={r.get('backend')} source={r.get('source')} returncode={r.get('returncode')}")
            for key, val in r.get('checks', {}).items():
                if not val:
                    print(f"  check_failed={key}")
            stdout=(r.get('stdout') or '').strip()
            stderr=(r.get('stderr') or '').strip()
            if stdout:
                print("  stdout_tail=" + stdout[-800:].replace("\n"," | "))
            if stderr:
                print("  stderr_tail=" + stderr[-800:].replace("\n"," | "))
    return 0 if failed==0 else 3
if __name__=='__main__': raise SystemExit(main())
