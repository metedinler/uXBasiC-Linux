"""Mechanical coordination inventory; recorded status is not semantic acceptance."""
import argparse, collections, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ISSUE_ID=r'S-\d+(?:-[A-Za-z0-9]+|[A-Za-z]+)?'
def sid(v):
    m=re.fullmatch(r'S-(\d+)(.*)',v)
    return f'S-{int(m[1]):03d}{m[2]}' if m else v

def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',default=str(ROOT/'reports/coordination_status')); args=p.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    text=(ROOT/'ai_koordinasyon/SORUN_TAKIP.md').read_text(encoding='utf-8-sig')
    # Imported early issues (S-020..S-045) use third-level headings. They
    # remain first-class records; dated update headings are not new issues.
    heads=list(re.finditer(r'^#{2,3}\s+('+ISSUE_ID+r')\b[^\n]*',text,re.M))
    issues=[]
    for i,m in enumerate(heads):
        block=text[m.end():heads[i+1].start() if i+1<len(heads) else len(text)]
        status=re.search(r'\*\*Durum:\*\*\s*`([^`]+)`',block)
        if not status: status=re.search(r'\*\*Durum:\*\*\s*([^\n·]+)',block)
        if not status: status=re.search(r'`((?:YAPILDI|KISMEN|ACIK|TASARIM|KARAR)[^`]*)`',m[0])
        raw=status[1].strip() if status else 'AYRISTIRILAMADI'
        normalized=raw.upper().replace('_','-').replace('Ğ','G').replace('İ','I').replace('Ç','C')
        if 'KISM' in normalized: category='KISMEN'
        elif normalized.startswith('YAPILDI') and 'DOGRULANDI' in normalized: category='KAYITTA-DOGRULANDI'
        elif normalized.startswith('YAPILDI'): category='KAYITTA-YAPILDI'
        elif any(v in normalized for v in ('TASARIM','PLAN','HEDEF')): category='PLAN-HEDEF'
        elif any(v in normalized for v in ('ACIK','DEVAM','BEKLIYOR')): category='ACIK-DEVAM'
        else: category='DIGER-BELIRSIZ'
        issues.append(dict(id=sid(m[1]),title=m[0].lstrip('# '),status=raw,category=category,line=text.count('\n',0,m.start())+1))
    groups=collections.defaultdict(list)
    for row in issues: groups[row['id']].append(row)
    mapping=[]
    for line in (ROOT/'tools/kitap/kilavuz_v2/veri/sorun_eslemesi.txt').read_text(encoding='utf-8-sig').splitlines():
        m=re.match(r'\s*(G-[\w-]+)\s*=\s*('+ISSUE_ID+r')\s*$',line)
        if m: mapping.append(dict(catalog=m[1],issue=sid(m[2])))
    data=dict(schema='uxb.coordination_inventory.v1',scope='Mechanical recorded status; not a feature completion percentage or fresh execution claim',issues=len(issues),unique_ids=len(groups),categories=dict(collections.Counter(x['category'] for x in issues)),catalog_mappings=len(mapping),missing_issue_ids=[x for x in mapping if x['issue'] not in groups],duplicate_issue_ids={k:[x['line'] for x in v] for k,v in groups.items() if len(v)>1},records=issues)
    (out/'status.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Koordinasyon kayıt dökümü','','Bu sayım kayıtların yazılı durumudur; özelliklerin tamamlanma yüzdesi veya yeni motor kabulü değildir.','','| Durum grubu | Kayıt |','|---|---:|']+[f'| {k} | {v} |' for k,v in data['categories'].items()]
    lines+=['',f"Kayıt: {len(issues)}; benzersiz S kimliği: {len(groups)}; V2 eşlemesi: {len(mapping)}.",f"Karşılığı bulunamayan eşleme: {len(data['missing_issue_ids'])}; tekrarlı S kimliği: {len(data['duplicate_issue_ids'])}.",'','Tam satır/kimlik/durum listesi status.json içindedir. Açık özelliklerin kanıtlı sırası ai_koordinasyon/CANLI_TAKIP.md içindedir.']
    (out/'status.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
