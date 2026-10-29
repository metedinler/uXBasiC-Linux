#!/usr/bin/env python3
"""UXClazz source generator.

Transforms a deliberately small, line-oriented CLAZZ surface into ordinary
uXBasic CLASS/INTERFACE/MAGIC/PROPERTY code. The compiler core is untouched.

Supported MVP surface:
  CLAZZ VALUE|DATA|ENTITY|COMPONENT|ACTOR|NATIVE Name [EXTENDS Base]
      IMPLEMENTS IOne, ITwo
      USES TraitA, TraitB
      DERIVE EQ, HASH, CLONE, TOSTRING, JSON
      DECORATOR Name[(args)]
      [READONLY] FieldName AS Type
  END CLAZZ

The generated code is intentionally transparent and auditable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

VERSION = "1.0.0"
HEADER_RE = re.compile(
    r"^CLAZZ\s+(?:(VALUE|DATA|ENTITY|COMPONENT|ACTOR|NATIVE)\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+EXTENDS\s+([A-Za-z_][A-Za-z0-9_]*))?\s*$",
    re.IGNORECASE,
)
FIELD_RE = re.compile(
    r"^(READONLY\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+AS\s+([A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?)\s*$",
    re.IGNORECASE,
)


class UXClazzError(RuntimeError):
    pass


@dataclass
class FieldDef:
    name: str
    type_name: str
    readonly: bool = False
    source_line: int = 0


@dataclass
class ClazzDef:
    profile: str
    name: str
    base: str | None = None
    interfaces: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    derives: set[str] = field(default_factory=set)
    decorators: list[str] = field(default_factory=list)
    fields: list[FieldDef] = field(default_factory=list)
    source_line: int = 0
    trait_lines: list[int] = field(default_factory=list)
    derive_lines: dict[str, int] = field(default_factory=dict)


def strip_comment(line: str) -> str:
    # CLAZZ control files do not support quoted apostrophes; apostrophe begins a comment.
    return line.split("'", 1)[0].strip()


def split_names(text: str) -> list[str]:
    result = []
    for part in text.split(","):
        name = part.strip()
        if not name:
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?$", name):
            raise UXClazzError(f"invalid name/expression: {name}")
        result.append(name)
    return result


def validate_classes(classes: list[ClazzDef], source: str) -> None:
    """Check the emitted member namespace, not just the input field names."""
    class_names: dict[str, ClazzDef] = {}
    allowed_derives = {"EQ", "EQUALS", "HASH", "CLONE", "TOSTRING", "JSON"}
    for c in classes:
        class_key = c.name.upper()
        if class_key in class_names:
            previous = class_names[class_key]
            raise UXClazzError(
                f"{source}:{c.source_line}: duplicate class {c.name}; "
                f"first declaration at {source}:{previous.source_line}"
            )
        class_names[class_key] = c
        for derive in sorted(c.derives - allowed_derives):
            raise UXClazzError(
                f"{source}:{c.derive_lines.get(derive, c.source_line)}: "
                f"unsupported DERIVE {derive} in {c.name}"
            )

        members: dict[str, tuple[str, int]] = {}

        def reserve(name: str, owner: str, line: int) -> None:
            key = name.upper()
            if key in members:
                old_owner, old_line = members[key]
                raise UXClazzError(
                    f"{source}:{line}: generated member collision {c.name}.{name}: "
                    f"{owner}; conflicts with {old_owner} at {source}:{old_line}"
                )
            members[key] = (owner, line)

        fields: dict[str, FieldDef] = {}
        for f in c.fields:
            key = f.name.upper()
            if key in fields:
                old = fields[key]
                raise UXClazzError(
                    f"{source}:{f.source_line}: duplicate field {c.name}.{f.name}; "
                    f"first declaration at {source}:{old.source_line}"
                )
            fields[key] = f
            owner = f"field {f.name}"
            reserve(backing_name(f), owner, f.source_line)
            reserve(f"Get{f.name}", owner, f.source_line)
            if not f.readonly:
                reserve(f"Set{f.name}", owner, f.source_line)

        for i, trait in enumerate(c.traits):
            plain = trait.split("(", 1)[0]
            line = c.trait_lines[i] if i < len(c.trait_lines) else c.source_line
            for name in (f"__{plain}Part", f"Set{plain}Part", f"Get{plain}Part"):
                reserve(name, f"USES {trait}", line)
        reserve("__UxClazzMetadata", "generator metadata", c.source_line)
        derive_members = {"EQ": "Equals", "HASH": "MAGIC_HASH", "CLONE": "MAGIC_CLONE",
                          "TOSTRING": "MAGIC_TOSTRING", "JSON": "ToJson"}
        for derive in sorted({"EQ" if d == "EQUALS" else d for d in c.derives}):
            reserve(derive_members[derive], f"DERIVE {derive}",
                    c.derive_lines.get(derive, c.source_line))


def parse_text(text: str, source: str = "<memory>") -> list[ClazzDef]:
    classes: list[ClazzDef] = []
    current: ClazzDef | None = None
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = strip_comment(raw)
        if not line:
            continue
        if current is None:
            match = HEADER_RE.match(line)
            if not match:
                raise UXClazzError(f"{source}:{line_no}: expected CLAZZ header, got: {line}")
            profile = (match.group(1) or "DATA").upper()
            current = ClazzDef(profile=profile, name=match.group(2), base=match.group(3), source_line=line_no)
            continue
        if re.match(r"^END\s+CLAZZ$", line, re.IGNORECASE):
            if current.profile == "ENTITY":
                names = {f.name.upper() for f in current.fields}
                if "ID" not in names:
                    current.fields.insert(0, FieldDef("Id", "U64", True, current.source_line))
                if "VERSION" not in names:
                    current.fields.insert(1, FieldDef("Version", "U64", False, current.source_line))
            classes.append(current)
            current = None
            continue
        upper = line.upper()
        if upper.startswith("IMPLEMENTS "):
            current.interfaces.extend(split_names(line[len("IMPLEMENTS "):]))
        elif upper.startswith("USES "):
            traits = split_names(line[len("USES "):])
            current.traits.extend(traits)
            current.trait_lines.extend([line_no] * len(traits))
        elif upper.startswith("DERIVE "):
            derives = [x.upper() for x in split_names(line[len("DERIVE "):])]
            current.derives.update(derives)
            current.derive_lines.update({x: line_no for x in derives})
        elif upper.startswith("DECORATOR "):
            current.decorators.extend(split_names(line[len("DECORATOR "):]))
        else:
            match = FIELD_RE.match(line)
            if not match:
                raise UXClazzError(f"{source}:{line_no}: unsupported CLAZZ member: {line}")
            current.fields.append(FieldDef(match.group(2), match.group(3).upper(), bool(match.group(1)), line_no))
    if current is not None:
        raise UXClazzError(f"{source}:{current.source_line}: CLAZZ {current.name} is missing END CLAZZ")
    if not classes:
        raise UXClazzError(f"{source}: no CLAZZ declarations found")
    validate_classes(classes, source)
    return classes


def is_string(t: str) -> bool:
    return t.upper() == "STRING"


def is_float(t: str) -> bool:
    return t.upper() in {"F32", "F64", "F80", "F128"}


def backing_name(field: FieldDef) -> str:
    return "__" + field.name + "Value"


def value_to_string(field: FieldDef, owner: str = "THIS") -> str:
    ref = f"{owner}.{backing_name(field)}"
    return ref if is_string(field.type_name) else f"STR({ref})"


def hash_expr(field: FieldDef) -> str:
    ref = f"THIS.{backing_name(field)}"
    if is_string(field.type_name):
        return f"uxclazz_support.HashString({ref})"
    if is_float(field.type_name):
        return f"uxclazz_support.HashString(STR({ref}))"
    return f"uxclazz_support.HashI64(I64({ref}))"


def render_constructor(c: ClazzDef) -> list[str]:
    if not c.fields:
        return ["    CONSTRUCTOR()", "    END CONSTRUCTOR", ""]
    params = ", ".join(f"{f.name}Value AS {f.type_name}" for f in c.fields)
    lines = [f"    CONSTRUCTOR({params})"]
    for f in c.fields:
        lines.append(f"        THIS.{backing_name(f)} = {f.name}Value")
    lines += ["    END CONSTRUCTOR", ""]
    return lines


def render_equals(c: ClazzDef) -> list[str]:
    if not c.fields:
        expr = "TRUE"
    else:
        expr = " AND ".join(f"THIS.{backing_name(f)} == other.{backing_name(f)}" for f in c.fields)
    return [
        f"    VIRTUAL METHOD Equals(other AS {c.name}) AS BOOLEAN",
        f"        RETURN {expr}",
        "    END METHOD",
        "",
    ]


def render_hash(c: ClazzDef) -> list[str]:
    lines = ["    MAGIC HASH() AS U64", "        DIM h AS U64", "        h = 1469598103934665603"]
    for f in c.fields:
        lines.append(f"        h = uxclazz_support.HashCombine(h, {hash_expr(f)})")
    lines += ["        RETURN h", "    END MAGIC", ""]
    return lines


def render_clone(c: ClazzDef) -> list[str]:
    args = ", ".join(f"THIS.{backing_name(f)}" for f in c.fields)
    return [
        f"    MAGIC CLONE() AS {c.name}",
        f"        RETURN NEW {c.name}({args})" if args else f"        RETURN NEW {c.name}()",
        "    END MAGIC",
        "",
    ]


def render_tostring(c: ClazzDef) -> list[str]:
    if not c.fields:
        expr = f'"{c.name}()"'
    else:
        pieces: list[str] = [f'"{c.name}("']
        for idx, f in enumerate(c.fields):
            if idx:
                pieces.append('", "')
            pieces.append(f'"{f.name}="')
            pieces.append(value_to_string(f))
        pieces.append('")"')
        expr = " + ".join(pieces)
    return ["    MAGIC TOSTRING() AS STRING", f"        RETURN {expr}", "    END MAGIC", ""]


def render_json(c: ClazzDef) -> list[str]:
    if not c.fields:
        expr = '"{}"'
    else:
        pieces: list[str] = ['"{"']
        for idx, f in enumerate(c.fields):
            if idx:
                pieces.append('","')
            pieces.append(f'"\\\"{f.name}\\\":"')
            if is_string(f.type_name):
                pieces.extend(['"\\\""', f"uxclazz_support.EscapeJson(THIS.{backing_name(f)})", '"\\\""'])
            elif f.type_name == "BOOLEAN":
                pieces.append(f"uxclazz_support.BoolJson(THIS.{backing_name(f)})")
            else:
                pieces.append(f"STR(THIS.{backing_name(f)})")
        pieces.append('"}"')
        expr = " + ".join(pieces)
    return ["    METHOD ToJson() AS STRING", f"        RETURN {expr}", "    END METHOD", ""]


def render_trait_accessors(c: ClazzDef) -> tuple[list[str], list[str]]:
    private_lines: list[str] = []
    public_lines: list[str] = []
    for trait in c.traits:
        plain = trait.split("(", 1)[0]
        private_lines.append(f"    __{plain}Part AS {plain}")
        public_lines += [
            f"    METHOD Set{plain}Part(value AS {plain})",
            f"        THIS.__{plain}Part = value",
            "    END METHOD",
            "",
            f"    METHOD Get{plain}Part() AS {plain}",
            f"        RETURN THIS.__{plain}Part",
            "    END METHOD",
            "",
        ]
    return private_lines, public_lines


def render_metadata(c: ClazzDef) -> list[str]:
    decorators = ",".join(c.decorators)
    traits = ",".join(c.traits)
    interfaces = ",".join(c.interfaces)
    value = f"profile={c.profile};traits={traits};interfaces={interfaces};decorators={decorators}"
    value = value.replace('"', '\\"')
    return [
        "    STATIC METHOD __UxClazzMetadata() AS STRING",
        f'        RETURN "{value}"',
        "    END METHOD",
        "",
    ]


def render_class(c: ClazzDef) -> str:
    decl = f"CLASS {c.name}"
    if c.base:
        decl += f" EXTENDS {c.base}"
    if c.interfaces:
        decl += " IMPLEMENTS " + ", ".join(c.interfaces)
    trait_private, trait_public = render_trait_accessors(c)
    lines = [decl, "PRIVATE"]
    if not c.fields and not trait_private:
        lines.append("    __uxclazzEmpty AS I32")
    for f in c.fields:
        lines.append(f"    {backing_name(f)} AS {f.type_name}")
    lines.extend(trait_private)
    lines += ["", "PUBLIC"]
    lines.extend(render_constructor(c))
    for f in c.fields:
        lines += [
            f"    METHOD Get{f.name}() AS {f.type_name}",
            f"        RETURN THIS.{backing_name(f)}",
            "    END METHOD",
            "",
        ]
        if not f.readonly:
            lines += [
                f"    METHOD Set{f.name}(value AS {f.type_name})",
                f"        THIS.{backing_name(f)} = value",
                "    END METHOD",
                "",
            ]
    lines.extend(trait_public)
    derives = c.derives
    if "EQ" in derives or "EQUALS" in derives:
        lines.extend(render_equals(c))
    if "HASH" in derives:
        lines.extend(render_hash(c))
    if "CLONE" in derives:
        lines.extend(render_clone(c))
    if "TOSTRING" in derives:
        lines.extend(render_tostring(c))
    if "JSON" in derives:
        lines.extend(render_json(c))
    lines.extend(render_metadata(c))
    lines += ["END CLASS", ""]
    return "\n".join(lines)


def render(classes: list[ClazzDef], source_name: str) -> str:
    lines = [
        f"' Generated by UXClazz {VERSION} from {source_name}.",
        "' Compiler-core extension is not required.",
        'INCLUDE "include/modules/uxclazz.uxmh"',
        "",
    ]
    for c in classes:
        lines.append(render_class(c))
    return "\n".join(lines)


def manifest(classes: list[ClazzDef], source: Path, output: Path) -> dict:
    return {
        "generator": "uxclazz", "version": VERSION,
        "source": str(source), "output": str(output),
        "classes": [
            {
                "name": c.name, "profile": c.profile, "base": c.base,
                "interfaces": c.interfaces, "traits": c.traits,
                "derives": sorted(c.derives), "decorators": c.decorators,
                "fields": [{"name": f.name, "type": f.type_name, "readonly": f.readonly} for f in c.fields],
            }
            for c in classes
        ],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--check", action="store_true", help="parse and report without writing generated source")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        text = args.source.read_text(encoding="utf-8")
        classes = parse_text(text, str(args.source))
        if not args.check:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(render(classes, args.source.name), encoding="utf-8")
            print(f"WRITE generated uXBasic: {args.output}")
        if args.manifest:
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(json.dumps(manifest(classes, args.source, args.output), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"WRITE metadata: {args.manifest}")
        print(f"PASS UXClazz parse: {len(classes)} class(es)")
        return 0
    except (OSError, UXClazzError) as exc:
        print(f"FAIL UXClazz: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
