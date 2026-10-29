#!/usr/bin/env python3
from __future__ import annotations
import argparse, ctypes, json
from pathlib import Path

VOID,I32,U32,I64,U64,F64,PTR,STRPTR=range(8)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ns=ap.parse_args(); root=Path(ns.root).resolve()
    dll=ctypes.CDLL(str(root/'bin'/'uxffi.dll'))
    test=ctypes.CDLL(str(root/'build'/'tests'/'ffi_contract'/'uxb_ffi_token_test.dll'))
    dll.uxffi_version.restype=ctypes.c_int
    dll.uxffi_max_args.restype=ctypes.c_int
    invoke=dll.uxffi_invoke10
    invoke.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_double),ctypes.c_char_p,ctypes.c_int]
    invoke.restype=ctypes.c_int
    copy=dll.uxffi_copy_string; copy.argtypes=[ctypes.c_uint32,ctypes.c_char_p,ctypes.c_int]; copy.restype=ctypes.c_int
    release=dll.uxffi_release_handle; release.argtypes=[ctypes.c_uint32]; release.restype=ctypes.c_int
    assert dll.uxffi_version() >= 120
    assert dll.uxffi_max_args() == 10
    target=str(root/'build'/'tests'/'ffi_contract'/'uxb_ffi_token_test.dll').encode()
    def call(name,ret,kinds=(),u64=(),f64=()):
        n=len(kinds); ka=(ctypes.c_int*max(1,n))(*list(kinds or [0])); ua=(ctypes.c_uint64*max(1,n))(*list(u64 or [0])); fa=(ctypes.c_double*max(1,n))(*list(f64 or [0.0])); ru=ctypes.c_uint64(); rf=ctypes.c_double(); err=ctypes.create_string_buffer(512)
        ok=invoke(target,name.encode(),ret,n,ka if n else None,ua if n else None,fa if n else None,ctypes.byref(ru),ctypes.byref(rf),err,512)
        return ok,ru.value,rf.value,err.value.decode(errors='replace')
    ok,token,_,err=call('uxb_test_open',PTR); assert ok and token and not err
    text=ctypes.create_string_buffer(b'uXBasic-token-roundtrip')
    ok,rv,_,err=call('uxb_test_set',I32,(PTR,STRPTR),(token,ctypes.addressof(text))); assert ok and rv==1,err
    ok,string_token,_,err=call('uxb_test_get',STRPTR,(PTR,),(token,)); assert ok and string_token,err
    out=ctypes.create_string_buffer(256); assert copy(string_token,out,256)==1; assert out.value==b'uXBasic-token-roundtrip'
    ok,total,_,err=call('uxb_test_sum10',I64,(I32,)*10,tuple(range(1,11))); assert ok and total==55,err
    ok,_,half,err=call('uxb_test_half',F64,(I32,),(7,)); assert ok and half==7.5,err
    ok,_,_,err=call('uxb_test_free',VOID,(PTR,),(token,)); assert ok,err
    ok,_,_,err=call('uxb_test_get',STRPTR,(PTR,),(token,)); assert not ok and 'stale' in err.lower(),err
    assert release(token)==0
    print(json.dumps({'marker':'UXFFI_CONTRACT_V120_PASS','version':dll.uxffi_version(),'maxArgs':dll.uxffi_max_args(),'sum10':total,'half':half},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
