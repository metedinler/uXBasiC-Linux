from __future__ import annotations

from pathlib import Path
import re
from typing import Callable, Iterable

from .model import AstNode, ConversionReport
from .source_model import SourceModel


CALL_DLL_API_RE = re.compile(r"\bCALL\s*(?:\(|\s+)\s*(DLL|API)\b", re.IGNORECASE)


class PdsxEmitter:
    """
    uXBasic AST JSON -> pdsX BASX emitter.

    Policy:
    - Source-first: if preprocessed/source line exists, preserve it exactly.
    - Structural fallback: if no source line exists, rebuild a pdsX/BASIC-like line from AST.
    - No .hx generation: pdsX/HXA/user owns .hx and .prf content.
    - CALL DLL/API preserved, plus REM notes for the programmer.
    - All known AST nodes are accounted in coverage, including helper/expression nodes consumed by owners.
    """

    def __init__(self, source: SourceModel, profile: str = "", keep_profile_line: bool = True) -> None:
        self.source = source
        self.profile = profile
        self.keep_profile_line = keep_profile_line
        self.lines: list[str] = []
        self.report = ConversionReport()
        self.indent = 0
        self._line_for_node_index: dict[int, int] = {}
        self._handled_keys: set[tuple[str, int]] = set()
        self._counted_keys: set[tuple[str, int]] = set()
        self.handlers: dict[str, Callable[[AstNode], None]] = {}
        self._register_handlers()

    # ------------------------------------------------------------------
    # Registry / conversion entry
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        for kind in ALL_KNOWN_AST_KINDS:
            self.handlers[kind] = self.emit_generic

        self.handlers.update({
            "PROGRAM": self.emit_program,
            "BLOCK": self.emit_block,
            "DIM_STMT": self.emit_dim_stmt,
            "REDIM_STMT": self.emit_redim_stmt,
            "CONST_STMT": self.emit_const_stmt,
            "ASSIGN_STMT": self.emit_assign_stmt,
            "EXPR_STMT": self.emit_expr_stmt,
            "PRINT_STMT": self.emit_print_stmt,
            "INPUT_STMT": self.emit_input_stmt,
            "INPUT_FILE_STMT": self.emit_input_stmt,
            "INPUTF_STMT": self.emit_input_stmt,
            "IF_STMT": self.emit_if_stmt,
            "ELSEIF_PART": self.emit_elseif_part,
            "ELSE_PART": self.emit_else_part,
            "SELECT_STMT": self.emit_select_stmt,
            "CASE_BLOCK": self.emit_case_block,
            "CASE_ELSE": self.emit_case_else,
            "FOR_STMT": self.emit_for_stmt,
            "FOR_EACH_STMT": self.emit_for_each_stmt,
            "DO_STMT": self.emit_do_stmt,
            "DO_EACH_STMT": self.emit_do_each_stmt,
            "EXIT_STMT": self.emit_exit_stmt,
            "RETURN_STMT": self.emit_return_stmt,
            "GOTO_STMT": self.emit_passthrough_stmt,
            "GOSUB_STMT": self.emit_passthrough_stmt,
            "LABEL_STMT": self.emit_label_stmt,
            "CALL_STMT": self.emit_call_stmt,
            "TRY_STMT": self.emit_try_stmt,
            "THROW_STMT": self.emit_unary_stmt,
            "ASSERT_STMT": self.emit_assert_stmt,
            "END_STMT": self.emit_passthrough_stmt,
            "DEFTYPE_STMT": self.emit_passthrough_stmt,
            "RANDOMIZE_STMT": self.emit_unary_stmt,
            "INCDEC_STMT": self.emit_incdec_stmt,
            "OPEN_STMT": self.emit_passthrough_stmt,
            "CLOSE_STMT": self.emit_passthrough_stmt,
            "GET_STMT": self.emit_passthrough_stmt,
            "PUT_STMT": self.emit_passthrough_stmt,
            "SEEK_STMT": self.emit_passthrough_stmt,
            "LOCATE_STMT": self.emit_passthrough_stmt,
            "COLOR_STMT": self.emit_passthrough_stmt,
            "CLS_STMT": self.emit_passthrough_stmt,
            "DELETE_STMT": self.emit_unary_stmt,
            "SETSTRINGSIZE_STMT": self.emit_passthrough_stmt,
            "POKEB_STMT": self.emit_passthrough_stmt,
            "POKEW_STMT": self.emit_passthrough_stmt,
            "POKED_STMT": self.emit_passthrough_stmt,
            "POKES_STMT": self.emit_passthrough_stmt,
            "MEMCOPYB_STMT": self.emit_passthrough_stmt,
            "MEMCOPYW_STMT": self.emit_passthrough_stmt,
            "MEMCOPYD_STMT": self.emit_passthrough_stmt,
            "MEMFILLB_STMT": self.emit_passthrough_stmt,
            "MEMFILLW_STMT": self.emit_passthrough_stmt,
            "MEMFILLD_STMT": self.emit_passthrough_stmt,
            "SETNEWOFFSET_STMT": self.emit_passthrough_stmt,
            "INLINE_STMT": self.emit_inline_stmt,
            "TYPE_STMT": self.emit_type_stmt,
            "CLASS_STMT": self.emit_class_stmt,
            "CLASS_FIELD": self.emit_class_field,
            "CLASS_FRIEND_STMT": self.emit_class_friend_stmt,
            "CLASS_PROPERTY_DECL": self.emit_property_stmt,
            "CLASS_PROPERTY_GET_STMT": self.emit_property_accessor_stmt,
            "CLASS_PROPERTY_SET_STMT": self.emit_property_accessor_stmt,
            "CLASS_METHOD_DECL": self.emit_method_stmt,
            "CLASS_CONSTRUCTOR_DECL": self.emit_constructor_stmt,
            "CLASS_DESTRUCTOR_DECL": self.emit_destructor_stmt,
            "CLASS_OPERATOR_DECL": self.emit_operator_stmt,
            "INTERFACE_STMT": self.emit_interface_stmt,
            "INTERFACE_METHOD_DECL": self.emit_interface_method_decl,
            "ENUM_STMT": self.emit_enum_stmt,
            "SUB_STMT": self.emit_sub_stmt,
            "FUNCTION_STMT": self.emit_function_stmt,
            "DECLARE_SUB_STMT": self.emit_passthrough_stmt,
            "DECLARE_FUNCTION_STMT": self.emit_passthrough_stmt,
            "MODULE_STMT": self.emit_module_stmt,
            "NAMESPACE_STMT": self.emit_namespace_stmt,
            "MAIN_STMT": self.emit_main_stmt,
            "IMPORT_STMT": self.emit_passthrough_stmt,
            "INCLUDE_STMT": self.emit_passthrough_stmt,
            "USING_STMT": self.emit_passthrough_stmt,
            "ALIAS_STMT": self.emit_passthrough_stmt,
            "EVENT_STMT": self.emit_event_like_stmt,
            "SLOT_STMT": self.emit_event_like_stmt,
            "SLOT_CONTROL_STMT": self.emit_event_like_stmt,
            "TRIGGER_STMT": self.emit_event_like_stmt,
            "PIPE_STMT": self.emit_event_like_stmt,
            "THREAD_STMT": self.emit_event_like_stmt,
            "PARALEL_STMT": self.emit_event_like_stmt,
        })

    def convert(self, root: AstNode) -> tuple[str, ConversionReport]:
        self.count_all_nodes(root)
        if self.profile and self.keep_profile_line:
            self.lines.append(f'PROFILE "{self.profile}"')
            self.lines.append("")
        self.emit_node(root)
        for c in self.source.remaining_comments():
            self.lines.append(c)
        text = "\n".join(self.lines).rstrip() + "\n"
        self.report.unhandled_counts = {
            k: self.report.node_counts.get(k, 0) - self.report.handled_counts.get(k, 0)
            for k in sorted(self.report.node_counts)
            if self.report.node_counts.get(k, 0) != self.report.handled_counts.get(k, 0)
        }
        return text, self.report

    # ------------------------------------------------------------------
    # Coverage helpers
    # ------------------------------------------------------------------

    def node_key(self, node: AstNode) -> tuple[str, int]:
        idx = node.index
        return ("idx", idx) if idx is not None else ("obj", id(node.raw))

    def count_all_nodes(self, root: AstNode) -> None:
        def walk(n: AstNode | None) -> None:
            if n is None:
                return
            key = self.node_key(n)
            if key in self._counted_keys:
                return
            self._counted_keys.add(key)
            self.report.count_node(n.kind)
            walk(n.left)
            walk(n.right)
            for ch in n.children:
                walk(ch)
        walk(root)

    def mark_handled(self, node: AstNode | None) -> None:
        if node is None:
            return
        key = self.node_key(node)
        if key in self._handled_keys:
            return
        self._handled_keys.add(key)
        self.report.count_handled(node.kind)

    def mark_tree_handled(self, node: AstNode | None) -> None:
        if node is None:
            return
        seen: set[tuple[str, int]] = set()
        def walk(n: AstNode | None) -> None:
            if n is None:
                return
            key = self.node_key(n)
            if key in seen:
                return
            seen.add(key)
            self.mark_handled(n)
            walk(n.left)
            walk(n.right)
            for ch in n.children:
                walk(ch)
        walk(node)

    # ------------------------------------------------------------------
    # Emission primitives
    # ------------------------------------------------------------------

    def emit_node(self, node: AstNode) -> None:
        handler = self.handlers.get(node.kind, self.emit_generic)
        handler(node)
        self.mark_handled(node)

    def emit_line(self, text: str, node: AstNode | None = None, mark_source: bool = False) -> None:
        if node and node.line:
            for c in self.source.pending_comments_before(node.line):
                self.lines.append(c)
        prefix = "    " * self.indent
        out_line = prefix + text if text else ""
        self.lines.append(out_line)
        out_no = len(self.lines)
        if node and node.index is not None:
            self._line_for_node_index[node.index] = out_no
            self.report.source_map.append({
                "node_index": node.index,
                "node_kind": node.kind,
                "source_line": node.line,
                "source_column": node.column,
                "output_line": out_no,
                "mode": "source" if mark_source else "structural",
                "text": text,
            })
        if mark_source and node and node.line:
            self.source.mark_emitted(node.line)
            self.report.source_lines_used += 1
        else:
            self.report.structural_lines_used += 1

    def source_exact(self, node: AstNode) -> str | None:
        if node.line and self.source.has_line(node.line) and node.line not in self.source.emitted_lines:
            raw = self.source.statement_line(node.line)
            if raw.strip() and not raw.lstrip().startswith("%%"):
                return raw
        return None

    def emit_source_or(self, node: AstNode, fallback: str, mark_children: bool = False) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            self.add_call_dll_api_notes_if_needed(exact, node)
            if mark_children:
                for ch in node.children:
                    self.mark_tree_handled(ch)
                self.mark_tree_handled(node.left)
                self.mark_tree_handled(node.right)
        else:
            self.emit_line(fallback, node)
            self.add_call_dll_api_notes_if_needed(fallback, node)

    def add_call_dll_api_notes_if_needed(self, text: str, node: AstNode) -> None:
        m = CALL_DLL_API_RE.search(text)
        if not m:
            return
        self.report.call_dll_api_count += 1
        kind = m.group(1).upper()
        note1 = f"REM uxbasic2pdsxS: CALL {kind} satırı aynen korundu."
        note2 = "REM uxbasic2pdsxS: pdsX/Python tarafında ctypes, cffi, pywin32, pythonnet veya özel .hx/.py sarmalayıcı ile programcı çözer."
        self.lines.append(("    " * self.indent) + note1)
        self.lines.append(("    " * self.indent) + note2)

    # ------------------------------------------------------------------
    # Statements / blocks
    # ------------------------------------------------------------------

    def emit_program(self, node: AstNode) -> None:
        for ch in node.children:
            self.emit_node(ch)

    def emit_block(self, node: AstNode) -> None:
        for ch in node.children:
            self.emit_node(ch)

    def emit_generic(self, node: AstNode) -> None:
        if self.is_statement_like(node):
            self.emit_passthrough_stmt(node)
        else:
            # Helper/expression nodes are converted by owners or expr(). If reached alone, emit a safe REM.
            self.report.warn("UXB2PDSX_HELPER_NODE_REACHED", f"Yardımcı AST node tek başına görüldü; pdsX çıktısına REM olarak işlendi: {node.kind}", node)
            self.emit_line(f"REM uxbasic2pdsxS: helper node {node.kind} value={node.value}", node)
            self.mark_tree_handled(node)

    def emit_passthrough_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node), mark_children=True)

    def emit_dim_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            for ch in node.children:
                self.mark_tree_handled(ch)
            return
        parts = []
        for decl in node.children:
            if decl.kind != "DIM_DECL":
                continue
            self.mark_handled(decl)
            seg = decl.value
            bounds = decl.child_kind("DIM_BOUNDS")
            if bounds:
                self.mark_handled(bounds)
                seg += "(" + ", ".join(self.expr(c) for c in bounds.children) + ")"
            typ = decl.child_kind("TYPE_REF")
            if typ:
                seg += " AS " + self.expr(typ)
            init = decl.child_kind("INIT_EXPR")
            if init:
                self.mark_handled(init)
                val_node = init.left or (init.children[0] if init.children else None)
                seg += " = " + self.expr(val_node)
            parts.append(seg)
        self.emit_line("DIM " + ", ".join(parts), node)

    def emit_redim_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node, keyword="REDIM"), mark_children=True)

    def emit_const_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node, keyword="CONST"), mark_children=True)

    def emit_assign_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            self.mark_tree_handled(node.left)
            self.mark_tree_handled(node.right)
            return
        op = node.op or "="
        self.emit_line(f"{self.expr(node.left)} {op} {self.expr(node.right)}", node)

    def emit_expr_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            for ch in node.children:
                self.mark_tree_handled(ch)
            self.mark_tree_handled(node.left)
            return
        self.emit_line(self.expr(node.left or (node.children[0] if node.children else node)), node)

    def emit_print_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            for ch in node.children:
                self.mark_tree_handled(ch)
            return
        args = []
        for ch in node.children:
            if ch.kind == "PRINT_ITEM":
                self.mark_handled(ch)
                args.append(self.expr(ch.left or (ch.children[0] if ch.children else ch)))
            else:
                args.append(self.expr(ch))
        self.emit_line("PRINT" + ((" " + ", ".join(args)) if args else ""), node)

    def emit_input_stmt(self, node: AstNode) -> None:
        keyword = node.kind.replace("_STMT", "").replace("_", " ")
        self.emit_source_or(node, self.reconstruct_statement(node, keyword=keyword), mark_children=True)

    def emit_if_stmt(self, node: AstNode) -> None:
        children = node.children
        if not children:
            self.emit_source_or(node, "IF TRUE THEN")
            return
        cond = children[0]
        rest = children[1:]
        if len(rest) == 1 and rest[0].line == node.line:
            exact = self.source_exact(node)
            if exact is not None:
                self.emit_line(exact, node, mark_source=True)
                self.mark_tree_handled(cond)
                self.mark_tree_handled(rest[0])
                return
        self.emit_line(f"IF {self.expr(cond)} THEN", node)
        self.indent += 1
        for ch in rest:
            if ch.kind not in {"ELSEIF_PART", "ELSE_PART"}:
                self.emit_node(ch)
        self.indent -= 1
        for ch in rest:
            if ch.kind in {"ELSEIF_PART", "ELSE_PART"}:
                self.emit_node(ch)
        self.emit_line("END IF", node)

    def emit_elseif_part(self, node: AstNode) -> None:
        cond = node.children[0] if node.children else None
        self.emit_line(f"ELSEIF {self.expr(cond)} THEN", node)
        self.indent += 1
        for ch in node.children[1:]:
            self.emit_node(ch)
        self.indent -= 1

    def emit_else_part(self, node: AstNode) -> None:
        self.emit_line("ELSE", node)
        self.indent += 1
        for ch in node.children:
            self.emit_node(ch)
        self.indent -= 1

    def emit_select_stmt(self, node: AstNode) -> None:
        selector = node.children[0] if node.children else None
        self.emit_line(f"SELECT CASE {self.expr(selector)}", node)
        self.indent += 1
        for ch in node.children[1:]:
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line("END SELECT", node)

    def emit_case_block(self, node: AstNode) -> None:
        case_parts = []
        body_start = 0
        for i, ch in enumerate(node.children):
            if ch.kind in {"CASE_IS_VALUE", "CASE_ELSE"}:
                case_parts.append(self.expr(ch))
                body_start = i + 1
            elif self.is_expression_like(ch):
                case_parts.append(self.expr(ch))
                body_start = i + 1
            else:
                break
        self.emit_line("CASE " + (", ".join(case_parts) if case_parts else ""), node)
        self.indent += 1
        for ch in node.children[body_start:]:
            self.emit_node(ch)
        self.indent -= 1

    def emit_case_else(self, node: AstNode) -> None:
        self.emit_line("CASE ELSE", node)
        self.indent += 1
        for ch in node.children:
            self.emit_node(ch)
        self.indent -= 1

    def emit_for_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            for ch in node.children[:3]:
                self.mark_tree_handled(ch)
        else:
            var = node.value or "I"
            start = self.expr(node.children[0]) if len(node.children) > 0 else "0"
            stop = self.expr(node.children[1]) if len(node.children) > 1 else "0"
            step = self.expr(node.children[2]) if len(node.children) > 2 else "1"
            self.emit_line(f"FOR {var} = {start} TO {stop} STEP {step}", node)
        self.indent += 1
        for ch in node.children[3:]:
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line("NEXT " + (node.value or ""), node)

    def emit_for_each_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
        else:
            items = node.child_kind("EACH_ITEMS") or (node.children[0] if node.children else None)
            target = node.value or "ITEM"
            seq = ", ".join(self.expr(ch) for ch in items.children) if items else "[]"
            if items:
                self.mark_handled(items)
            self.emit_line(f"FOR {target} IN {seq}", node)
        body = node.child_kind("EACH_BODY")
        self.indent += 1
        if body:
            self.mark_handled(body)
            for ch in body.children:
                self.emit_node(ch)
        else:
            for ch in node.children[1:]:
                self.emit_node(ch)
        self.indent -= 1
        self.emit_line("NEXT " + (node.value or ""), node)

    def emit_do_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
        else:
            self.emit_line("DO", node)
        self.indent += 1
        for ch in node.children:
            if self.is_statement_like(ch):
                self.emit_node(ch)
            else:
                self.mark_tree_handled(ch)
        self.indent -= 1
        self.emit_line("LOOP", node)

    def emit_do_each_stmt(self, node: AstNode) -> None:
        self.emit_passthrough_block(node, "DO EACH", "LOOP")

    def emit_exit_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, "EXIT" + ((" " + node.value) if node.value else ""), mark_children=True)

    def emit_return_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            self.mark_tree_handled(node.left)
            for ch in node.children:
                self.mark_tree_handled(ch)
            return
        val = self.expr(node.children[0]) if node.children else self.expr(node.left) if node.left else ""
        self.emit_line("RETURN" + ((" " + val) if val else ""), node)

    def emit_label_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
        else:
            self.emit_line((node.value or "LABEL") + ":", node)

    def emit_call_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            self.add_call_dll_api_notes_if_needed(exact, node)
            for ch in node.children:
                self.mark_tree_handled(ch)
            return
        line = "CALL " + ", ".join(self.expr(ch) for ch in node.children)
        if node.value:
            line = "CALL " + node.value + ((" " + ", ".join(self.expr(ch) for ch in node.children)) if node.children else "")
        self.emit_line(line, node)
        self.add_call_dll_api_notes_if_needed(line, node)

    def emit_try_stmt(self, node: AstNode) -> None:
        self.emit_line("TRY", node)
        self.indent += 1
        for ch in node.children:
            if ch.kind == "TRY_BODY":
                self.mark_handled(ch)
                for st in ch.children:
                    self.emit_node(st)
        self.indent -= 1
        for ch in node.children:
            if ch.kind == "CATCH_PART":
                self.emit_line("CATCH" + ((" " + ch.value) if ch.value else ""), ch)
                self.mark_handled(ch)
                self.indent += 1
                for st in ch.children:
                    self.emit_node(st)
                self.indent -= 1
            elif ch.kind == "FINALLY_PART":
                self.emit_line("FINALLY", ch)
                self.mark_handled(ch)
                self.indent += 1
                for st in ch.children:
                    self.emit_node(st)
                self.indent -= 1
        self.emit_line("END TRY", node)

    def emit_unary_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node), mark_children=True)

    def emit_assert_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node, keyword="ASSERT"), mark_children=True)

    def emit_incdec_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            self.mark_tree_handled(node.left)
            return
        self.emit_line(f"{self.expr(node.left)}{node.op or '++'}", node)

    def emit_inline_stmt(self, node: AstNode) -> None:
        self.emit_passthrough_stmt(node)
        for ch in node.children:
            if self.is_statement_like(ch):
                self.emit_node(ch)
            else:
                self.mark_tree_handled(ch)

    # ------------------------------------------------------------------
    # Declarations / OOP
    # ------------------------------------------------------------------

    def emit_type_stmt(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
        else:
            self.emit_line("TYPE " + node.value, node)
        self.indent += 1
        for ch in node.children:
            if ch.kind == "TYPE_FIELD":
                self.emit_type_field(ch)
            else:
                self.mark_tree_handled(ch)
        self.indent -= 1
        self.emit_line("END TYPE", node)

    def emit_type_field(self, node: AstNode) -> None:
        self.mark_handled(node)
        typ = node.child_kind("TYPE_REF")
        if typ:
            self.emit_line(f"{node.value} AS {self.expr(typ)}", node)
        else:
            self.emit_line(f"{node.value}" + ((" AS " + node.type_name) if node.type_name else ""), node)

    def emit_class_stmt(self, node: AstNode) -> None:
        bases = [ch.value for ch in node.children if ch.kind == "CLASS_BASE_REF" and ch.value]
        for ch in node.children:
            if ch.kind in {"CLASS_BASE_REF", "CLASS_IMPLEMENTS_REF", "CLASS_DECORATOR_REF", "CLASS_MIXIN_REF", "CLASS_FLAG", "CLASS_ACCESS"}:
                self.mark_tree_handled(ch)
        head = "CLASS " + node.value + ((" EXTENDS " + ", ".join(bases)) if bases else "")
        self.emit_line(head, node)
        self.indent += 1
        for ch in node.children:
            if ch.kind in {"CLASS_BASE_REF", "CLASS_IMPLEMENTS_REF", "CLASS_DECORATOR_REF", "CLASS_MIXIN_REF", "CLASS_FLAG", "CLASS_ACCESS"}:
                continue
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line("END CLASS", node)

    def emit_class_field(self, node: AstNode) -> None:
        exact = self.source_exact(node)
        if exact is not None:
            self.emit_line(exact, node, mark_source=True)
            for ch in node.children:
                self.mark_tree_handled(ch)
            return
        flags = [ch.value for ch in node.children if ch.kind == "CLASS_FIELD_FLAG" and ch.value]
        for ch in node.children:
            if ch.kind == "CLASS_FIELD_FLAG":
                self.mark_handled(ch)
        typ = node.child_kind("TYPE_REF")
        line = " ".join(flags + ["DIM", node.value]).strip()
        if typ:
            line += " AS " + self.expr(typ)
        elif node.type_name:
            line += " AS " + node.type_name
        self.emit_line(line, node)

    def emit_class_friend_stmt(self, node: AstNode) -> None:
        self.emit_source_or(node, self.reconstruct_statement(node, keyword="FRIEND"), mark_children=True)

    def emit_method_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "FUNCTION", "END FUNCTION")

    def emit_constructor_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "SUB", "END SUB", name_override="__init__")

    def emit_destructor_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "SUB", "END SUB", name_override="__del__")

    def emit_operator_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "FUNCTION", "END FUNCTION", name_override=f"OPERATOR_{node.op or 'UNKNOWN'}")

    def emit_property_stmt(self, node: AstNode) -> None:
        self.emit_line("PROPERTY " + node.value, node)
        self.indent += 1
        for ch in node.children:
            if ch.kind in {"CLASS_PROPERTY_FLAG", "CLASS_ACCESS", "TYPE_REF"}:
                self.mark_tree_handled(ch)
                continue
            self.emit_node(ch) if self.is_statement_like(ch) else self.mark_tree_handled(ch)
        self.indent -= 1
        self.emit_line("END PROPERTY", node)

    def emit_property_accessor_stmt(self, node: AstNode) -> None:
        keyword = "GET" if node.kind == "CLASS_PROPERTY_GET_STMT" else "SET"
        self.emit_passthrough_block(node, keyword, "END " + keyword)

    def emit_interface_stmt(self, node: AstNode) -> None:
        self.emit_line("INTERFACE " + node.value, node)
        self.indent += 1
        for ch in node.children:
            if ch.kind == "INTERFACE_METHOD_DECL":
                self.emit_interface_method_decl(ch)
            else:
                self.emit_node(ch) if self.is_statement_like(ch) else self.mark_tree_handled(ch)
        self.indent -= 1
        self.emit_line("END INTERFACE", node)

    def emit_interface_method_decl(self, node: AstNode) -> None:
        params = self.params(node)
        ret = (" AS " + node.type_name) if node.type_name else ""
        self.emit_line(f"FUNCTION {node.value}({params}){ret}", node)
        for ch in node.children:
            if ch.kind not in {"PARAM_DECL", "RETURN_TYPE", "TYPE_REF"}:
                self.mark_tree_handled(ch)

    def emit_enum_stmt(self, node: AstNode) -> None:
        bases = [ch for ch in node.children if ch.kind == "ENUM_BASE_TYPE"]
        self.emit_line("ENUM " + node.value + ((" AS " + self.expr(bases[0])) if bases else ""), node)
        for b in bases:
            self.mark_handled(b)
        self.indent += 1
        for ch in node.children:
            if ch.kind == "ENUM_ITEM":
                self.mark_handled(ch)
                val = ch.child_role("VALUE") or (ch.children[0] if ch.children else None)
                self.emit_line(ch.value + ((" = " + self.expr(val)) if val else ""), ch)
        self.indent -= 1
        self.emit_line("END ENUM", node)

    def emit_sub_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "SUB", "END SUB")

    def emit_function_stmt(self, node: AstNode) -> None:
        self.emit_routine(node, "FUNCTION", "END FUNCTION")

    def emit_routine(self, node: AstNode, keyword: str, end_keyword: str, name_override: str | None = None) -> None:
        name = name_override or node.value or "anonymous"
        params = self.params(node)
        ret = ""
        if keyword == "FUNCTION" and node.type_name:
            ret = " AS " + node.type_name
        self.emit_line(f"{keyword} {name}({params}){ret}", node)
        self.indent += 1
        for ch in node.children:
            if ch.kind in {"PARAM_DECL", "TYPE_REF", "RETURN_TYPE", "CLASS_ACCESS", "CLASS_METHOD_FLAG", "CLASS_FLAG"}:
                self.mark_tree_handled(ch)
                continue
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line(end_keyword, node)

    def emit_module_stmt(self, node: AstNode) -> None:
        self.emit_named_block(node, "MODULE", "END MODULE")

    def emit_namespace_stmt(self, node: AstNode) -> None:
        self.emit_named_block(node, "NAMESPACE", "END NAMESPACE")

    def emit_main_stmt(self, node: AstNode) -> None:
        self.emit_line("MAIN", node)
        self.indent += 1
        for ch in node.children:
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line("END MAIN", node)

    def emit_named_block(self, node: AstNode, keyword: str, end_keyword: str) -> None:
        self.emit_line(keyword + ((" " + node.value) if node.value else ""), node)
        self.indent += 1
        for ch in node.children:
            self.emit_node(ch)
        self.indent -= 1
        self.emit_line(end_keyword, node)

    def emit_event_like_stmt(self, node: AstNode) -> None:
        self.emit_passthrough_stmt(node)
        for ch in node.children:
            if self.is_statement_like(ch):
                self.indent += 1
                self.emit_node(ch)
                self.indent -= 1
            else:
                self.mark_tree_handled(ch)

    def emit_passthrough_block(self, node: AstNode, head: str, tail: str) -> None:
        self.emit_source_or(node, head)
        self.indent += 1
        for ch in node.children:
            if self.is_statement_like(ch):
                self.emit_node(ch)
            else:
                self.mark_tree_handled(ch)
        self.indent -= 1
        self.emit_line(tail, node)

    # ------------------------------------------------------------------
    # Reconstructors
    # ------------------------------------------------------------------

    def params(self, node: AstNode) -> str:
        out = []
        for ch in node.children:
            if ch.kind == "PARAM_DECL":
                self.mark_handled(ch)
                seg = ch.value
                if ch.flags:
                    # Conservative: flags are target/runtime metadata; keep names unchanged rather than guessing.
                    pass
                if ch.type_name:
                    seg += " AS " + ch.type_name
                typ = ch.child_kind("TYPE_REF")
                if typ and not ch.type_name:
                    seg += " AS " + self.expr(typ)
                out.append(seg)
        return ", ".join(out)

    def reconstruct_statement(self, node: AstNode, keyword: str | None = None) -> str:
        key = keyword or node.kind.replace("_STMT", "").replace("_", " ")
        args = []
        if node.value:
            args.append(node.value)
        args.extend(self.expr(ch) for ch in node.children if self.is_expression_like(ch))
        if node.left:
            args.append(self.expr(node.left))
        if node.right:
            args.append(self.expr(node.right))
        return key + ((" " + ", ".join(a for a in args if a)) if args else "")

    def expr(self, node: AstNode | None) -> str:
        if node is None:
            return ""
        self.mark_handled(node)
        k = node.kind
        if k in {"IDENT", "KEYWORD_REF"}:
            return node.value
        if k == "NUMBER":
            return node.value
        if k == "STRING":
            return '"' + node.value.replace('"', '""') + '"'
        if k == "BOOLEAN":
            return node.value.upper() if node.value else "TRUE"
        if k in {"TYPE_REF", "RETURN_TYPE", "MODE_REF", "ENUM_BASE_TYPE"}:
            return node.value or node.type_name
        if k == "BINARY":
            return f"{self.expr(node.left)} {node.op} {self.expr(node.right)}"
        if k == "UNARY":
            op = node.op or ""
            inner = self.expr(node.left or node.right or (node.children[0] if node.children else None))
            return f"{op}{inner}" if op in {"-", "+", "!", "~"} else f"{op} {inner}".strip()
        if k == "TERNARY_EXPR":
            cond = self.expr(node.left or (node.children[0] if node.children else None))
            a = self.expr(node.children[0]) if len(node.children) > 0 else ""
            b = self.expr(node.children[1]) if len(node.children) > 1 else self.expr(node.right)
            return f"IIF({cond}, {a}, {b})"
        if k == "CALL_EXPR":
            name = node.value or self.expr(node.left)
            args = ", ".join(self.expr(ch) for ch in node.children)
            return f"{name}({args})"
        if k in {"FIELD_EXPR", "MEMBER_EXPR"}:
            base_node = node.child_role("BASE") or node.left
            left = self.expr(base_node) if base_node else node.value
            right_node = node.right or node.child_role("MEMBER")
            right = self.expr(right_node) if right_node else ""
            if node.value and not right and left != node.value:
                return f"{left}.{node.value}"
            if node.value and not right:
                return node.value
            return f"{left}.{right}" if right else left
        if k == "INDEX_EXPR":
            base = self.expr(node.child_role("BASE") or node.left or (node.children[0] if node.children else None))
            indexes = [ch for ch in node.children if ch.role.upper() != "BASE"]
            if not indexes and node.right:
                indexes = [node.right]
            return f"{base}[{', '.join(self.expr(ch) for ch in indexes)}]"
        if k == "RANGE_EXPR":
            return f"{self.expr(node.left)} TO {self.expr(node.right)}"
        if k == "CAST_EXPR":
            typ = node.type_name or (node.children[0].value if node.children else "")
            val = self.expr(node.left or node.right or (node.children[-1] if node.children else None))
            return f"CAST({val} AS {typ})" if typ else f"CAST({val})"
        if k == "SIZEOF_EXPR":
            return "SIZEOF(" + self.expr(node.left or (node.children[0] if node.children else None)) + ")"
        if k == "INIT_EXPR":
            return self.expr(node.left or (node.children[0] if node.children else None))
        if k == "PROMPT_EXPR":
            return self.expr(node.left or (node.children[0] if node.children else None))
        if k == "CASE_IS_VALUE":
            return (node.op + " " if node.op else "IS ") + (self.expr(node.left or (node.children[0] if node.children else None)))
        if k in {"DIM_BOUNDS", "EACH_ITEMS", "SLOT_HEADER_ARGS", "ALIAS_TARGET", "USING_ITEM", "FRIEND_ITEM"}:
            return ", ".join(self.expr(ch) for ch in node.children) or node.value
        if k in {"PRINT_ITEM", "REDIM_DECL", "CONST_DECL", "DIM_DECL"}:
            return node.value or ", ".join(self.expr(ch) for ch in node.children)
        if node.value:
            return node.value
        if node.children:
            return ", ".join(self.expr(ch) for ch in node.children)
        return ""

    def is_statement_like(self, node: AstNode) -> bool:
        k = node.kind
        return k == "PROGRAM" or k == "BLOCK" or k.endswith("_STMT") or k.endswith("_DECL") or k in {
            "ELSEIF_PART", "ELSE_PART", "CASE_BLOCK", "CASE_ELSE", "TRY_BODY", "CATCH_PART", "FINALLY_PART",
            "TYPE_FIELD", "CLASS_FIELD", "ENUM_ITEM", "INTERFACE_METHOD_DECL",
        }

    def is_expression_like(self, node: AstNode) -> bool:
        k = node.kind
        return k in {
            "IDENT", "NUMBER", "STRING", "BOOLEAN", "TYPE_REF", "BINARY", "UNARY", "TERNARY_EXPR", "CALL_EXPR",
            "FIELD_EXPR", "KEYWORD_REF", "NEW_EXPR", "RANGE_EXPR", "INCDEC_EXPR", "INDEX_EXPR", "MEMBER_EXPR",
            "CAST_EXPR", "SIZEOF_EXPR", "INIT_EXPR", "PROMPT_EXPR", "CASE_IS_VALUE", "MODE_REF", "ENUM_BASE_TYPE",
            "DIM_BOUNDS", "EACH_ITEMS", "SLOT_HEADER_ARGS", "ALIAS_TARGET", "USING_ITEM", "FRIEND_ITEM",
        } or k.endswith("_EXPR")


ALL_KNOWN_AST_KINDS = {
    "PROGRAM", "BLOCK", "IDENT", "NUMBER", "STRING", "BOOLEAN", "TYPE_REF", "PARAM_DECL", "RETURN_TYPE",
    "BINARY", "UNARY", "TERNARY_EXPR", "CALL_EXPR", "FIELD_EXPR", "KEYWORD_REF", "NEW_EXPR", "RANGE_EXPR", "INCDEC_EXPR", "INDEX_EXPR", "MEMBER_EXPR", "CAST_EXPR", "SIZEOF_EXPR", "INIT_EXPR", "PROMPT_EXPR",
    "DIM_STMT", "DIM_DECL", "DIM_BOUNDS", "REDIM_STMT", "REDIM_DECL", "CONST_STMT", "CONST_DECL", "TYPE_STMT", "TYPE_FIELD", "CLASS_STMT", "CLASS_FIELD", "CLASS_PROPERTY_DECL", "CLASS_PROPERTY_GET_STMT", "CLASS_PROPERTY_SET_STMT", "CLASS_METHOD_DECL", "CLASS_CONSTRUCTOR_DECL", "CLASS_DESTRUCTOR_DECL", "CLASS_OPERATOR_DECL", "CLASS_BASE_REF", "CLASS_IMPLEMENTS_REF", "CLASS_DECORATOR_REF", "CLASS_MIXIN_REF", "CLASS_FLAG", "CLASS_FIELD_FLAG", "CLASS_METHOD_FLAG", "CLASS_PROPERTY_FLAG", "CLASS_ACCESS", "CLASS_FRIEND_STMT", "FRIEND_ITEM", "INTERFACE_STMT", "INTERFACE_METHOD_DECL", "ENUM_STMT", "ENUM_ITEM", "ENUM_BASE_TYPE", "SUB_STMT", "FUNCTION_STMT", "DECLARE_SUB_STMT", "DECLARE_FUNCTION_STMT", "MODULE_STMT", "NAMESPACE_STMT", "MAIN_STMT", "IMPORT_STMT", "INCLUDE_STMT", "USING_STMT", "USING_ITEM", "ALIAS_STMT", "ALIAS_TARGET",
    "ASSIGN_STMT", "EXPR_STMT", "PRINT_STMT", "PRINT_ITEM", "INPUT_STMT", "INPUT_FILE_STMT", "INPUTF_STMT", "IF_STMT", "ELSEIF_PART", "ELSE_PART", "SELECT_STMT", "CASE_BLOCK", "CASE_ELSE", "CASE_IS_VALUE", "FOR_STMT", "FOR_EACH_STMT", "EACH_ITEMS", "EACH_BODY", "DO_STMT", "DO_EACH_STMT", "EXIT_STMT", "RETURN_STMT", "GOTO_STMT", "GOSUB_STMT", "LABEL_STMT", "CALL_STMT", "TRY_STMT", "TRY_BODY", "CATCH_PART", "FINALLY_PART", "THROW_STMT", "ASSERT_STMT", "END_STMT", "DEFTYPE_STMT", "RANDOMIZE_STMT", "INCDEC_STMT",
    "OPEN_STMT", "MODE_REF", "CLOSE_STMT", "GET_STMT", "PUT_STMT", "SEEK_STMT", "LOCATE_STMT", "COLOR_STMT", "CLS_STMT",
    "DELETE_STMT", "SETSTRINGSIZE_STMT", "POKEB_STMT", "POKEW_STMT", "POKED_STMT", "POKES_STMT", "MEMCOPYB_STMT", "MEMCOPYW_STMT", "MEMCOPYD_STMT", "MEMFILLB_STMT", "MEMFILLW_STMT", "MEMFILLD_STMT", "SETNEWOFFSET_STMT", "INLINE_STMT",
    "EVENT_STMT", "SLOT_STMT", "SLOT_HEADER_ARGS", "SLOT_CONTROL_STMT", "TRIGGER_STMT", "PIPE_STMT", "THREAD_STMT", "PARALEL_STMT",
}
