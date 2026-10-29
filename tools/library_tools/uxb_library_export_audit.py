#!/usr/bin/env python3
"""Audit built uXBasic DLL architecture and exports without third-party Python packages."""
from __future__ import annotations
import argparse, csv, json, re, struct, sys
from dataclasses import dataclass, asdict
from pathlib import Path

CALL_RE = re.compile(
    r'CALL\s*\(\s*DLL\s*,\s*"([^"]+\.dll)"\s*,\s*"([^"]+)"', re.I
)
MACHINE_NAMES = {0x014C: "x86", 0x8664: "x64", 0xAA64: "arm64"}

@dataclass
class ExportRow:
    dll: str
    path: str
    machine: str
    status: str
    expected_count: int
    exported_count: int
    missing_count: int
    missing_symbols: str
    message: str

class PEError(RuntimeError):
    pass

def u16(data: bytes, off: int) -> int:
    return struct.unpack_from('<H', data, off)[0]

def u32(data: bytes, off: int) -> int:
    return struct.unpack_from('<I', data, off)[0]

def rva_to_offset(rva: int, sections: list[tuple[int,int,int,int]]) -> int:
    for virtual_address, virtual_size, raw_ptr, raw_size in sections:
        size = max(virtual_size, raw_size)
        if virtual_address <= rva < virtual_address + size:
            return raw_ptr + (rva - virtual_address)
    raise PEError(f"RVA 0x{rva:x} is outside sections")

def parse_pe(path: Path) -> tuple[str, set[str]]:
    data = path.read_bytes()
    if len(data) < 0x100 or data[:2] != b'MZ':
        raise PEError('not a PE file')
    pe = u32(data, 0x3C)
    if pe + 24 > len(data) or data[pe:pe+4] != b'PE\0\0':
        raise PEError('PE signature missing')
    machine = u16(data, pe + 4)
    section_count = u16(data, pe + 6)
    optional_size = u16(data, pe + 20)
    optional = pe + 24
    magic = u16(data, optional)
    if magic == 0x20B:      # PE32+
        data_dir = optional + 112
    elif magic == 0x10B:    # PE32
        data_dir = optional + 96
    else:
        raise PEError(f'unsupported optional header magic 0x{magic:x}')
    export_rva = u32(data, data_dir)
    export_size = u32(data, data_dir + 4)
    section_table = optional + optional_size
    sections = []
    for i in range(section_count):
        off = section_table + i * 40
        if off + 40 > len(data): raise PEError('truncated section table')
        virtual_size = u32(data, off + 8)
        virtual_address = u32(data, off + 12)
        raw_size = u32(data, off + 16)
        raw_ptr = u32(data, off + 20)
        sections.append((virtual_address, virtual_size, raw_ptr, raw_size))
    exports: set[str] = set()
    if export_rva and export_size:
        ed = rva_to_offset(export_rva, sections)
        if ed + 40 > len(data): raise PEError('truncated export directory')
        number_of_names = u32(data, ed + 24)
        address_of_names = u32(data, ed + 32)
        names_off = rva_to_offset(address_of_names, sections) if number_of_names else 0
        for i in range(number_of_names):
            name_rva = u32(data, names_off + i * 4)
            noff = rva_to_offset(name_rva, sections)
            end = data.find(b'\0', noff)
            if end < 0: raise PEError('unterminated export name')
            exports.add(data[noff:end].decode('ascii', errors='replace'))
    return MACHINE_NAMES.get(machine, f'0x{machine:04x}'), exports

def resolve_root(value: str) -> Path:
    p = Path(value).resolve()
    if (p/'runtime_ext').is_dir() and (p/'libsx').is_dir(): return p
    if (p/'uxb'/'runtime_ext').is_dir(): return p/'uxb'
    raise SystemExit(f'uXBasic root not found: {p}')

def wrapper_exports(root: Path) -> dict[str,set[str]]:
    result: dict[str,set[str]] = {}
    for p in root.glob('libsx/*/*.bas'):
        if 'PLACEHOLDER' in p.name.upper(): continue
        text = p.read_text(encoding='utf-8', errors='ignore')
        for dll, symbol in CALL_RE.findall(text):
            result.setdefault(dll.lower(), set()).add(symbol)
    return result

def find_dll(root: Path, dll: str) -> Path | None:
    candidates = [
        root/'dist/libraries/bin'/dll,
        root/'bin'/dll,
        root/'dist/runtime_ext'/dll,
    ]
    for c in candidates:
        if c.is_file(): return c
    return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--report-dir', default='reports/libraries/exports')
    ap.add_argument('--require-all', action='store_true')
    ap.add_argument('--require-x64', action='store_true')
    ap.add_argument('--require-required', action='store_true', help='require manifest libraries marked required')
    ap.add_argument('--only-dll', action='append', default=[], help='audit only this DLL name; repeatable')
    args = ap.parse_args()
    root = resolve_root(args.root)
    expected = wrapper_exports(root)
    only_dlls={str(x).lower() for x in args.only_dll}
    if only_dlls:
        expected={dll:symbols for dll,symbols in expected.items() if dll in only_dlls}
    required_dlls: set[str] = set()
    manifest_path=root/'manifests/uxb_library_system.json'
    if manifest_path.is_file():
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        required_dlls={str(x.get('dll','')).lower() for x in manifest.get('libraries',[]) if x.get('required') and x.get('dll')}
        if only_dlls: required_dlls &= only_dlls
        for dll in required_dlls: expected.setdefault(dll,set())
    rows: list[ExportRow] = []
    failures = 0
    for dll, symbols in sorted(expected.items()):
        path = find_dll(root, dll)
        if path is None:
            status = 'MISSING'
            if args.require_all or (args.require_required and dll in required_dlls): failures += 1
            rows.append(ExportRow(dll,'','',status,len(symbols),0,len(symbols),';'.join(sorted(symbols)),'DLL not built/deployed'))
            continue
        try:
            machine, exported = parse_pe(path)
            missing = sorted(symbols - exported)
            status = 'PASS'
            message = ''
            if missing:
                status = 'MISSING_EXPORTS'; failures += 1
            if args.require_x64 and machine != 'x64':
                status = 'WRONG_ARCH'; failures += 1
                message = f'expected x64, got {machine}'
            rows.append(ExportRow(dll,str(path.relative_to(root)).replace('\\','/'),machine,status,len(symbols),len(exported),len(missing),';'.join(missing),message))
        except Exception as exc:
            failures += 1
            rows.append(ExportRow(dll,str(path.relative_to(root)).replace('\\','/'),'','BAD_PE',len(symbols),0,len(symbols),';'.join(sorted(symbols)),str(exc)))
    # The interpreter bridge has no .bas wrapper but its three exports are contractual.
    bridge = find_dll(root, 'uxffi.dll')
    if bridge and (not only_dlls or 'uxffi.dll' in only_dlls):
        try:
            machine, exported = parse_pe(bridge)
            want={'uxffi_version','uxffi_invoke10','uxffi_copy_string','uxffi_release_handle','uxffi_clear_handles','uxffi_shutdown'}
            missing=sorted(want-exported)
            status='PASS' if not missing else 'MISSING_EXPORTS'
            if missing: failures += 1
            if args.require_x64 and machine!='x64': status='WRONG_ARCH'; failures += 1
            rows.append(ExportRow('uxffi.dll',str(bridge.relative_to(root)).replace('\\','/'),machine,status,len(want),len(exported),len(missing),';'.join(missing),''))
        except Exception as exc:
            failures += 1
            rows.append(ExportRow('uxffi.dll',str(bridge.relative_to(root)).replace('\\','/'),'','BAD_PE',6,0,6,'',str(exc)))
    out=root/args.report_dir; out.mkdir(parents=True,exist_ok=True)
    with (out/'dll_export_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(ExportRow.__dataclass_fields__)); w.writeheader(); w.writerows(asdict(r) for r in rows)
    summary={
        'schema':'uxb.library_export_audit.v1','status':'PASS' if failures==0 else 'FAIL',
        'failure_count':failures,'dll_count':len(rows),'rows':[asdict(r) for r in rows]
    }
    (out/'dll_export_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"DLL export audit status={summary['status']} dlls={len(rows)} failures={failures}")
    return 0 if failures==0 else 1

if __name__=='__main__':
    raise SystemExit(main())
