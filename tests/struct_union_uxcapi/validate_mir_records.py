#!/usr/bin/env python3
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
records = {r["name"].upper(): r for r in data.get("module", {}).get("record_types", [])}

def require(name: str):
    if name not in records:
        raise SystemExit(f"FAIL: record missing: {name}")
    return records[name]

def fields(record):
    return {f["name"].upper(): f for f in record.get("fields", [])}

vec = require("VEC2")
assert vec["kind"] == "struct" and vec["abi"] == "c"
assert vec["size"] == 8 and vec["alignment"] == 4
assert vec["ffi_by_value"] is True and vec["ffi_by_reference"] is True
assert fields(vec)["X"]["offset"] == 0
assert fields(vec)["Y"]["offset"] == 4

union = require("NUMBERBITS")
assert union["kind"] == "union" and union["size"] == 8
assert fields(union)["ASU64"]["offset"] == 0
assert fields(union)["ASF64"]["offset"] == 0
assert union["ffi_by_value"] is False and union["ffi_by_reference"] is True

packed = require("PACKEDHEADER")
assert packed["kind"] == "struct" and packed["pack"] == 1
assert packed["size"] == 5 and packed["alignment"] == 1
assert packed["ffi_by_value"] is False
assert fields(packed)["VALUE"]["offset"] == 1

aligned = require("ALIGNEDVALUE")
assert aligned["explicit_alignment"] == 16
assert aligned["size"] == 16 and aligned["alignment"] == 16
assert aligned["ffi_by_value"] is False

print("PASS: MIR record_types STRUCT/UNION/PACK/ALIGN")
