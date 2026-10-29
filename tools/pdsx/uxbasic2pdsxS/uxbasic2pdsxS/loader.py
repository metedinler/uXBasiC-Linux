from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .model import AstNode
from .source_model import read_text_any


class BridgeLoadError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(read_text_any(path))
    except FileNotFoundError as exc:
        raise BridgeLoadError(f"JSON dosyası bulunamadı: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BridgeLoadError(f"JSON okunamadı: {path}: {exc}") from exc


def discover_file(json_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        p = json_dir / name
        if p.exists():
            return p
    # Secondary: tolerate common nested artifact directories copied into json dir.
    lowered = {name.lower() for name in names}
    for p in json_dir.rglob("*.json"):
        if p.name.lower() in lowered:
            return p
    return None


def load_ast(json_dir: Path, ast_path: Path | None = None) -> AstNode:
    if ast_path is None:
        ast_path = discover_file(json_dir, ["ast.json", "main.ast.json", "parser_ast.json", "ast_full.json"])
    if ast_path is None:
        raise BridgeLoadError(f"AST JSON bulunamadı. Beklenen: {json_dir}/ast.json")
    data = load_json(ast_path)
    if isinstance(data, dict) and isinstance(data.get("root"), dict):
        return AstNode(data["root"])
    if isinstance(data, dict) and str(data.get("kind") or "").upper() == "PROGRAM":
        return AstNode(data)
    raise BridgeLoadError(f"AST JSON içinde root düğümü bulunamadı: {ast_path}")


def load_optional_json(json_dir: Path, names: list[str]) -> Any | None:
    p = discover_file(json_dir, names)
    if p is None:
        return None
    return load_json(p)


def diagnostics_have_errors(diag: Any) -> bool:
    if not diag:
        return False
    items = diag if isinstance(diag, list) else diag.get("diagnostics", []) if isinstance(diag, dict) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        lvl = str(item.get("level") or item.get("severity") or item.get("kind") or "").upper()
        code = str(item.get("code") or "").upper()
        msg = str(item.get("message") or "")
        if lvl in {"ERROR", "ERR", "FATAL"} or code.endswith("ERROR") or "error" in msg.lower():
            return True
    return False



def extract_profile_from_preprocess_result(data: Any) -> str:
    """Best-effort profile extraction from uXBasic preprocess_result.json."""
    if not isinstance(data, dict):
        return ""
    # Official shape: "profiles": [{"key":"PROFILE", "value":"..."}]
    for key in ("profiles", "profile", "manifest"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                ikey = str(item.get("key") or item.get("name") or "").lower()
                ival = str(item.get("value") or "").strip()
                if ival and (ikey in {"profile", "profiles"} or "profile" in ikey):
                    return ival
    # Also tolerate metadata wrappers produced by external tools.
    meta = data.get("metadata")
    if isinstance(meta, dict):
        val = str(meta.get("profile") or meta.get("pdsx_profile") or "").strip()
        if val:
            return val
    return ""
