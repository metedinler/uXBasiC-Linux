"""Source-derived registration inventory. Registration never implies acceptance."""
import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import os
import shutil
import subprocess


def tool_catalog(root, output, guide):
    """Read script sources without importing or executing the tools."""
    paths = set()
    excluded = {'node_modules', '__pycache__', '.git', 'FreeBASIC-1.10.1-win64',
                'wabt', 'out', 'tmp', 'build', 'dist', 'out_web', 'out_x64'}
    for folder in ('tools', 'compiler/scripts', 'tests'):
        for directory, names, files in os.walk(root / folder):
            names[:] = sorted(n for n in names if n not in excluded)
            paths.update(Path(directory) / n for n in files
                         if Path(n).suffix.lower() in {'.py', '.ps1', '.bat', '.cmd'})
    paths.update(p for p in root.iterdir() if p.suffix.lower() in {'.ps1', '.bat', '.cmd'})
    records = []
    powershell = []
    for path in sorted(paths):
        data = path.read_bytes()
        source = data.decode('utf-8-sig', errors='replace')
        row = dict(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
                   bytes=len(data), purpose='', options=[], functions=[], delegates=[], errors=[])
        comments = [s.strip().lstrip('#').strip() for s in source.splitlines()[:18]
                    if s.strip().startswith('#')]
        row['purpose'] = ' '.join(comments)[:700]
        if path.suffix == '.py':
            try:
                tree = ast.parse(source, filename=str(path))
                row['purpose'] = ast.get_docstring(tree) or row['purpose']
                row['functions'] = [n.name for n in ast.walk(tree)
                                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                        row['options'].append(ast.unparse(node))
                    if isinstance(node, ast.Subscript) and ast.unparse(node.value) == 'sys.argv':
                        row['options'].append('positional: ' + ast.unparse(node))
            except SyntaxError as error:
                row['errors'].append(str(error))
        elif path.suffix == '.ps1':
            powershell.append(str(path))
        else:
            row['options'] = sorted(set(re.findall(r'%~?[1-9]|%\*|--[\w-]+', source)))
        row['delegates'] = sorted(set(re.findall(r'[\w./\\-]+\.(?:py|ps1|bat|cmd|exe)', source, re.I)))
        records.append(row)
    # The PowerShell parser reads syntax only. Calling Get-Command on scripts
    # or running each tool with --help could execute destructive top-level code.
    ps = shutil.which('pwsh') or shutil.which('powershell')
    if powershell and not ps:
        raise SystemExit('PowerShell is required to read script parameter ASTs.')
    if powershell:
        program = r'''
$paths = [Console]::In.ReadToEnd() | ConvertFrom-Json
$rows = foreach ($path in $paths) {
  $tokens = $null; $errors = $null
  $tree = [Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
  $parameters = @($tree.ParamBlock.Parameters | ForEach-Object { $_.Extent.Text })
  $functions = @($tree.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true) | ForEach-Object Name)
  [pscustomobject]@{path=$path;options=$parameters;functions=$functions;errors=@($errors|ForEach-Object Message)}
}
ConvertTo-Json -InputObject @($rows) -Depth 5 -Compress
'''
        proc = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command', program],
                              input=json.dumps(powershell), encoding='utf-8', capture_output=True, timeout=120)
        if proc.returncode:
            raise SystemExit(proc.stderr)
        by_path = {str((root / r['path']).resolve()).casefold(): r for r in records}
        for info in json.loads(proc.stdout):
            row = by_path[str(Path(info['path']).resolve()).casefold()]
            for key in ('options', 'functions', 'errors'):
                row[key] = [str(value) for value in (info[key] or []) if value is not None]
    payload = dict(schema='uxb.tool_catalog.v1', records=records, count=len(records),
                   method='Full source read; Python AST and PowerShell AST; BAT token/delegate inventory. Tools are not executed.',
                   limitations=['Source inventory is not semantic acceptance or a successful execution claim.',
                                'Dynamic argparse expansion and delegated CLI require reading the referenced tool.',
                                'Vendored tools, generated output folders, historical reports and RAG copies are excluded.'])
    (output / 'tools.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    begin, end = '<!-- UXB_TOOL_CATALOG_BEGIN -->', '<!-- UXB_TOOL_CATALOG_END -->'
    lines = [begin, '## Kaynaktan çıkarılan betik ve CLI dökümü', '',
             f'{len(records)} betiğin tam içeriği okunarak Python/PowerShell sözdiziminden çıkarıldı. '
             'Bu döküm çalıştırma başarısı değildir. Ayrıntılı kaynak kimlikleri: '
             '`reports/acceptance_inventory/tools.json`.', '',
             'Python satırlarında seçenek adları, varsayılanlar, zorunluluk ve choices kaynak ifadeleriyle; '
             'PowerShell satırlarında gerçek parametre bildirimleriyle gösterilir. BAT/CMD `%*` '
             'seçenekleri çağırdığı araca iletir. Dinamik seçenekler ve alt araçlar ayrıca okunmalıdır.', '']
    for row in records:
        lines += [f"### `{row['path']}`", '', (row['purpose'] or 'Açıklama başlığı yok; aşağıdaki giriş ve alt araçları inceleyin.').replace('\n', ' '), '',
                  '```text', *(row['options'] or ['Parametre bildirimi yok; alt araç/ortam değişkeni kullanımı olabilir.']), '```',
                  'Rutinler: ' + (', '.join(row['functions']) or 'üst düzey komutlar') + '.',
                  'Çağrı/yol başvuruları: ' + (', '.join(row['delegates']) or 'yok') + '.', '']
        if row['errors']:
            lines += ['AYRIŞTIRMA HATASI: ' + '; '.join(row['errors']), '']
    lines += [end]
    text = guide.read_text(encoding='utf-8-sig')
    block = '\n'.join(lines)
    if begin in text:
        if text.count(begin) != 1 or text.count(end) != 1:
            raise SystemExit('Catalog markers must occur exactly once.')
        start, finish = text.index(begin), text.index(end) + len(end)
        text = text[:start] + block + text[finish:]
    else:
        text = text.rstrip() + '\n\n' + block + '\n'
    guide.write_text(text, encoding='utf-8')
    print(json.dumps({'tools': len(records), 'parse_errors': sum(bool(r['errors']) for r in records), 'guide': str(guide)}))

ROOT = Path(__file__).resolve().parents[2]
ENGINES = ("AST", "MIR", "x64", "AST-x64", "JS", "WASM")
parser = argparse.ArgumentParser()
parser.add_argument("--output", default="reports/acceptance_inventory")
parser.add_argument("--tools", action="store_true", help="Inventory script sources and update the existing tool guide; do not execute tools.")
parser.add_argument("--guide", default="docs/SON_DAGITIM_DERLEME_VE_TEST_REHBERI_20260729_TR.md")
args = parser.parse_args()
output = (ROOT / args.output).resolve()
if not output.is_relative_to(ROOT):
    raise SystemExit("Inventory output must remain within the active repository.")
output.mkdir(parents=True, exist_ok=True)
if args.tools:
    guide = (ROOT / args.guide).resolve()
    if not guide.is_relative_to(ROOT) or not guide.is_file():
        raise SystemExit('Guide must be an existing document within the repository.')
    tool_catalog(ROOT, output, guide)
    raise SystemExit(0)
rows = {}
hashes = {}


def read(relative):
    path = ROOT / relative
    data = path.read_bytes()
    hashes[relative] = hashlib.sha256(data).hexdigest()
    return data.decode("utf-8-sig").splitlines()


def add(name, category, path, line, **metadata):
    key = (category, name.upper())
    row = rows.setdefault(key, {"name": name.upper(), "category": category,
                               "registrations": [], "metadata": metadata,
                               "acceptance": {engine: "UNMEASURED" for engine in ENGINES}})
    row["registrations"].append({"path": path, "line": line, "sha256": hashes[path], "metadata": metadata})


def case_function(relative, function, category):
    active = False
    for number, line in enumerate(read(relative), 1):
        if re.match(r"\s*(?:Private\s+)?Function\s+" + function + r"\b", line, re.I):
            active = True
        elif active and re.match(r"\s*End Function\b", line, re.I):
            break
        elif active and re.match(r"\s*Case\b", line, re.I):
            for name in re.findall(r'"([^"\r\n]+)"', line):
                add(name, category, relative, number)


case_function("src/parser/lexer/lexer_keyword_table.fbs", "IsKeyword", "lexer_keyword")
case_function("src/surface/uxb_surface_registry.fbs", "UXBSurfaceKnown", "surface_registration")
relative = "src/type_binding/type_builtin_registry.fbs"
for number, line in enumerate(read(relative), 1):
    match = re.search(r'UXBBuiltinTypeRuleMake\("([^"]+)",\s*("[^"]+"|\w+),\s*"([^"]*)",\s*"([^"]*)"\)', line)
    if match:
        name, result, arguments, targets = match.groups()
        add(name, "typed_builtin", relative, number, return_type=result.strip('"'), argument_policy=arguments,
            declared_target_policy=targets)
relative = "src/parser/parser/parser_stmt_registry.fbs"
for number, line in enumerate(read(relative), 1):
    match = re.match(r'\s*AddStatementDispatchEntry\s+"([^"]+)",\s*(\w+)', line)
    if match:
        add(match[1], "statement_dispatch", relative, number, handler=match[2])

# Declarations are an inventory of the live wrapper inputs, not proof that a
# DLL exports them or that a target implements the declared ABI.
for path in sorted((ROOT / "libsx").rglob("*.bas")):
    relative = path.relative_to(ROOT).as_posix()
    namespaces = []
    for number, line in enumerate(read(relative), 1):
        if re.match(r"\s*END\s+NAMESPACE\b", line, re.I):
            if namespaces:
                namespaces.pop()
        ns = re.match(r"\s*NAMESPACE\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)", line, re.I)
        if ns:
            namespaces.append(ns[1])
        namespace = ".".join(namespaces)
        match = re.match(r"\s*(?:PUBLIC\s+|PRIVATE\s+)?(?:DECLARE\s+)?(FUNCTION|SUB)\s+([A-Za-z_]\w*)", line, re.I)
        if match and not line.lstrip().upper().startswith("PRIVATE"):
            add((namespace + "." if namespace else "") + match[2], "library_declaration", relative, number,
                routine_kind=match[1].upper())

ordered = sorted(rows.values(), key=lambda row: (row["category"], row["name"]))
counts = {category: sum(row["category"] == category for row in ordered)
          for category in sorted({row["category"] for row in ordered})}
record = {"schema": "uxb.source_acceptance_inventory.v1", "source_hashes": hashes,
          "counts": counts, "rows": ordered,
          "registration_counts": {category: sum(len(row['registrations']) for row in ordered if row['category'] == category) for category in counts},
          "limitations": ["All acceptance cells start UNMEASURED.",
                          "A registry route or declared target policy is not implemented feature support.",
                          "Library declarations do not prove DLL exports, ownership, or ABI behavior.",
                          "Types, provider manifests, operators and protocol coverage need separate inventories.",
                          "A whole-program PASS must not be assigned to every token appearing in the source."]}
(output / "inventory.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
with (output / "inventory.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["category", "name", "registration_count", *ENGINES])
    for row in ordered:
        writer.writerow([row["category"], row["name"], len(row["registrations"]),
                         *(row["acceptance"][engine] for engine in ENGINES)])
(output / "summary.json").write_text(json.dumps({"counts": counts, "rows": len(ordered),
                                               "measured_acceptance_cells": 0,
                                               "unmeasured_cells": len(ordered) * len(ENGINES)}, indent=2), encoding="utf-8")
print(json.dumps({"rows": len(ordered), "counts": counts, "output": str(output)}, ensure_ascii=False))
