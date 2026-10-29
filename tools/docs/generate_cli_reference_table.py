#!/usr/bin/env python3
"""Generate the complete CLI reference table from the canonical registry export."""
from __future__ import annotations

import json
from pathlib import Path


def clean(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


root = Path(__file__).resolve().parents[2]
surface = json.loads((root / "vscode-extension/generated/language-surface.json").read_text(encoding="utf-8"))
items = [item for item in surface["cliOptions"] if not item.get("removed")]
lines = [
    "# uXBasic CLI Anahtarları: Tam Kullanım ve Anlam Tablosu",
    "",
    "Bu belge compiler kaynaklarından üretilen kanonik CLI registry’sini temel alır.",
    "Varsayılan bildirim dili İngilizcedir; Türkçe için `--message-lang tr` kullanılır.",
    "",
    "Temel kalıp:",
    "",
    "```powershell",
    r".\bin\uxb.exe <verb> .\program.uxb [anahtarlar]",
    "```",
    "",
    f"Toplam etkin anahtar: **{len(items)}**.",
    "",
    "| Uzun anahtar | Kısa | Değer ister | Dosya üretir | Katman | Beklenen çıktı | Görevi / doğrulama sözleşmesi |",
    "|---|---|---:|---:|---|---|---|",
]
for item in items:
    lines.append(
        "| `{}` | `{}` | {} | {} | {} | {} | {} |".format(
            clean(item["name"]),
            clean(item.get("short")),
            "Evet" if item.get("needsValue") else "Hayır",
            "Evet" if item.get("producesFile") else "Hayır",
            clean(item.get("layer")),
            clean(item.get("expectedExtension")),
            clean(item.get("validation")),
        )
    )
lines += [
    "",
    "## Sık kullanılan örnekler",
    "",
    "```powershell",
    r".\bin\uxb.exe lex .\program.uxb --tokens-json-out .\reports\tokens.json",
    r".\bin\uxb.exe ast .\program.uxb --ast-json-out .\reports\ast.json",
    r".\bin\uxb.exe sem .\program.uxb --all-diagnostics-json-out .\reports\diagnostics.json",
    r".\bin\uxb.exe int .\program.uxb --interpreter-backend AST",
    r".\bin\uxb.exe int .\program.uxb --interpreter-backend MIR",
    r".\bin\uxb.exe bld .\program.uxb --x64-mode MIR --build-x64-out .\build\program_x64",
    r".\bin\uxb.exe ast .\program.uxb --message-lang tr",
    "```",
    "",
    "Makine doğrulama raporu `reports/cli/all_cli_options_verify.json` konumunda üretilir.",
]
out = root / "docs/UXB_CLI_TUM_ANAHTARLAR_KULLANIM_TABLOSU_20260729_TR.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WRITE {out} rows={len(items)}")
