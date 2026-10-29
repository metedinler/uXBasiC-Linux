#!/usr/bin/env python3
"""Inventory shipped DLLs and uXBasic wrapper signatures."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PURPOSE_RULES = [
    (r"uxraylib|raylib|glfw", "Oyun, pencere, 2B/3B grafik, giriş ve ses"),
    (r"uxsdl3|sdl3", "Yedek platform, pencere, giriş, gamepad ve ses"),
    (r"uxterminal", "ANSI terminal GUI, terminal sprite ve kaydırma"),
    (r"uxlogic|lua", "Lua betik, Prolog süreç köprüsü ve fuzzy mantık"),
    (r"uxcapi|uxcabi|uxffi|ffi", "C ABI, dinamik DLL çağrısı ve aggregate köprüsü"),
    (r"uxjs|quickjs", "JavaScript/QuickJS çalışma zamanı"),
    (r"python", "Python gömme ve çağrı köprüsü"),
    (r"openblas|math|matrix|tensor|stats", "Sayısal hesaplama, matris ve istatistik"),
    (r"tbb|uv|pthread", "Paralellik, olay döngüsü ve thread çalışma bağımlılığı"),
    (r"sqlite|duck|data|collection", "Veri, koleksiyon ve sorgu"),
    (r"ssl|crypto|curl|http|net", "Ağ, HTTP ve kriptografi"),
    (r"audio|sound|miniaudio", "Ses aygıtı ve ses işleme"),
    (r"image|png|jpeg|webp|zlib", "Görüntü/kodlayıcı ve sıkıştırma"),
]


def purpose(name: str) -> str:
    lowered = name.lower()
    for pattern, description in PURPOSE_RULES:
        if re.search(pattern, lowered):
            return description
    return "Genel uXBasic yerel çalışma veya üçüncü taraf bağımlılığı"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exports(path: Path, objdump: Path | None) -> list[str]:
    if not objdump or not objdump.exists():
        return []
    result = subprocess.run(
        [str(objdump), "-p", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )
    in_names = False
    names: list[str] = []
    for line in result.stdout.splitlines():
        if "[Ordinal/Name Pointer] Table" in line:
            in_names = True
            continue
        if in_names:
            # GNU objdump on PE/COFF prints e.g.:
            # [   0] +base[   1]  0000 uxcapi_version
            match = re.match(r"\s*\[\s*\d+\]\s+\+base\[\s*\d+\]\s+[0-9A-Fa-f]+\s+(.+?)\s*$", line)
            if not match:
                match = re.match(r"\s*\[\s*\d+\]\s+([A-Za-z_?@][^\s]*)\s*$", line)
            if match:
                symbol = match.group(1).strip()
                if symbol and not symbol.startswith('+base['): names.append(symbol)
            elif names and not line.strip():
                break
    return names


DECL_RE = re.compile(
    r"^\s*(FUNCTION|SUB)\s+([A-Za-z_][A-Za-z0-9_.]*)\s*"
    r"\((.*?)\)\s*(?:AS\s+([A-Za-z0-9_]+))?\s*$", re.I
)
PARAM_RE = re.compile(
    r"(?:BYVAL\s+|BYREF\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+AS\s+([A-Za-z0-9_]+)", re.I
)
CALL_RE = re.compile(
    r'CALL\s*\(\s*DLL\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*'
    r'([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)(?:\s*,\s*"([^"]*)")?', re.I
)


def wrapper_api(path: Path, root: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    namespace = ""
    result: list[dict] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        ns = re.match(r"NAMESPACE\s+([A-Za-z_][A-Za-z0-9_.]*)", stripped, re.I)
        if ns:
            namespace = ns.group(1)
        decl = DECL_RE.match(lines[index])
        if not decl:
            index += 1
            continue
        kind, name, raw_params, return_type = decl.groups()
        params = [{"name": n, "type": t.upper()} for n, t in PARAM_RE.findall(raw_params)]
        if kind.upper() == "SUB":
            return_type = "VOID"
        connection = None
        scan = index + 1
        end_token = "END " + kind.upper()
        while scan < len(lines) and lines[scan].strip().upper() != end_token:
            match = CALL_RE.search(lines[scan])
            if match:
                dll, symbol, native_return, convention, signature = match.groups()
                connection = {
                    "dll": dll,
                    "symbol": symbol,
                    "return": native_return.upper(),
                    "convention": convention.upper(),
                    "signature": signature or "",
                }
                break
            scan += 1
        qualified = f"{namespace}.{name}" if namespace else name
        syntax_params = ", ".join(f"{p['name']} AS {p['type']}" for p in params)
        syntax = f"{kind.upper()} {qualified}({syntax_params})"
        if return_type and kind.upper() == "FUNCTION":
            syntax += f" AS {return_type.upper()}"
        result.append({
            "wrapper": path.relative_to(root).as_posix(),
            "name": qualified,
            "kind": kind.upper(),
            "parameters": params,
            "return": (return_type or "VARIANT").upper(),
            "syntax": syntax,
            "connection": connection,
        })
        index = scan + 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--objdump", default=r"C:\msys64\ucrt64\bin\objdump.exe")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    objdump = Path(args.objdump) if args.objdump else None
    manifest_path = root / "manifests" / "uxb_library_system.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = {
        item.get("dll", "").lower()
        for item in manifest.get("libraries", [])
        if item.get("dll")
    }
    for item in manifest.get("libraries", []):
        declared.update(alias.lower() for alias in item.get("dll_aliases", []))

    dll_paths: dict[str, list[Path]] = {}
    for folder in (root / "bin", root / "dist" / "libraries" / "bin"):
        if folder.exists():
            for path in folder.glob("*.dll"):
                dll_paths.setdefault(path.name.lower(), []).append(path)

    dlls = []
    for key, locations in sorted(dll_paths.items()):
        preferred = next((p for p in locations if "dist" in p.parts), locations[0])
        export_names = exports(preferred, objdump)
        dlls.append({
            "name": preferred.name,
            "purpose": purpose(preferred.name),
            "declared_in_library_manifest": key in declared,
            "bytes": preferred.stat().st_size,
            "sha256": sha256(preferred),
            "locations": [p.relative_to(root).as_posix() for p in locations],
            "export_count": len(export_names),
            "exports": export_names,
        })

    apis: list[dict] = []
    for path in sorted((root / "libsx").rglob("*.bas")):
        apis.extend(wrapper_api(path, root))

    payload = {
        "schema": "uxb.dll-wrapper-inventory.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dll_count": len(dlls),
        "wrapper_api_count": len(apis),
        "dlls": dlls,
        "wrapper_apis": apis,
    }
    output_json = root / "manifests" / "uxb_dll_inventory.json"
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# uXBasic DLL ve wrapper API envanteri",
        "",
        f"Üretilen DLL sayısı: **{len(dlls)}**. Wrapper API sayısı: **{len(apis)}**.",
        "",
        "## DLL karar tablosu",
        "",
        "| DLL | Amaç | Manifest kaydı | Export | Boyut |",
        "|---|---|---:|---:|---:|",
    ]
    for item in dlls:
        lines.append(
            f"| `{item['name']}` | {item['purpose']} | "
            f"{'Evet' if item['declared_in_library_manifest'] else 'Otomatik envanter'} | "
            f"{item['export_count']} | {item['bytes']} |"
        )
    lines += [
        "",
        "## uXBasic wrapper imzaları",
        "",
        "| uXBasic syntax | Giriş tipleri | Çıkış | DLL bağlantısı |",
        "|---|---|---|---|",
    ]
    for api in apis:
        param_types = ", ".join(p["type"] for p in api["parameters"]) or "-"
        connection = api["connection"]
        if connection:
            connect_text = (
                f"`{connection['dll']}!{connection['symbol']}` "
                f"{connection['convention']} `{connection['signature'] or '-'}`"
            )
        else:
            connect_text = "uXBasic gövdesi / doğrudan wrapper"
        lines.append(
            f"| `{api['syntax']}` | {param_types} | `{api['return']}` | {connect_text} |"
        )
    lines += [
        "",
        "## Bağlantı hükmü",
        "",
        "- Skaler ve en çok 10 argümanlı C fonksiyonları `CALL(DLL, ...)` ile doğrudan bağlanır.",
        "- C `float` sınırda F64 alan adaptörle çevrilir; uXBasic FFI yüzeyi F64 kullanır.",
        "- STRUCT değerleri UXCAPI descriptor veya C adaptörle bağlanır; UNION by-value için C adaptör zorunludur.",
        "- Sahiplik gerektiren nesneler ham pointer yerine handle ile açılır ve eşleşen `Close/Free/Unload` çağrısıyla kapatılır.",
        "- Script runtimeları için doğrudan DLL köprüsü tercih edilir; tam runtime ağacı isteyen Prolog gibi sistemlerde CLI süreç köprüsü taşınabilir yoldur.",
    ]
    output_md = root / "docs" / "UXB_DLL_WRAPPER_API_ENVANTERI_20260729.md"
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS dll={len(dlls)} wrapper_api={len(apis)}")
    print(output_json)
    print(output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
