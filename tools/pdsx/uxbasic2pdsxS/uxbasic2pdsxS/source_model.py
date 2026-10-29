from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


_FULL_COMMENT_RE = re.compile(r"^\s*(?:'|REM\b|#)", re.IGNORECASE)


def read_text_any(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def split_basic_inline_comment(line: str) -> tuple[str, str]:
    """Split at apostrophe outside double quotes. Returns (code, comment)."""
    in_str = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_str and i + 1 < len(line) and line[i + 1] == '"':
                i += 2
                continue
            in_str = not in_str
        elif ch == "'" and not in_str:
            return line[:i].rstrip(), line[i:]
        i += 1
    return line.rstrip(), ""


def is_full_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or bool(_FULL_COMMENT_RE.match(line))


@dataclass
class SourceModel:
    path: Path | None = None
    lines: list[str] = field(default_factory=list)
    emitted_lines: set[int] = field(default_factory=set)
    cursor: int = 1

    @classmethod
    def empty(cls) -> "SourceModel":
        return cls()

    @classmethod
    def from_path(cls, path: Path) -> "SourceModel":
        text = read_text_any(path)
        return cls(path=path, lines=text.splitlines())

    @classmethod
    def discover(cls, json_dir: Path, explicit: Path | None = None) -> "SourceModel":
        if explicit and explicit.exists():
            return cls.from_path(explicit)
        candidates = [
            json_dir / "preprocessed.uxb",
            json_dir / "preprocessed.bas",
            json_dir / "preprocessed.basx",
            json_dir / "source.uxb",
            json_dir / "main.uxb",
            json_dir / "input.uxb",
        ]
        for p in candidates:
            if p.exists():
                return cls.from_path(p)
        return cls.empty()

    def has_line(self, line_no: int) -> bool:
        return 1 <= line_no <= len(self.lines)

    def raw_line(self, line_no: int) -> str:
        return self.lines[line_no - 1] if self.has_line(line_no) else ""

    def statement_line(self, line_no: int) -> str:
        raw = self.raw_line(line_no)
        return raw.rstrip("\r\n")

    def mark_emitted(self, line_no: int) -> None:
        if line_no > 0:
            self.emitted_lines.add(line_no)
            if line_no >= self.cursor:
                self.cursor = line_no + 1

    def pending_comments_before(self, line_no: int) -> list[str]:
        out: list[str] = []
        if not self.lines or line_no <= 0:
            return out
        stop = min(line_no, len(self.lines) + 1)
        while self.cursor < stop:
            raw = self.raw_line(self.cursor)
            if self.cursor not in self.emitted_lines and is_full_comment_or_blank(raw):
                out.append(raw.rstrip())
                self.emitted_lines.add(self.cursor)
            self.cursor += 1
        return out

    def remaining_comments(self) -> list[str]:
        out: list[str] = []
        while self.cursor <= len(self.lines):
            raw = self.raw_line(self.cursor)
            if self.cursor not in self.emitted_lines and is_full_comment_or_blank(raw):
                out.append(raw.rstrip())
                self.emitted_lines.add(self.cursor)
            self.cursor += 1
        return out

    def inline_comment(self, line_no: int) -> str:
        if not self.has_line(line_no):
            return ""
        _, comment = split_basic_inline_comment(self.raw_line(line_no))
        return comment
