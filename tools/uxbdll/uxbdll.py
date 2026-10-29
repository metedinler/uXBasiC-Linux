#!/usr/bin/env python3
"""uxbdll: link an existing uXBasic x64 ASM/OBJ build directory as a Win64 DLL.

This tool intentionally does not modify the uXBasic compiler. It consumes the
artifacts already emitted by the x64 build pipeline:
  program.asm, obj/program.obj, program_link_args.rsp, interop/toolchain.env.bat

It validates exported NASM symbols, writes a GNU/MinGW .def file, generates a
CALL(DLL) wrapper, and writes a reproducible build_dll.bat script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

VERSION = "1.0.0"
GLOBAL_RE = re.compile(r"^\s*global\s+([^\s;,]+)", re.IGNORECASE)
LABEL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*):")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

RETURN_MAP = {
    "VOID": ("VOID", None),
    "I8": ("I8", "I8"), "U8": ("U8", "U8"),
    "I16": ("I16", "I16"), "U16": ("U16", "U16"),
    "I32": ("I32", "I32"), "U32": ("U32", "U32"),
    "I64": ("I64", "I64"), "U64": ("U64", "U64"),
    "F32": ("F32", "F32"), "F64": ("F64", "F64"),
    "PTR": ("PTR", "U64"),
    "STRPTR": ("STRPTR", "STRING"),
    "WSTRPTR": ("WSTRPTR", "U64"),
    "BOOLEAN": ("I32", "BOOLEAN"),
}
ARG_TYPES = set(RETURN_MAP) | {"STRING", "OBJECT"}


class UxBDllError(RuntimeError):
    pass


def _norm_type(value: str) -> str:
    t = str(value).strip().upper()
    if t == "STRING":
        return "STRPTR"
    if t == "OBJECT":
        return "PTR"
    if t not in ARG_TYPES:
        raise UxBDllError(f"unsupported ABI type: {value}")
    return t


def _safe_ident(value: str, label: str) -> str:
    if not IDENT_RE.match(value):
        raise UxBDllError(f"invalid {label}: {value!r}")
    return value


def _bat_quote(path: Path | str) -> str:
    return f'"{str(path)}"'


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UxBDllError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UxBDllError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise UxBDllError("manifest root must be an object")
    return data


@dataclass(frozen=True)
class Argument:
    name: str
    abi_type: str
    uxb_type: str


@dataclass(frozen=True)
class Export:
    public: str
    internal: str
    return_abi: str
    return_uxb: str | None
    args: tuple[Argument, ...]
    calling_convention: str


@dataclass(frozen=True)
class Config:
    manifest_path: Path
    project_root: Path
    build_dir: Path
    output_dir: Path
    dll_name: str
    library_name: str
    namespace: str
    wrapper_bas: Path
    wrapper_uxmh: Path
    exports: tuple[Export, ...]
    runtime_dependencies: tuple[str, ...]
    linker_flags: tuple[str, ...]
    build_program: bool


def _resolve(base: Path, raw: str | None, default: str) -> Path:
    p = Path(raw or default)
    return p if p.is_absolute() else (base / p).resolve()


def parse_config(manifest_path: Path) -> Config:
    raw = _load_json(manifest_path)
    manifest_dir = manifest_path.parent.resolve()
    project_root = _resolve(manifest_dir, raw.get("project_root"), ".")
    build_dir = _resolve(project_root, raw.get("build_dir"), "build/x64/module")
    output_dir = _resolve(project_root, raw.get("output_dir"), str(build_dir))

    library_name = _safe_ident(str(raw.get("name", "uxmodule")), "library name")
    dll_name = str(raw.get("dll_name", library_name + ".dll"))
    if Path(dll_name).name != dll_name or not dll_name.lower().endswith(".dll"):
        raise UxBDllError("dll_name must be a simple .dll filename")
    namespace = _safe_ident(str(raw.get("namespace", library_name)), "namespace")

    wrapper_bas = _resolve(project_root, raw.get("wrapper_bas"), f"libsx/{library_name}/{library_name}.bas")
    wrapper_uxmh = _resolve(project_root, raw.get("wrapper_uxmh"), f"include/modules/{library_name}.uxmh")

    exports_raw = raw.get("exports")
    if not isinstance(exports_raw, list) or not exports_raw:
        raise UxBDllError("manifest.exports must be a non-empty array")

    exports: list[Export] = []
    public_seen: set[str] = set()
    for item in exports_raw:
        if not isinstance(item, dict):
            raise UxBDllError("each export must be an object")
        public = _safe_ident(str(item.get("public", "")), "public export name")
        internal = _safe_ident(str(item.get("internal", "")), "internal NASM symbol")
        if public.lower() in public_seen:
            raise UxBDllError(f"duplicate public export: {public}")
        public_seen.add(public.lower())
        ret = _norm_type(str(item.get("return", "VOID")))
        call_ret, uxb_ret = RETURN_MAP[ret]
        if "wrapper_return" in item:
            uxb_ret = str(item["wrapper_return"]).strip().upper()
        args_raw = item.get("args", [])
        if not isinstance(args_raw, list):
            raise UxBDllError(f"args for {public} must be an array")
        args: list[Argument] = []
        for index, arg in enumerate(args_raw):
            if isinstance(arg, str):
                abi = _norm_type(arg)
                name = f"arg{index}"
                uxb_type = "U64" if abi in {"PTR", "WSTRPTR"} else ("STRING" if abi == "STRPTR" else abi)
            elif isinstance(arg, dict):
                name = _safe_ident(str(arg.get("name", f"arg{index}")), "argument name")
                abi = _norm_type(str(arg.get("type", "U64")))
                uxb_type = str(arg.get("uxb_type", "U64" if abi in {"PTR", "WSTRPTR"} else ("STRING" if abi == "STRPTR" else abi))).strip().upper()
            else:
                raise UxBDllError(f"invalid argument #{index} for {public}")
            args.append(Argument(name=name, abi_type=abi, uxb_type=uxb_type))
        cc = str(item.get("calling_convention", "CDECL")).strip().upper()
        if cc not in {"CDECL", "STDCALL", "WIN64"}:
            raise UxBDllError(f"unsupported calling convention for {public}: {cc}")
        if cc == "WIN64":
            cc = "CDECL"  # uXBasic CALL surface uses CDECL for Win64's unified ABI.
        exports.append(Export(public, internal, call_ret, uxb_ret, tuple(args), cc))

    deps = raw.get("runtime_dependencies", [])
    if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
        raise UxBDllError("runtime_dependencies must be an array of filenames")
    flags = raw.get("linker_flags", ["-Wl,--enable-auto-import"])
    if not isinstance(flags, list) or not all(isinstance(x, str) for x in flags):
        raise UxBDllError("linker_flags must be an array of strings")

    return Config(
        manifest_path=manifest_path.resolve(), project_root=project_root,
        build_dir=build_dir, output_dir=output_dir, dll_name=dll_name,
        library_name=library_name, namespace=namespace,
        wrapper_bas=wrapper_bas, wrapper_uxmh=wrapper_uxmh,
        exports=tuple(exports), runtime_dependencies=tuple(deps),
        linker_flags=tuple(flags), build_program=bool(raw.get("build_program", True)),
    )


def scan_globals(asm_path: Path) -> set[str]:
    try:
        text = asm_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise UxBDllError(f"program.asm not found: {asm_path}") from exc
    return {m.group(1) for line in text.splitlines() if (m := GLOBAL_RE.match(line))}


def promote_existing_labels_to_globals(cfg: Config) -> tuple[str, ...]:
    """Expose compiler-emitted function labels without inventing symbols.

    The x64 backend emits routine labels but intentionally marks only ``main``
    global for EXE builds.  A DLL build needs selected, manifest-approved
    labels to be global before NASM rebuilds program.obj.
    """
    asm_path = cfg.build_dir / "program.asm"
    text = asm_path.read_text(encoding="utf-8", errors="replace")
    globals_found = scan_globals(asm_path)
    labels = {m.group(1) for line in text.splitlines() if (m := LABEL_RE.match(line))}
    promote = tuple(exp.internal for exp in cfg.exports
                    if exp.internal not in globals_found and exp.internal in labels)
    if promote:
        prefix = "\n".join(f"global {symbol}" for symbol in promote) + "\n"
        asm_path.write_text(prefix + text, encoding="utf-8", newline="")
    return promote


def validate_artifacts(cfg: Config) -> set[str]:
    required = [cfg.build_dir / "program.asm", cfg.build_dir / "program_link_args.rsp", cfg.build_dir / "interop/toolchain.env.bat"]
    if cfg.build_program:
        required.append(cfg.build_dir / "build_program.bat")
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise UxBDllError("missing x64 build artifacts:\n  " + "\n  ".join(missing))
    promoted = promote_existing_labels_to_globals(cfg)
    globals_found = scan_globals(cfg.build_dir / "program.asm")
    lower_map = {x.lower(): x for x in globals_found}
    missing_symbols: list[str] = []
    case_hints: list[str] = []
    for export in cfg.exports:
        if export.internal not in globals_found:
            missing_symbols.append(export.internal)
            if export.internal.lower() in lower_map:
                case_hints.append(f"{export.internal} (actual: {lower_map[export.internal.lower()]})")
    if missing_symbols:
        msg = "export symbols missing from program.asm globals:\n  " + "\n  ".join(missing_symbols)
        if case_hints:
            msg += "\ncase-sensitive matches available:\n  " + "\n  ".join(case_hints)
        raise UxBDllError(msg)
    if promoted:
        print("PROMOTE ASM globals: " + ", ".join(promoted))
    return globals_found


def render_def(cfg: Config) -> str:
    lines = [f"LIBRARY {cfg.library_name}", "", "EXPORTS"]
    for exp in cfg.exports:
        lines.append(f"    {exp.public}={exp.internal}")
    lines.append("")
    return "\r\n".join(lines)


def render_wrapper(cfg: Config) -> str:
    lines = [
        f"' Auto-generated by uxbdll {VERSION}.",
        f"' Source manifest: {cfg.manifest_path.name}",
        "' Do not edit by hand; regenerate from the manifest.",
        "",
        f"NAMESPACE {cfg.namespace}",
        "",
        f'CONST DLL_NAME = "{cfg.dll_name}"',
        "",
    ]
    for exp in cfg.exports:
        params = ", ".join(f"{a.name} AS {a.uxb_type}" for a in exp.args)
        call_sig = ",".join(a.abi_type for a in exp.args)
        values = ", ".join(a.name for a in exp.args)
        signature_tail = ""
        if exp.args:
            signature_tail = f', "{call_sig}", {values}'
        if exp.return_uxb is None:
            lines.append(f"SUB {exp.public}({params})")
            lines.append(f'    CALL(DLL, "{cfg.dll_name}", "{exp.public}", VOID, {exp.calling_convention}{signature_tail})')
            lines.append("END SUB")
        else:
            lines.append(f"FUNCTION {exp.public}({params}) AS {exp.return_uxb}")
            lines.append(f'    RETURN CALL(DLL, "{cfg.dll_name}", "{exp.public}", {exp.return_abi}, {exp.calling_convention}{signature_tail})')
            lines.append("END FUNCTION")
        lines.append("")
    lines.append("END NAMESPACE")
    lines.append("")
    return "\n".join(lines)


def render_uxmh(cfg: Config) -> str:
    rel = os.path.relpath(cfg.wrapper_bas, cfg.project_root).replace("\\", "/")
    return f"' Auto-generated public forwarding header: {cfg.library_name}\n\nINCLUDE \"{rel}\"\n"


def render_build_bat(cfg: Config) -> str:
    build_dir = str(cfg.build_dir)
    output_dir = str(cfg.output_dir)
    def_path = str(cfg.build_dir / f"{cfg.library_name}.def")
    implib = str(cfg.output_dir / f"lib{cfg.library_name}.dll.a")
    output_dll = str(cfg.output_dir / cfg.dll_name)
    flags = " ".join(cfg.linker_flags)
    lines = [
        "@echo off",
        "setlocal EnableExtensions EnableDelayedExpansion",
        f'set "UXBDLL_PROJECT_ROOT={str(cfg.project_root)}"',
        f'set "UXBDLL_BUILD_DIR={build_dir}"',
        f'set "UXBDLL_OUTPUT_DIR={output_dir}"',
        'pushd "%UXBDLL_PROJECT_ROOT%"',
        'if errorlevel 1 exit /b 1',
        'if not exist "%UXBDLL_OUTPUT_DIR%" mkdir "%UXBDLL_OUTPUT_DIR%"',
    ]
    if cfg.build_program:
        lines += [
            'call "%UXBDLL_BUILD_DIR%\\build_program.bat"',
            "if errorlevel 1 exit /b 1",
        ]
    lines += [
        'call "%UXBDLL_BUILD_DIR%\\interop\\toolchain.env.bat"',
        "if errorlevel 1 exit /b 1",
        'if not defined UXB_LINK_CMD set "UXB_LINK_CMD=gcc"',
        f'"%UXB_LINK_CMD%" -shared @"%UXBDLL_BUILD_DIR%\\program_link_args.rsp" "{def_path}" {flags} -Wl,--out-implib,"{implib}" -o "{output_dll}"',
        "if errorlevel 1 exit /b 1",
    ]
    if cfg.runtime_dependencies:
        lines += [
            'for %%D in (' + " ".join(f'"{d}"' for d in cfg.runtime_dependencies) + ') do (',
            '  if exist "%CD%\\bin\\%%~D" copy /Y "%CD%\\bin\\%%~D" "%UXBDLL_OUTPUT_DIR%\\%%~D" >nul',
            '  if not exist "%UXBDLL_OUTPUT_DIR%\\%%~D" if exist "%CD%\\dist\\runtime_ext\\%%~D" copy /Y "%CD%\\dist\\runtime_ext\\%%~D" "%UXBDLL_OUTPUT_DIR%\\%%~D" >nul',
            '  if not exist "%UXBDLL_OUTPUT_DIR%\\%%~D" if exist "%CD%\\native\\uxb_runtime\\build\\%%~D" copy /Y "%CD%\\native\\uxb_runtime\\build\\%%~D" "%UXBDLL_OUTPUT_DIR%\\%%~D" >nul',
            ')',
        ]
    lines += [
        f'echo [uxbdll] DLL: {output_dll}',
        f'echo [uxbdll] import library: {implib}',
        "popd",
        "exit /b 0",
        "",
    ]
    return "\r\n".join(lines)


def write_outputs(cfg: Config, force: bool) -> dict[str, str]:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.wrapper_bas.parent.mkdir(parents=True, exist_ok=True)
    cfg.wrapper_uxmh.parent.mkdir(parents=True, exist_ok=True)
    outputs = {
        "def": cfg.build_dir / f"{cfg.library_name}.def",
        "build_bat": cfg.build_dir / "build_dll.bat",
        "wrapper_bas": cfg.wrapper_bas,
        "wrapper_uxmh": cfg.wrapper_uxmh,
        "report": cfg.build_dir / "uxbdll_report.json",
    }
    for path in outputs.values():
        if path.exists() and not force and path.name != "uxbdll_report.json":
            raise UxBDllError(f"refusing to overwrite existing file without --force: {path}")
    outputs["def"].write_text(render_def(cfg), encoding="utf-8", newline="")
    outputs["build_bat"].write_text(render_build_bat(cfg), encoding="utf-8", newline="")
    outputs["wrapper_bas"].write_text(render_wrapper(cfg), encoding="utf-8")
    outputs["wrapper_uxmh"].write_text(render_uxmh(cfg), encoding="utf-8")
    report = {
        "tool": "uxbdll", "version": VERSION,
        "manifest": str(cfg.manifest_path), "build_dir": str(cfg.build_dir),
        "output_dll": str(cfg.output_dir / cfg.dll_name),
        "exports": [{"public": x.public, "internal": x.internal} for x in cfg.exports],
        "generated": {k: str(v) for k, v in outputs.items() if k != "report"},
    }
    outputs["report"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in outputs.items()}


def verify_dll(cfg: Config) -> None:
    dll = cfg.output_dir / cfg.dll_name
    if not dll.exists():
        raise UxBDllError(f"DLL not found: {dll}")
    candidates = [
        os.environ.get("UXB_OBJDUMP", ""),
        shutil.which("objdump") or "",
        shutil.which("llvm-objdump") or "",
        shutil.which("dumpbin") or "",
    ]
    if os.name == "nt":
        candidates.extend([
            r"C:\msys64\ucrt64\bin\objdump.exe",
            r"C:\msys64\mingw64\bin\objdump.exe",
        ])
    tool = next((x for x in candidates if x and Path(x).exists()), None)
    if tool is None:
        raise UxBDllError("objdump/llvm-objdump/dumpbin not found; set UXB_OBJDUMP for export audit")
    tool_name = Path(tool).name.lower()
    if tool_name.startswith("dumpbin"):
        cmd = [tool, "/nologo", "/exports", str(dll)]
    elif tool_name.startswith("llvm-objdump"):
        cmd = [tool, "--private-headers", str(dll)]
    else:
        cmd = [tool, "-p", str(dll)]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise UxBDllError(f"export audit failed:\n{proc.stderr}")
    text = proc.stdout.lower()
    missing = [x.public for x in cfg.exports if x.public.lower() not in text]
    if missing:
        raise UxBDllError("DLL export audit missing:\n  " + "\n  ".join(missing))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--force", action="store_true", help="overwrite generated files")
    parser.add_argument("--run", action="store_true", help="run generated build_dll.bat on Windows")
    parser.add_argument("--verify-only", action="store_true", help="audit an already-built DLL")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        cfg = parse_config(args.manifest.resolve())
        if args.verify_only:
            verify_dll(cfg)
            print(f"PASS uxbdll export audit: {cfg.output_dir / cfg.dll_name}")
            return 0
        globals_found = validate_artifacts(cfg)
        outputs = write_outputs(cfg, args.force)
        print(f"PASS global symbol validation: {len(globals_found)} symbols")
        for key, value in outputs.items():
            print(f"WRITE {key}: {value}")
        if args.run:
            if os.name != "nt":
                raise UxBDllError("--run requires Windows cmd.exe")
            proc = subprocess.run(["cmd.exe", "/d", "/c", str(Path(outputs["build_bat"]))], cwd=cfg.project_root)
            if proc.returncode != 0:
                raise UxBDllError(f"build_dll.bat failed with exit code {proc.returncode}")
            verify_dll(cfg)
            print(f"PASS DLL build and export audit: {cfg.output_dir / cfg.dll_name}")
        return 0
    except UxBDllError as exc:
        print(f"FAIL uxbdll: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
