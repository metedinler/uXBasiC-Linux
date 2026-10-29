from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json
import shutil

from .model import ConversionReport
from .emitter import ALL_KNOWN_AST_KINDS


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_project(
    out_dir: Path,
    project_name: str,
    basx_text: str,
    profile: str = "",
    profiles_dir: str = "profiles/",
    headers_dir: str = "hx/",
    requirements: list[str] | None = None,
    copy_profiles_from: Path | None = None,
    copy_hx_from: Path | None = None,
) -> dict[str, str]:
    out_dir = out_dir.resolve()
    basx_dir = out_dir / "basx"
    build_dir = out_dir / "build"
    reports_dir = out_dir / "reports"
    hx_dir = out_dir / "hx"
    prf_dir = out_dir / "profiles"
    docs_dir = out_dir / "docs"
    tests_dir = out_dir / "tests"

    for d in (basx_dir, build_dir, reports_dir, docs_dir, tests_dir):
        d.mkdir(parents=True, exist_ok=True)

    if copy_profiles_from and copy_profiles_from.exists():
        if prf_dir.exists():
            shutil.rmtree(prf_dir)
        shutil.copytree(copy_profiles_from, prf_dir)
        profiles_dir = "profiles/"
    else:
        prf_dir.mkdir(parents=True, exist_ok=True)

    if copy_hx_from and copy_hx_from.exists():
        if hx_dir.exists():
            shutil.rmtree(hx_dir)
        shutil.copytree(copy_hx_from, hx_dir)
        headers_dir = "hx/"
    else:
        hx_dir.mkdir(parents=True, exist_ok=True)

    basx_path = basx_dir / "main.basx"
    write_text(basx_path, basx_text)

    reqs = requirements or []
    project_lines = [
        "[project]",
        f"name = {project_name}",
        "main = basx/main.basx",
        f"output = build/{project_name}.py",
        f"source_map = build/{project_name}.map.json",
        "diagnostics = build/diagnostics.json",
        "alias_report = build/aliases.json",
        "",
        "[folders]",
        "basx = basx/",
        f"headers = {headers_dir}",
        f"profiles = {profiles_dir}",
        "build = build/",
        "docs = docs/",
        "tests = tests/",
        "",
    ]
    if profile:
        project_lines.extend(["[profiles]", f"use = {profile}", ""])
    if reqs:
        project_lines.append("[requirements]")
        for r in reqs:
            project_lines.append(f"package = {r}")
        project_lines.append("")
    project_lines.extend([
        "[vscode]",
        "live_build = true",
        "live_errors = true",
        "show_generated_python = true",
        "",
    ])
    prj_path = out_dir / f"{project_name}.prj"
    write_text(prj_path, "\n".join(project_lines))

    return {
        "out_dir": str(out_dir),
        "project": str(prj_path),
        "basx": str(basx_path),
        "build": str(build_dir),
        "reports": str(reports_dir),
        "profiles_dir": str(prf_dir),
        "headers_dir": str(hx_dir),
    }


def write_report(out_dir: Path, report: ConversionReport, project_info: dict[str, str]) -> None:
    reports_dir = Path(project_info["reports"])
    data = {
        "program": "uxbasic2pdsxS",
        "version": "0.2.0",
        "project": project_info,
        "summary": {
            "node_kinds_seen": len(report.node_counts),
            "nodes_seen_total": sum(report.node_counts.values()),
            "node_kinds_handled": len(report.handled_counts),
            "nodes_handled_total": sum(report.handled_counts.values()),
            "unhandled_total": sum(report.unhandled_counts.values()),
            "source_lines_used": report.source_lines_used,
            "structural_lines_used": report.structural_lines_used,
            "call_dll_api_count": report.call_dll_api_count,
            "source_map_entries": len(report.source_map),
            "diagnostic_count": len(report.diagnostics),
            "error_count": sum(1 for d in report.diagnostics if d.level == "ERROR"),
            "warn_count": sum(1 for d in report.diagnostics if d.level == "WARN"),
        },
        "node_counts": report.node_counts,
        "handled_counts": report.handled_counts,
        "unhandled_counts": report.unhandled_counts,
        "diagnostics": [asdict(d) for d in report.diagnostics],
    }
    write_text(reports_dir / "uxbasic2pdsxS_report.json", json.dumps(data, ensure_ascii=False, indent=2))
    write_text(reports_dir / "source_map.json", json.dumps(report.source_map, ensure_ascii=False, indent=2))

    with (reports_dir / "node_coverage.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["node_kind", "known_in_uxbasic", "seen", "handled", "coverage"])
        all_kinds = sorted(ALL_KNOWN_AST_KINDS | set(report.node_counts) | set(report.handled_counts))
        for k in all_kinds:
            seen = report.node_counts.get(k, 0)
            handled = report.handled_counts.get(k, 0)
            coverage = "OK" if seen == handled else ("UNSEEN" if seen == 0 else "PARTIAL")
            w.writerow([k, "YES" if k in ALL_KNOWN_AST_KINDS else "NO", seen, handled, coverage])


def write_usage_doc(out_dir: Path, project_info: dict[str, str]) -> None:
    text = f"""# uxbasic2pdsxS çıktısı

Bu klasör, uXBasic JSON çıktılarından pdsX proje düzeni üretmek için oluşturuldu.

## Ana hedefler

1. `json/ast.json` içindeki tüm uXBasic AST node türlerini pdsX BASX karşılığına çevirmek.
2. `.hx` üretmemek; `.hx` dosyaları pdsX/HXA veya programcı tarafından hazırlanır.
3. uXBasic yorum satırlarını (`REM`, `'`, `#`) kaynakta göründüğü sırayla BASX dosyasına taşımak.
4. `CALL DLL` ve `CALL API` satırlarını aynen korumak; altına programcıya DLL/API çözüm notu eklemek.
5. uXBasic içine pdsX backend gömmemek; ayrı ara bağlayıcı olarak çalışmak.

## Üretilen ana dosyalar

- Proje: `{project_info['project']}`
- BASX: `{project_info['basx']}`
- Rapor: `{project_info['reports']}/uxbasic2pdsxS_report.json`
- Node kapsamı: `{project_info['reports']}/node_coverage.csv`
- Kaynak haritası: `{project_info['reports']}/source_map.json`

## pdsX ile devam

```bat
python C:\\pdsx_wrapper\\pdsx_cli.py check "{project_info['project']}"
python C:\\pdsx_wrapper\\pdsx_cli.py build "{project_info['project']}" --show-python
python C:\\pdsx_wrapper\\pdsx_cli.py run "{project_info['project']}"
```
"""
    write_text(out_dir / "docs" / "UXBASIC2PDSXS_USAGE.md", text)
