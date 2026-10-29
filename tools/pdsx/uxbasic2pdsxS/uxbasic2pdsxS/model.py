from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass
class AstNode:
    raw: dict[str, Any]

    @property
    def index(self) -> int | None:
        v = self.raw.get("index")
        return int(v) if isinstance(v, int) or (isinstance(v, str) and v.isdigit()) else None

    @property
    def kind(self) -> str:
        return str(self.raw.get("kind") or "").upper()

    @property
    def value(self) -> str:
        return str(self.raw.get("value") or "")

    @property
    def op(self) -> str:
        return str(self.raw.get("op") or "")

    @property
    def line(self) -> int:
        v = self.raw.get("line") or self.raw.get("lineNo") or 0
        try:
            return int(v)
        except Exception:
            return 0

    @property
    def column(self) -> int:
        v = self.raw.get("column") or self.raw.get("colNo") or 0
        try:
            return int(v)
        except Exception:
            return 0

    @property
    def role(self) -> str:
        return str(self.raw.get("role") or "").upper()

    @property
    def type_name(self) -> str:
        return str(self.raw.get("type") or self.raw.get("typeName") or "")

    @property
    def symbol(self) -> str:
        return str(self.raw.get("symbol") or "")

    @property
    def flags(self) -> int:
        try:
            return int(self.raw.get("flags") or 0)
        except Exception:
            return 0

    @property
    def source_file(self) -> str:
        return str(self.raw.get("sourceFile") or "")

    @property
    def children(self) -> list[AstNode]:
        out: list[AstNode] = []
        for ch in self.raw.get("children") or []:
            if isinstance(ch, dict):
                out.append(AstNode(ch))
        return out

    @property
    def left(self) -> AstNode | None:
        x = self.raw.get("left")
        return AstNode(x) if isinstance(x, dict) else None

    @property
    def right(self) -> AstNode | None:
        x = self.raw.get("right")
        return AstNode(x) if isinstance(x, dict) else None

    def child_kind(self, kind: str) -> AstNode | None:
        k = kind.upper()
        for ch in self.children:
            if ch.kind == k:
                return ch
        return None

    def children_kind(self, kind: str) -> list[AstNode]:
        k = kind.upper()
        return [ch for ch in self.children if ch.kind == k]

    def child_role(self, role: str) -> AstNode | None:
        r = role.upper()
        for ch in self.children:
            if ch.role == r:
                return ch
        return None

    def visible_children(self) -> list[AstNode]:
        return [ch for ch in self.children if ch.kind not in {"TYPE_REF", "RETURN_TYPE", "CLASS_ACCESS", "CLASS_FLAG", "CLASS_FIELD_FLAG", "CLASS_METHOD_FLAG", "CLASS_PROPERTY_FLAG"}]


@dataclass
class Diagnostic:
    level: str
    code: str
    message: str
    node_kind: str = ""
    line: int = 0
    column: int = 0
    node_index: int | None = None


@dataclass
class ConversionReport:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    node_counts: dict[str, int] = field(default_factory=dict)
    handled_counts: dict[str, int] = field(default_factory=dict)
    source_lines_used: int = 0
    structural_lines_used: int = 0
    call_dll_api_count: int = 0
    unhandled_counts: dict[str, int] = field(default_factory=dict)
    source_map: list[dict[str, Any]] = field(default_factory=list)

    def count_node(self, kind: str) -> None:
        self.node_counts[kind] = self.node_counts.get(kind, 0) + 1

    def count_handled(self, kind: str) -> None:
        self.handled_counts[kind] = self.handled_counts.get(kind, 0) + 1

    def warn(self, code: str, message: str, node: AstNode | None = None) -> None:
        self.diagnostics.append(
            Diagnostic(
                level="WARN",
                code=code,
                message=message,
                node_kind=node.kind if node else "",
                line=node.line if node else 0,
                column=node.column if node else 0,
                node_index=node.index if node else None,
            )
        )

    def error(self, code: str, message: str, node: AstNode | None = None) -> None:
        self.diagnostics.append(
            Diagnostic(
                level="ERROR",
                code=code,
                message=message,
                node_kind=node.kind if node else "",
                line=node.line if node else 0,
                column=node.column if node else 0,
                node_index=node.index if node else None,
            )
        )
