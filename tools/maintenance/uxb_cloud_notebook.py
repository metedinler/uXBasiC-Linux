"""Produce the portable Colab/Kaggle QLoRA notebook; no local GPU fiction."""
import ast
import json
from pathlib import Path
import textwrap

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'tekdosyaklsoru/egitim/bulut/uxb_egitim_bulut.ipynb'
cells=[]
def md(text):
    cells.append(dict(cell_type='markdown',id=f'uxb-{len(cells):02}',metadata={},source=textwrap.dedent(text).strip()+'\n'))
def code(text):
    text=textwrap.dedent(text).strip()+'\n'; ast.parse(text)
    cells.append(dict(cell_type='code',id=f'uxb-{len(cells):02}',metadata={},source=text,execution_count=None,outputs=[]))

md('''
# uXBasic: güncel kaynaklardan bulut GPU eğitimi

`egitim_bulut.zip` dosyasını yükleyin; hücreleri sırayla çalıştırın.
Colab'da GPU çalışma zamanı seçin. Kaggle'da GPU ve Internet açık olmalıdır.
Bu defter gerçek QLoRA eğitimi, eğitim öncesi/sonrası doğrulama kaybı ve
adaptör dosyaları üretir. Bir veri paketi veya yalnız biçim kontrolü,
eğitilmiş model değildir. Ücretsiz GPU erişimi ve süre garantisi yoktur.

Veri, kaynak dosyası ve aynı yanıt üzerinden gruplara ayrılmıştır.
Kural ve tasarım hedefleri mevcut motor desteğiyle karıştırılmaz.
Semantik kontrolden geçen programların tüm motorlarda çalıştığı iddia edilmez.

Kaynaklar: [TRL 0.28 SFT](https://huggingface.co/docs/trl/v0.28.0/en/sft_trainer),
[Colab kaynak sınırları](https://research.google.com/colaboratory/faq.html).
''')
md('### 1. Veri paketini aç ve SHA-256 / ayrık kümeleri doğrula')
code('''
import hashlib, json, zipfile
from pathlib import Path
if Path('egitim_bulut.zip').exists():
    with zipfile.ZipFile('egitim_bulut.zip') as archive:
        for name in ['train.jsonl','valid.jsonl','source_snapshot.json','OZET.json']:
            Path(name).write_bytes(archive.read(name))
manifest=json.loads(Path('OZET.json').read_text(encoding='utf-8'))
for name,digest in manifest['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest, name+' SHA256 mismatch'
rows={split:[json.loads(line) for line in Path(split+'.jsonl').read_text(encoding='utf-8').splitlines()] for split in ['train','valid']}
for field in ['kaynak','group_id','response_sha256']:
    assert not {r[field] for r in rows['train']} & {r[field] for r in rows['valid']}, field+' leakage'
assert len(rows['train'])==manifest['train'] and len(rows['valid'])==manifest['valid']
assert all([m['role'] for m in r['messages']]==['system','user','assistant'] for split in rows for r in rows[split])
print('Paket doğrulandı:',manifest['created_at'],{s:len(r) for s,r in rows.items()})
print('Kaynak dosyaları:',manifest['source_files'],'; paket üretildiğinde GPU eğitimi:',manifest['gpu_training_executed'])
''')
md('### 2. GPU ve bağımlılıklar')
code('''
import subprocess, sys
import torch
assert torch.cuda.is_available(), 'GPU yok: Colab Çalışma zamanı türünden GPU seçin. Bu hücre CPU eğitimine sessizce geçmez.'
print(torch.cuda.get_device_name(0), 'VRAM GiB:', round(torch.cuda.get_device_properties(0).total_memory/2**30,1))
subprocess.check_call([sys.executable,'-m','pip','install','-q',
    'trl==0.28.0','transformers>=4.56.2,<5','peft>=0.17,<0.20',
    'datasets>=3,<5','accelerate>=1.4,<2','bitsandbytes>=0.48,<0.50'])
Path('environment.freeze.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
''')
md('### 3. Model, örnek sayısı ve uzunluk kontrolü')
code('''
import random
from collections import Counter
from huggingface_hub import model_info
from datasets import Dataset
from transformers import AutoTokenizer
MODEL='Qwen/Qwen2.5-Coder-3B-Instruct'
REVISION=model_info(MODEL).sha
ORNEK=0       # 0=tümü; örneğin 3000, temel kural/hedef örneklerini koruyarak sınırlar
UZUNLUK=1536
EPOCH=1
tok=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
tok.eos_token='<|im_end|>'
tok.pad_token=tok.eos_token
tok.padding_side='right'
rng=random.Random(7)
essential=[r for r in rows['train'] if r['tur'] in ['kural','dil_yasak','hedef_tasarim']]
other=[r for r in rows['train'] if r['tur'] not in ['kural','dil_yasak','hedef_tasarim']]
rng.shuffle(other)
train_rows=essential+other[:max(0,ORNEK-len(essential))] if ORNEK else essential+other
rng.shuffle(train_rows)
def prepare(selected):
    kept=[]; dropped=0
    for r in selected:
        ids=tok.apply_chat_template(r['messages'],tokenize=True,add_generation_prompt=False)
        # Do not truncate away a response or leave a half-written code block.
        if len(ids)>UZUNLUK:
            dropped+=1
            continue
        kept.append({'prompt':r['messages'][:-1],'completion':r['messages'][-1:]})
    assert kept, 'Uzunluk kontrolünden sonra veri kalmadı'
    return Dataset.from_list(kept),dropped
train_ds,train_dropped=prepare(train_rows)
valid_ds,valid_dropped=prepare(rows['valid'])
data_check=dict(train=len(train_ds),validation=len(valid_ds),train_too_long=train_dropped,valid_too_long=valid_dropped,model=MODEL,revision=REVISION,length=UZUNLUK,seed=7)
Path('data_check.json').write_text(json.dumps(data_check,indent=2),encoding='utf-8')
print(data_check)
''')
md('### 4. Gerçek 4-bit LoRA eğitimi ve ayrı doğrulama')
code('''
import math
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from transformers.trainer_utils import get_last_checkpoint
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,quantization_config=quant,device_map={'':0},torch_dtype=torch.float16)
model.config.use_cache=False
model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True)
lora=LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,task_type='CAUSAL_LM',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])
run_config=dict(files=manifest['files'],model=MODEL,revision=REVISION,examples=ORNEK,length=UZUNLUK,epochs=EPOCH,seed=7,
    train_rows=len(train_ds),valid_rows=len(valid_ds),lora_rank=16,learning_rate=2e-4)
run_signature=hashlib.sha256(json.dumps(run_config,sort_keys=True).encode()).hexdigest()
run_dir=Path('cikti_'+run_signature[:16]); run_dir.mkdir(exist_ok=True)
identity=run_dir/'run_config.json'
if identity.exists():
    assert json.loads(identity.read_text(encoding='utf-8'))==run_config, 'Checkpoint veri/model ayarları farklı'
identity.write_text(json.dumps(run_config,indent=2),encoding='utf-8')
cfg=SFTConfig(output_dir=str(run_dir),num_train_epochs=EPOCH,per_device_train_batch_size=1,per_device_eval_batch_size=1,
    gradient_accumulation_steps=16,learning_rate=2e-4,lr_scheduler_type='cosine',warmup_ratio=0.03,
    logging_steps=10,save_steps=100,eval_strategy='steps',eval_steps=100,fp16=True,max_length=UZUNLUK,
    gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},packing=False,
    report_to='none',completion_only_loss=True,assistant_only_loss=False,eos_token='<|im_end|>',seed=7,data_seed=7)
trainer=SFTTrainer(model=model,args=cfg,train_dataset=train_ds,eval_dataset=valid_ds,peft_config=lora,processing_class=tok)
before=trainer.evaluate(metric_key_prefix='before')
checkpoint=get_last_checkpoint(str(run_dir))
trained=trainer.train(resume_from_checkpoint=checkpoint)
after=trainer.evaluate(metric_key_prefix='after')
assert trainer.state.global_step>0, 'Eğitim adımı yok; adaptör hazır sayılamaz'
assert math.isfinite(before['before_loss']) and math.isfinite(after['after_loss'])
metrics=dict(before=before,after=after,steps=trainer.state.global_step,model=MODEL,revision=REVISION,
    validation_loss_improved=after['after_loss']<before['before_loss'],data_sha256=manifest['files'],run=run_config)
print(json.dumps(metrics,indent=2))
''')
md('### 5. Adaptörü, ölçümleri ve tekrar üretim bilgisini indir')
code('''
import shutil
adapter=Path('uxb_adaptor'); adapter.mkdir(exist_ok=True)
trainer.save_model(str(adapter)); tok.save_pretrained(str(adapter))
assert (adapter/'adapter_model.safetensors').is_file()
assert (adapter/'adapter_model.safetensors').stat().st_size>0
(adapter/'training_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
for name in ['OZET.json','source_snapshot.json','data_check.json','environment.freeze.txt']:
    shutil.copy2(name,adapter/name)
shutil.make_archive('uxb_adaptor','zip',str(adapter))
print('Adaptör:',Path('uxb_adaptor.zip').stat().st_size,'bayt; doğrulama iyileşti:',metrics['validation_loss_improved'])
print('Bu, compiler testlerinden geçmiş model iddiası değildir. Döndüğünde yerel uXBasic kabul testleri yapılacak.')
try:
    from google.colab import files
except ImportError:
    print('Kaggle Output bölümünden uxb_adaptor.zip dosyasını indirin.')
else:
    files.download('uxb_adaptor.zip')
''')
md('''
### Sonraki adım
`uxb_adaptor.zip` dosyasını bu bilgisayardaki `uxb/tekdosyaklsoru/egitim/bulut/`
klasörüne koyun. Taban model/revizyon ve ölçümler doğrulandıktan sonra
Ollama dönüşümü ve gerçek uXBasic kod üretme/derleme testleri yapılır.
Yalnız kaybın azalması, dilin bütün özelliklerinin doğru üretildiğini kanıtlamaz.
''')
notebook=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.11')),cells=cells)
TARGET.write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding='utf-8')
print('Notebook generated:',TARGET,'cells:',len(cells),'code cells syntax checked')
