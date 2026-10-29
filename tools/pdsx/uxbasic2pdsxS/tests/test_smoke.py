from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_bridge(jdir: Path, out: Path, *extra: str):
    cmd = [
        sys.executable,
        str(ROOT / "uxbasic2pdsxS.py"),
        "--json-dir",
        str(jdir),
        "--out",
        str(out),
        "--project-name",
        "main",
        "--profile",
        "py30_std",
        *extra,
    ]
    return subprocess.run(cmd, text=True, capture_output=True)


def test_smoke_source_first_comments_and_call_notes(tmp_path: Path):
    jdir = tmp_path / "json"
    jdir.mkdir()
    ast = {
        "node_count": 7,
        "root": {
            "index": 0,
            "kind": "PROGRAM",
            "value": "",
            "op": "",
            "line": 1,
            "column": 1,
            "children": [
                {"index": 1, "kind": "DIM_STMT", "value": "", "op": "", "line": 2, "column": 1, "children": []},
                {"index": 2, "kind": "ASSIGN_STMT", "value": "", "op": "=", "line": 3, "column": 1, "left": {"index": 3, "kind": "IDENT", "value": "A"}, "right": {"index": 4, "kind": "NUMBER", "value": "10"}, "children": []},
                {"index": 5, "kind": "CALL_STMT", "value": "", "op": "", "line": 4, "column": 1, "children": []},
                {"index": 6, "kind": "PRINT_STMT", "value": "", "op": "", "line": 5, "column": 1, "children": []},
            ],
        },
    }
    (jdir / "ast.json").write_text(json.dumps(ast), encoding="utf-8")
    (jdir / "preprocessed.uxb").write_text(
        "' yorum\nDIM A AS INTEGER\nA = 10\nCALL(DLL, \"x.dll\", \"f\")\nPRINT A\n",
        encoding="utf-8",
    )
    out = tmp_path / "pdsx"
    r = run_bridge(jdir, out)
    assert r.returncode == 0, r.stderr
    basx = (out / "basx" / "main.basx").read_text(encoding="utf-8")
    assert "' yorum" in basx
    assert "CALL(DLL" in basx
    assert "ctypes" in basx
    assert (out / "main.prj").exists()
    report = json.loads((out / "reports" / "uxbasic2pdsxS_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["unhandled_total"] == 0
    assert report["summary"]["source_map_entries"] >= 4
    assert (out / "reports" / "source_map.json").exists()


def test_structural_fallback_handles_expression_nodes(tmp_path: Path):
    jdir = tmp_path / "json"
    jdir.mkdir()
    ast = {
        "node_count": 6,
        "root": {
            "index": 0,
            "kind": "PROGRAM",
            "children": [
                {
                    "index": 1,
                    "kind": "ASSIGN_STMT",
                    "op": "=",
                    "line": 0,
                    "column": 0,
                    "left": {"index": 2, "kind": "IDENT", "value": "A"},
                    "right": {
                        "index": 3,
                        "kind": "BINARY",
                        "op": "+",
                        "left": {"index": 4, "kind": "NUMBER", "value": "1"},
                        "right": {"index": 5, "kind": "NUMBER", "value": "2"},
                    },
                    "children": [],
                }
            ],
        },
    }
    (jdir / "ast.json").write_text(json.dumps(ast), encoding="utf-8")
    out = tmp_path / "pdsx"
    r = run_bridge(jdir, out, "--no-profile-line")
    assert r.returncode == 0, r.stderr
    basx = (out / "basx" / "main.basx").read_text(encoding="utf-8")
    assert "A = 1 + 2" in basx
    report = json.loads((out / "reports" / "uxbasic2pdsxS_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["unhandled_total"] == 0
