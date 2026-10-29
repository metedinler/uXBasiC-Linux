"""Build a traceable cloud training package from current, grouped source data."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parent
DATA = ROOT / 'tekdosyaklsoru/egitim'
CLOUD = DATA / 'bulut'
SYSTEM = ('Sen uXBasic ve onun FreeBASIC ile yazılmış derleyicisi üzerinde çalışan bir kodlayıcısın. '
          'Kaynak kodu ile hedef tasarımı ayır. Bir özelliği ancak yürütme kanıtı varsa çalışıyor diye sun. '
          'Tasarım ve deneysel öneriler uygulanması gereken hedeflerdir; mevcut destek iddiası değildir. '
          'Yer tutucu veya sahte başarı üretme. İstenen dil ile derleyicinin uygulama dilini karıştırma.')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def build(compiler):
    CLOUD.mkdir(parents=True, exist_ok=True)
    evidence = ROOT / 'reports/knowledge_20261018'
    evidence.mkdir(parents=True, exist_ok=True)
    compiler = compiler.resolve()
    compiler_hash = sha(compiler)
    cache_path = evidence / 'semantic_checks.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    snapshot, checks, counts, records = {}, {}, Counter(), []
    secret = re.compile(r'(?:sk-[A-Za-z0-9_-]{24,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{25,}|gsk_[A-Za-z0-9]{25,})')
    kept_types = {'program', 'rutin_yaz', 'kural', 'dil_yasak'}

    def admit(row):
        kind = row.get('tur', '')
        if kind not in kept_types:
            counts['excluded:unverified_description_or_card'] += 1
            return
        source = row.get('kaynak', '').replace('\\', '/')
        path = WORKSPACE / source
        if not path.is_file():
            path = ROOT / source
        messages = row.get('messages', [])
        if len(messages) != 3 or [m.get('role') for m in messages] != ['system','user','assistant']:
            counts['excluded:invalid_messages'] += 1
            return
        if any(not isinstance(m.get('content'), str) or not m['content'].strip() for m in messages):
            counts['excluded:empty_message'] += 1
            return
        if secret.search(json.dumps(messages, ensure_ascii=False)):
            counts['excluded:credential_pattern'] += 1
            return
        if kind != 'dil_yasak' and not path.is_file():
            counts['excluded:missing_provenance'] += 1
            return
        if path.is_file():
            source = path.resolve().relative_to(WORKSPACE).as_posix()
            digest = snapshot.setdefault(source, sha(path))
            if row.get('source_sha256') and row['source_sha256'] != digest:
                raise RuntimeError('Stale generated source: ' + source)
        else:
            digest = None
        validation = {'source': 'current', 'runtime': 'not_claimed'}
        if kind in ('program', 'dil_ornek'):
            # BAS can be FreeBASIC or a library module; never label it a tested
            # uXBasic program merely because it occurs in a source directory.
            if path.suffix.lower() != '.uxb' or path.stat().st_size > 4000:
                counts['excluded:not_bounded_uxb_program'] += 1
                return
            source_text = path.read_text(encoding='utf-8', errors='replace')
            if re.search(r'(?im)^\s*(?:INCLUDE|IMPORT|LIBTYPE)\b|CALL\s*\(\s*(?:DLL|API)\b', source_text):
                counts['excluded:external_dependency_program'] += 1
                return
            key = compiler_hash + ':' + source + ':' + digest
            if key not in cache:
                try:
                    p = subprocess.run([str(compiler),'sem',str(path),'--out-root',str(evidence/'sem_build')],
                                       cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace', timeout=25)
                    cache[key] = {'exit': p.returncode, 'detail': (p.stdout+'\n'+p.stderr)[-600:]}
                except subprocess.TimeoutExpired:
                    cache[key] = {'exit': -999, 'detail': 'semantic validation timeout'}
                dump(cache_path, cache)
            checks[source] = cache[key]
            if cache[key]['exit'] != 0:
                counts['excluded:semantic_rejection'] += 1
                return
            validation['semantic'] = 'passed'
        answer = messages[-1]['content']
        if kind == 'rutin_yaz' and re.search(r'\b(?:noop|dummy|placeholder|stub)\b', messages[1]['content'], re.I):
            counts['excluded:placeholder_routine'] += 1
            return
        records.append({'messages': [{'role':'system','content':SYSTEM}, messages[1], messages[2]],
                        'tur':kind,'kaynak':source,'source_sha256':digest,'validation':validation})

    input_rows=[json.loads(line) for split in ('train','valid') for line in (DATA/(split+'.jsonl')).open(encoding='utf-8')]
    pending={}
    for row in input_rows:
        if row.get('tur')!='program': continue
        path=WORKSPACE/row.get('kaynak','')
        if not path.is_file(): path=ROOT/row.get('kaynak','')
        if not path.is_file() or path.suffix.lower()!='.uxb' or path.stat().st_size>4000: continue
        if re.search(r'(?im)^\s*(?:INCLUDE|IMPORT|LIBTYPE)\b|CALL\s*\(\s*(?:DLL|API)\b',path.read_text(encoding='utf-8',errors='replace')): continue
        source=path.resolve().relative_to(WORKSPACE).as_posix()
        key=compiler_hash+':'+source+':'+sha(path)
        if key not in cache: pending[key]=path
    def precheck(item):
        key,path=item
        destination=evidence/'sem_build'/hashlib.sha256(key.encode()).hexdigest()[:16]
        try:
            result=subprocess.run([str(compiler),'sem',str(path),'--out-root',str(destination)],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=25)
            return key,{'exit':result.returncode,'detail':(result.stdout+'\n'+result.stderr)[-600:]}
        except subprocess.TimeoutExpired:
            return key,{'exit':-999,'detail':'semantic validation timeout'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(precheck,item) for item in pending.items()]
        for i,future in enumerate(as_completed(futures),1):
            key,value=future.result(); cache[key]=value
            if i%20==0: dump(cache_path,cache)
            if i%100==0: print(f'Semantic validation {i}/{len(futures)}',flush=True)
    dump(cache_path,cache)
    for row in input_rows: admit(row)
    # Current V2 templates replace the old, stale rule book. Their status notes
    # remain in the response; a design target is never converted to support.
    for name in ('03_program_yapisi.md','11_nesne.md','23_kararlar.md'):
        path = ROOT/'tools/kitap/kilavuz_v2/sablon'/name
        source = path.relative_to(WORKSPACE).as_posix()
        snapshot[source] = sha(path)
        for part in re.split(r'(?m)(?=^#{2,4} )', path.read_text(encoding='utf-8')):
            if not 100 <= len(part) <= 16000 or '{{' in part:
                continue
            title = part.splitlines()[0].lstrip('# ')
            records.append({'messages':[{'role':'system','content':SYSTEM},
                            {'role':'user','content':f'Güncel uXBasic V2 kılavuzunda {title} bölümünü, mevcut durum ve uygulama hedeflerini ayırarak anlat.'},
                            {'role':'assistant','content':part}], 'tur':'hedef_tasarim','kaynak':source,
                            'source_sha256':snapshot[source],'validation':{'source':'current','runtime':'not_claimed'}})
    # Connected components prevent leakage through the same file OR an identical
    # response reused under a different path. Split decisions are deterministic.
    parent = {}
    def find(x):
        parent.setdefault(x,x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(a,b):
        a,b = find(a),find(b)
        if a != b:
            parent[max(a,b)] = min(a,b)
    for r in records:
        response = hashlib.sha256(re.sub(r'\s+',' ',r['messages'][-1]['content']).strip().encode()).hexdigest()
        r['response_sha256'] = response
        union('source:'+r['kaynak'], 'response:'+response)
    essential = {find('source:'+r['kaynak']) for r in records if r['tur'] in ('dil_yasak','kural','hedef_tasarim')}
    splits = {'train':[], 'valid':[]}
    seen = set()
    for r in records:
        key = hashlib.sha256(json.dumps(r['messages'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if key in seen:
            counts['excluded:duplicate_conversation'] += 1
            continue
        seen.add(key)
        group = find('source:'+r['kaynak'])
        split = 'valid' if group not in essential and int(hashlib.sha256(group.encode()).hexdigest()[:8],16)%20 == 0 else 'train'
        r['group_id'] = hashlib.sha256(group.encode()).hexdigest()
        splits[split].append(r)
        counts[split+':'+r['tur']] += 1
    assert splits['train'] and splits['valid'], 'Empty training/validation split'
    for field in ('kaynak','response_sha256','group_id'):
        assert not {r[field] for r in splits['train']} & {r[field] for r in splits['valid']}, field+' leakage'
    for source,digest in snapshot.items():
        assert sha(WORKSPACE/source) == digest, 'Source changed during preparation: '+source
    for split,rows in splits.items():
        with (CLOUD/(split+'.jsonl')).open('w',encoding='utf-8',newline='\n') as f:
            for row in rows:
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
    dump(CLOUD/'source_snapshot.json',snapshot)
    report = {'schema':'uxb.cloud_training.v2','created_at':datetime.now(timezone.utc).isoformat(),
              'compiler':str(compiler),'compiler_sha256':compiler_hash,'counts':dict(counts),
              'train':len(splits['train']),'valid':len(splits['valid']),
              'source_files':len({r['kaynak'] for values in splits.values() for r in values if (WORKSPACE/r['kaynak']).is_file()}),
              'audited_source_files':len(snapshot),
              'semantic_sources_checked':len(checks),'semantic_sources_passed':sum(c['exit']==0 for c in checks.values()),
              'source_overlap':0,'response_overlap':0,'group_overlap':0,'gpu_training_executed':False,
              'files':{name:sha(CLOUD/name) for name in ('train.jsonl','valid.jsonl','source_snapshot.json')}}
    dump(CLOUD/'OZET.json',report)
    with zipfile.ZipFile(CLOUD/'egitim_bulut.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ('train.jsonl','valid.jsonl','source_snapshot.json','OZET.json'):
            z.write(CLOUD/name,name)
    report['zip_sha256'] = sha(CLOUD/'egitim_bulut.zip')
    dump(evidence/'cloud_training.json',report)
    print(json.dumps({k:v for k,v in report.items() if k != 'files'},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--compiler',type=Path,required=True)
    build(p.parse_args().compiler)
