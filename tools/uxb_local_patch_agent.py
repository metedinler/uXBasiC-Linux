#!/usr/bin/env python3
"""Local, API-key-free patch agent for Python, FreeBASIC and C sources.

Dry-run is the default.  The model may propose only a unified diff; this tool
validates paths, applies through ``git apply`` and keeps timestamped backups.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".py", ".pyi", ".bas", ".bi", ".fbs", ".fb", ".c", ".h", ".cc", ".cpp", ".hpp"
}
DIFF_PATH = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check,
    )


def safe_relative(root: Path, raw: str) -> Path:
    candidate = (root / raw).resolve()
    try:
        relative = candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"workspace disina cikmaya calisan yol: {raw}") from exc
    if relative.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"izin verilmeyen dosya turu: {relative}")
    return relative


def extract_diff(text: str) -> str:
    fenced = re.search(r"```(?:diff|patch)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    diff = fenced.group(1) if fenced else text
    start = diff.find("diff --git ")
    if start < 0:
        raise ValueError("model unified diff uretmedi")
    return diff[start:].strip() + "\n"


def collect_context(root: Path, request: str, max_files: int = 12, max_chars: int = 50000) -> str:
    words = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", request) if len(w) > 3][:8]
    files: list[Path] = []
    for word in words:
        result = run(["rg", "-l", "-i", "--glob", "!build/**", "--glob", "!dist/**", word, "."], root, False)
        for line in result.stdout.splitlines():
            path = (root / line).resolve()
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS and path not in files:
                files.append(path)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break
    chunks: list[str] = []
    used = 0
    for path in files:
        data = path.read_text(encoding="utf-8", errors="replace")
        room = max_chars - used
        if room <= 0:
            break
        data = data[:room]
        chunks.append(f"\n### {path.relative_to(root)}\n{data}")
        used += len(data)
    return "".join(chunks)


def ask_ollama(endpoint: str, model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/generate", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))["response"]


def validate_diff(root: Path, diff: str) -> list[Path]:
    paths = [safe_relative(root, item) for item in DIFF_PATH.findall(diff)]
    if not paths:
        raise ValueError("diff icinde +++ b/... dosyasi yok")
    patch_file = root / "build" / "local_patch_agent" / "candidate.patch"
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(diff, encoding="utf-8", newline="\n")
    checked = run(["git", "apply", "--check", "--whitespace=error-all", str(patch_file)], root, False)
    if checked.returncode:
        raise ValueError("git apply --check basarisiz:\n" + checked.stdout)
    return paths


def backup_and_apply(root: Path, diff: str, paths: list[Path]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root / ".patch_backup" / f"local_agent_{stamp}"
    for relative in paths:
        source = root / relative
        if source.exists():
            destination = backup / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    patch_file = root / "build" / "local_patch_agent" / f"applied_{stamp}.patch"
    patch_file.write_text(diff, encoding="utf-8", newline="\n")
    run(["git", "apply", "--whitespace=error-all", str(patch_file)], root)
    return backup


def verify_changed_files(root: Path, paths: list[Path]) -> None:
    fbc = root / "tools" / "FreeBASIC-1.10.1-win64" / "fbc64.exe"
    gcc = shutil.which("gcc")
    for relative in paths:
        path = root / relative
        suffix = path.suffix.lower()
        if suffix in {".py", ".pyi"}:
            run([sys.executable, "-m", "py_compile", str(path)], root)
        elif suffix in {".bas", ".fb"} and fbc.exists():
            out = root / "build" / "local_patch_agent" / (path.stem + ".o")
            run([str(fbc), "-lang", "fb", "-c", "-x", str(out), str(path)], root)
        elif suffix in {".c", ".cc", ".cpp"} and gcc:
            run([gcc, "-fsyntax-only", str(path)], root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Yerel Ollama tabanli guvenli yama agenti")
    parser.add_argument("request", nargs="?", help="istenen degisiklik")
    parser.add_argument("--root", default=".")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--ollama", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--apply", action="store_true", help="dogrulanmis yamayi uygula")
    parser.add_argument("--patch-file", help="Ollama yerine mevcut unified diff dosyasini denetle")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.patch_file:
        diff = Path(args.patch_file).read_text(encoding="utf-8")
    else:
        if not args.request:
            parser.error("request veya --patch-file gerekli")
        context = collect_context(root, args.request)
        prompt = f"""Sen yalniz unified diff ureten bir kod yama aracisin.
Hedef diller Python, FreeBASIC ve C/C++.
Workspace disina cikma, binary dosya degistirme, komut calistirma.
Aciklama yazma; sadece diff --git ile baslayan uygulanabilir yama yaz.
Istek: {args.request}
Kaynak baglami:
{context}
"""
        diff = extract_diff(ask_ollama(args.ollama, args.model, prompt, args.timeout))

    paths = validate_diff(root, diff)
    output = root / "build" / "local_patch_agent" / "candidate.patch"
    print(f"PATCH_CHECK_OK files={len(paths)} patch={output}")
    if not args.apply:
        print("DRY_RUN: uygulamak icin --apply ekleyin")
        return 0
    backup = backup_and_apply(root, diff, paths)
    verify_changed_files(root, paths)
    print(f"PATCH_APPLY_OK backup={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

