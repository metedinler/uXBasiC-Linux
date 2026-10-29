from __future__ import annotations
import argparse, json, pathlib, re, sys

REQUIRED_API = 131
MAX_ARGS = 10

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--json-out')
    ns=ap.parse_args()
    root=pathlib.Path(ns.root).resolve()
    checks=[]
    def add(name, ok, detail=''):
        checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    required=[
      'src/parser/parser/parser_stmt_dispatch.fbs',
      'src/semantic/ffi_signature_binding.fbs',
      'src/codegen/x64/ffi_call_backend.fbs',
      'src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs',
      'src/interpreter/mir/mir_interp_ffi.fbs',
      'src/runtime/exec/exec_ffi_bridge10.fbs',
      'src/runtime/exec/exec_ffi_runtime.fbs',
      'src/runtime/ffi/runtime_ffi.fbs',
      'runtime_ext/uxffi/uxffi.c','runtime_ext/uxffi/uxffi.h',
      'tests/libraries/ffi_final/test_uxffi_uxconfig_roundtrip.py',
      'tests/libraries/uxjsruntime/test_generated_js_e2e.py',
      'tools/release/package_uxbasic_distribution_final.ps1',
      'compiler/scripts/run_final_ffi_quickjs_release_gate.ps1',
    ]
    missing=[x for x in required if not (root/x).is_file()]
    add('required_files',not missing,', '.join(missing))
    if missing: return emit(ns,checks)
    def read(rel): return (root/rel).read_text(encoding='utf-8',errors='replace')
    parser=read('src/parser/parser/parser_stmt_dispatch.fbs')
    sem=read('src/semantic/ffi_signature_binding.fbs')
    x64=read('src/codegen/x64/ffi_call_backend.fbs')
    gate=read('src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs')
    mir=read('src/interpreter/mir/mir_interp_ffi.fbs')
    bridge=read('src/runtime/exec/exec_ffi_bridge10.fbs')
    ex=read('src/runtime/exec/exec_ffi_runtime.fbs')
    rt=read('src/runtime/ffi/runtime_ffi.fbs')
    c=read('runtime_ext/uxffi/uxffi.c')
    h=read('runtime_ext/uxffi/uxffi.h')
    build=read('runtime_ext/uxffi/build_uxffi_dll.bat')
    add('parser_all_call_nodes', all(x in parser for x in ['CALL_DLL_STMT','CALL_API_STMT','CALL_STMT','CALL_EXPR','Case "CALL_STMT", "CALL_EXPR", "CALL"']))
    add('parser_counts_runtime_args', 'UXB_FFI_MAX_RUNTIME_ARGS As Integer = 10' in parser and 'NodeChildCount' in parser and 'argument type-list exceeds the ABI10 limit' in parser)
    add('parser_rejects_unsupported_convention', all(x in parser for x in ['FASTCALL','THISCALL','VECTORCALL']))
    add('semantic_abi10', 'Const UXB_FFI_MAX_ARGS As Integer = 10' in sem)
    add('x64_api_dll_normalization', 'resolvedCallKind = "API"' in x64 and 'entryOut.dllName &= ".dll"' in x64)
    add('x64_gate_abi10', 'sig.argCount > 10' in gate and 'unsupported ABI10 return type' in gate and 'unsupported ABI10 argument type' in gate)
    add('api_131_header', '#define UXFFI_API_VERSION 131' in h and '#define UXFFI_MAX_ARGS 10' in h)
    add('api_131_source', 'return UXFFI_API_VERSION' in c and 'uxffi_max_args(void)' in c)
    exports=['uxffi_version','uxffi_max_args','uxffi_invoke10','uxffi_string_length','uxffi_copy_string','uxffi_release_handle','uxffi_clear_handles','uxffi_shutdown']
    add('complete_exports', all(x in h and x in c and x in build for x in exports))
    add('generation_tokens', all(x in c for x in ['UXFFI_HANDLE_GENERATION_MASK','next_generation','decode_token','stale or invalid pointer handle token']))
    add('owned_string_snapshot', all(x in c for x in ['duplicate_bounded_string','ReadProcessMemory','VirtualQuery','store_handle(copy, 1)']))
    add('dynamic_string_copy', 'uxffi_string_length' in c and 'out_capacity > length' in c and 'length + 1u' in c)
    add('freebasic_warmup', 'uxfb_runtime_ready' in c and 'is_required_freebasic_module' in c)
    add('executor_api_gate', 'UXFFI_REQUIRED_VERSION As Long = 131' in bridge and 'uxffi_max_args' in bridge)
    add('runtime_api_gate', 'UXB_RTFFI_REQUIRED_VERSION As Long = 131' in rt and 'uxffi_max_args' in rt)
    add('mir_api_gate', 'UXB_MIRFFI_REQUIRED_VERSION As Long = 131' in mir and 'uxffi_max_args' in mir)
    add('fail_closed_typed_bridge', 'Typed ABI10 execution is fail-closed' in bridge and 'ABI10 requires bin\\uxffi.dll API 131' in bridge)
    add('all_dynamic_strptr_consumers', all('uxffi_string_length' in x and 'CAllocate(requiredBytes)' in x for x in [bridge,rt,mir]))
    add('legacy_args_i32_runtime', 'legacy CALL(DLL/API) records' in rt and 'argTypes(i) = "I32"' in rt)
    add('legacy_args_i32_mir', 'Legacy calls without an explicit ABI10 type list are integer calls' in mir and 'argTypes(i) = "I32"' in mir)
    # Crucial pointer-width rule: I64/U64/PTR accept U64_PTR; U32 remains strictly INTEGER.
    add('u64_ptr_preserved', ex.count('argValue.valueType <> "U64_PTR"') >= 3 and 'u64Out = ExecValueToU64(iv)' in ex)
    u32=re.search(r'Case "U32"(.*?)(?=\n\s*Case )',ex,re.S)
    add('u32_rejects_ptr_token', bool(u32) and 'U64_PTR' not in u32.group(1) and '32-bit integer' in u32.group(1))
    add('debug_removed','[UXB_FFI_DEBUG]' not in ex)
    add('no_old_api_literals', not re.search(r'UXFFI_(?:REQUIRED_|API_)?VERSION[^\n]*(?:110|120)', bridge+'\n'+rt+'\n'+mir+'\n'+h))
    # Detect the exact PowerShell bug previously producing fake PASS.
    ps_files=list(root.rglob('*.ps1'))
    bad=[]
    for f in ps_files:
        t=f.read_text(encoding='utf-8',errors='replace')
        if re.search(r'param\s*\([^)]*\[string\[\]\]\s*\$Args\b',t,re.I|re.S): bad.append(str(f.relative_to(root)))
    add('no_powershell_args_collision',not bad,', '.join(bad))
    nested=[x for x in ['runtime_ext/runtime_ext','libsx/libsx','manifests/manifests'] if (root/x).exists()]
    add('no_nested_stale_trees',not nested,'Quarantine before release: '+', '.join(nested))
    return emit(ns,checks)

def emit(ns,checks):
    status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL'
    report={'schema':'uxb.final-ffi-quickjs-static.v1','status':status,'checks':checks}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if ns.json_out:
        p=pathlib.Path(ns.json_out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text+'\n',encoding='utf-8')
    print(text)
    return 0 if status=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
