#!/usr/bin/env python3
"""S-288: Ensure builtin call names newly added to runtime/type rules cannot bypass routine-name gate."""
from pathlib import Path
import re, sys
root = (Path(sys.argv[1]) if len(sys.argv) > 1 else
        next(p for p in Path(__file__).resolve().parents if (p/'src/main.bas').is_file()))
lexer = (root/'src/parser/lexer/lexer_keyword_table.fbs').read_text(encoding='utf-8-sig')
keywords = set(x.upper() for x in re.findall(r'"([a-z0-9_]+)"', lexer[:lexer.index('Private Function KeywordRegistryLookup')]))
runtime = (root/'src/runtime/memory_exec.fbs').read_text(encoding='utf-8-sig')
runtime = runtime[runtime.index('Private Function ExecIsBuiltinCallName'):runtime.index('Private Sub ExecSnapshotVars')]
runtime_names = set(re.findall(r'"([A-Z_0-9]+)"', runtime))
types = (root/'src/type_binding/type_builtin_registry.fbs').read_text(encoding='utf-8-sig')
type_names = set(re.findall(r'UXBBuiltinTypeRuleMake\("([A-Z_0-9]+)"', types))
parser = (root/'src/parser/parser/parser_shared.fbs').read_text(encoding='utf-8-sig')
parser = parser[parser.index('Private Function ParserNonKeywordBuiltinRoutineName'):parser.index('Private Sub ParserSetReservedNameError')]
parser_names = set(re.findall(r'"([A-Z_0-9]+)"', parser))
expected = (runtime_names | type_names) - keywords
missing = sorted(expected-parser_names)
excess = sorted(parser_names-expected)
print(f'Callable registry: {len(expected)} unkeyworded names; parser list: {len(parser_names)}')
if missing or excess:
    print('MISSING:', missing, 'EXCESS:', excess)
    sys.exit(1)
print('PASS: routine reserved-name registry agrees with runtime and type registries')
