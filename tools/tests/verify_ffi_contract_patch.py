from __future__ import annotations
from pathlib import Path
import argparse, json, re

def read(p: Path) -> str:
    return p.read_text(encoding='utf-8-sig', errors='replace')

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--json-out',default='');ns=ap.parse_args()
    root=Path(ns.root).resolve();errors=[];checks=[]
    def add(name,ok,msg=''):
        checks.append({'name':name,'ok':bool(ok)}); 
        if not ok: errors.append(msg or name)
    rels={
      'parser':'src/parser/parser/parser_stmt_dispatch.fbs','semantic':'src/semantic/ffi_signature_binding.fbs',
      'mir':'src/interpreter/mir/mir_interp_ffi.fbs','bridge':'src/runtime/exec/exec_ffi_bridge10.fbs',
      'exec':'src/runtime/exec/exec_ffi_runtime.fbs','x64':'src/codegen/x64/ffi_call_backend.fbs',
      'gate':'src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs','c':'runtime_ext/uxffi/uxffi.c','h':'runtime_ext/uxffi/uxffi.h'
    }
    missing=[r for r in rels.values() if not (root/r).is_file()]
    add('required_files',not missing,'missing: '+', '.join(missing))
    if missing: return emit(ns,root,errors,checks)
    t={k:read(root/v) for k,v in rels.items()}
    add('parser_all_forms',all(x in t['parser'] for x in ['CALL_DLL_STMT','CALL_API_STMT','CALL_STMT','CALL_EXPR','UXB_FFI_MAX_CALL_CHILDREN As Integer = UXB_FFI_MAX_RUNTIME_ARGS + 6']))
    add('parser_type_count','argument type-list count mismatch' in t['parser'])
    add('semantic_10','Const UXB_FFI_MAX_ARGS As Integer = 10' in t['semantic'])
    add('x64_api_suffix','resolvedCallKind = "API"' in t['x64'] and 'entryOut.dllName &= ".dll"' in t['x64'])
    add('x64_gate','sig.argCount > 10' in t['gate'] and 'unsupported ABI10 argument type' in t['gate'])
    add('api131','#define UXFFI_API_VERSION 131' in t['h'] and 'return UXFFI_API_VERSION' in t['c'])
    add('maxargs','#define UXFFI_MAX_ARGS 10' in t['h'] and 'uxffi_max_args(void)' in t['c'])
    add('version_parity',all(x in y for x,y in [('UXB_MIRFFI_REQUIRED_VERSION As Long = 131',t['mir']),('UXFFI_REQUIRED_VERSION As Long = 131',t['bridge'])]))
    add('legacy_i32','Legacy calls without an explicit ABI10 type list are integer calls' in t['mir'] and 'argTypes(i) = "I32"' in t['mir'])
    add('dynamic_strptr',all('uxffi_string_length' in y and 'CAllocate(requiredBytes)' in y for y in [t['mir'],t['bridge']]))
    add('strptr_input_native_keepalive','case UXFFI_STRPTR: values_ptr[i] = (void *)(uintptr_t)arg_u64[i]' in t['c'])
    add('ptr_token_generation',all(x in t['c'] for x in ['decode_token','next_generation','stale or invalid pointer handle token']))
    add('owned_snapshot',all(x in t['c'] for x in ['duplicate_bounded_string','store_handle(copy, 1)','uxffi_string_length']))
    add('debug_removed','[UXB_FFI_DEBUG]' not in t['exec'])
    for k in ['parser','semantic','mir','bridge','exec','x64','gate']:
        a=len(re.findall(r'(?im)^\s*(?:private\s+|public\s+)?function\b',t[k]));b=len(re.findall(r'(?im)^\s*end\s+function\b',t[k]));add('function_balance_'+k,a==b,f'{k} function balance {a}/{b}')
    return emit(ns,root,errors,checks)

def emit(ns,root,errors,checks):
    d={'schema':'uxb.ffi.contract.static.v3','status':'FAIL' if errors else 'PASS','source_root':str(root),'errors':errors,'check_count':len(checks),'checks':checks}
    s=json.dumps(d,ensure_ascii=False,indent=2)
    if ns.json_out:
        p=Path(ns.json_out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s+'\n',encoding='utf-8')
    print(s);return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
