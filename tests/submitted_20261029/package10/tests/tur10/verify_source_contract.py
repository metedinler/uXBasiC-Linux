from pathlib import Path
root=Path(__file__).resolve().parents[2]/'degistirilmis_kaynaklar'/'src'
checks={
 'parser unallocated bounds marker': ('parser/parser/parser_stmt_decl_dim_redim.fbs','ps.ast.nodes(boundsNode).op = "UNALLOCATED_ARRAY"'),
 'parser init forbidden': ('parser/parser/parser_stmt_decl_dim_redim.fbs','DIM: unallocated array cannot have an initializer'),
 'atomic decl storage retained': ('parser/parser/parser_stmt_decl_dim_redim.fbs','If storageClass <> "" Then ps.ast.nodes(declNode).op = storageClass'),
 'AST runtime empty array': ('runtime/memory_exec.fbs','ExecArrayResizeVar(es, varName, 0, -1, 0)'),
 'MIR DIM with tag': ('semantic/mir_lower_stmt_core_split.fbs','"UNALLOCATED"'),
 'MIR runtime LBOUND': ('semantic/mir_lower_array_dim.fbs','runtimeForm = 1'),
 'MIR interpreter empty heap': ('interpreter/mir/mir_interp_dispatch.fbs','ctx.heap.slots(arrayId).boundsDeclared = 1'),
 'native MIR descriptor': ('codegen/x64/mir_x64_arrays.fbs','MIRX64Emit cg, "    mov qword [rcx + 16], -1"'),
 'legacy scalar descriptor': ('codegen/x64/code_generator.fbs','X64EmitText cg, "    mov qword [rcx + 16], -1"'),
 'legacy SDA recognition': ('codegen/x64/helpers/x64_codegen_dynamic_class_arrays.fbs','dynamicDecl = 1'),
}
for label,(file,frag) in checks.items():
 if frag not in (root/file).read_text(encoding='utf-8-sig'):
  raise AssertionError(label)
 print('PASS',label)
print({'passed':len(checks),'total':len(checks),'scope':'static source checks, not executable compiler tests'})
