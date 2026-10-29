"""Local source-map/RAG maintenance. Never launches an AI coding agent."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
WORKSPACE=ROOT.parent
V4=WORKSPACE/'UxbRAG/UXB_HYBRID_RAG_V4_YORUMLU_JSON'
STATE=ROOT/'reports/knowledge_watch'
SOURCE_ROOTS=('src','include','libsx','compiler','native','runtime_ext')
EXTENSIONS={'.bas','.bi','.fbs','.uxb','.uxmh','.inc','.c','.cpp','.h','.hpp','.js'}

def snapshot():
    hashes={}
    newest=0
    for name in SOURCE_ROOTS:
        for p in (ROOT/name).rglob('*'):
            if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
                continue
            if any(x in {'build','bin','dist','.git','node_modules','__pycache__'} for x in p.parts):
                continue
            hashes[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
            newest=max(newest,p.stat().st_mtime)
    digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    return digest,newest,len(hashes)

def write(state):
    state['heartbeat']=datetime.now(timezone.utc).isoformat()
    (STATE/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')

def command(args,log):
    with (STATE/log).open('a',encoding='utf-8') as out:
        p=subprocess.run([sys.executable,'-u',*[str(x) for x in args]],cwd=WORKSPACE,
                         stdout=out,stderr=subprocess.STDOUT,timeout=3600)
    if p.returncode:
        raise RuntimeError(f'{log}: exit {p.returncode}')

def cycle(state,budget,quiet):
    digest,newest,count=snapshot()
    mapped=ROOT/'tekdosyaklsoru/kod_analiz/OZET.md'
    if 'mapped_source' not in state and mapped.exists() and mapped.stat().st_mtime>=newest:
        state['mapped_source']=digest
    state.update(pid=os.getpid(),source_fingerprint=digest,source_files=count,
                 automatic_agent_sessions=False,phase='checking')
    if digest!=state.get('mapped_source'):
        if time.time()-newest<quiet:
            state['phase']='waiting_for_source_quiet'
        else:
            state['phase']='mapping'; write(state)
            command([V4/'tools/Moduller/paketleyici31.py','-s','8192','-H','-P','-K','-R','-j'],'mapping.log')
            after,_,_=snapshot()
            if after==digest:
                state['mapped_source']=digest
            else:
                state['phase']='source_changed_during_mapping'
    # A cloud dataset is a dated snapshot, not silently changed while uploading.
    cloud=ROOT/'tekdosyaklsoru/egitim/bulut/source_snapshot.json'
    stale=[]
    if cloud.exists():
        for rel,d in json.loads(cloud.read_text(encoding='utf-8')).items():
            p=WORKSPACE/rel
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=d:
                stale.append(rel)
    state.update(cloud_snapshot_stale_files=stale,phase='rag_indexing'); write(state)
    command([V4/'tools/uxb_chroma_index.py','--config',V4/'config.core.json','--max-chunks',str(budget)],'rag.log')
    progress=V4/'index/file_manifest_core.json.progress.json'
    state['rag']=json.loads(progress.read_text(encoding='utf-8')) if progress.exists() else {'status':'unknown'}
    state.update(phase='idle',last_success=datetime.now(timezone.utc).isoformat()); write(state)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    parser.add_argument('--interval',type=int,default=60)
    parser.add_argument('--budget',type=int,default=64)
    parser.add_argument('--quiet',type=int,default=120)
    args=parser.parse_args()
    STATE.mkdir(parents=True,exist_ok=True)
    # The lock file stays on disk; the OS lock releases when this process exits.
    lock=(STATE/'watch.lock').open('a+b')
    lock.seek(0)
    if not lock.read(1): lock.write(b'1'); lock.flush()
    lock.seek(0)
    import msvcrt
    try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        raise SystemExit('Knowledge maintenance watcher is already running')
    state=json.loads((STATE/'state.json').read_text(encoding='utf-8')) if (STATE/'state.json').exists() else {}
    state.update(pid=os.getpid(),started_at=datetime.now(timezone.utc).isoformat())
    while True:
        try: cycle(state,args.budget,args.quiet)
        except Exception as exc:
            state.update(phase='failed',error=str(exc)); write(state)
            if args.once: raise
        if args.once: break
        time.sleep(max(10,args.interval))

if __name__=='__main__': main()
