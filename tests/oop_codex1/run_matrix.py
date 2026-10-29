"""Run expected-output checks against one isolated compiler, including real EXEs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "enum": ("ENUM Mode AS I32\n OFF=0\n ON=1\nEND ENUM\nPRINT Mode.ON\n", "1"),
    "enum_values": ("ENUM Choice AS I32\n Low = -3\n NextLow\n High = 12\n NextHigh\nEND ENUM\nPRINT Choice.Low\nPRINT choice.NextLow\nPRINT Choice.High\nPRINT Choice.NextHigh\n", "-3\n-2\n12\n13"),
    "class_field": ("CLASS Box\n DIM X AS I32\nEND CLASS\nDIM b AS Box=NEW Box()\nb.X=33\nPRINT b.X\n", "33"),
    "class_math": ("CLASS Point\n PUBLIC\n x AS I32\n y AS I32\n CONSTRUCTOR(a AS I32,b AS I32)\n THIS.x=a\n ME.y=b\n END CONSTRUCTOR\n METHOD Norm() AS I32\n RETURN THIS.x*THIS.x+ME.y*ME.y\n END METHOD\nEND CLASS\nDIM p AS Point=NEW Point(3,4)\nPRINT p.Norm()\n", "25"),
    "class_upcast": ("CLASS Base\n X AS I32\nEND CLASS\nCLASS Child EXTENDS Base\n Y AS I32\nEND CLASS\nDIM b AS Base\nb=NEW Child()\nb.X=42\nPRINT b.X\n", "42"),
    "class_upcast_explicit": ("CLASS Base\n X AS I32\nEND CLASS\nCLASS Child EXTENDS Base\n Y AS I32\nEND CLASS\nDIM b AS Base\nb = NEW Child()\nb.X=42\nPRINT b.X\n", "42"),
    "super_field": ("CLASS Base\n PUBLIC\n X AS I32\nEND CLASS\nCLASS Child EXTENDS Base\n PUBLIC\n METHOD Get() AS I32\n RETURN SUPER.X\n END METHOD\nEND CLASS\nDIM c AS Child=NEW Child()\nc.X=9\nPRINT c.Get()\n", "9"),
    "interface_upcast": ("INTERFACE IAnimal\n METHOD Speak() AS I32\nEND INTERFACE\nCLASS Dog IMPLEMENTS IAnimal\n PUBLIC\n VIRTUAL METHOD Speak() AS I32\n RETURN 42\n END METHOD\nEND CLASS\nDIM d AS Dog\nDIM i AS IAnimal\ni = d\nPRINT 7\n", "7"),
    "virtual_call": ("CLASS Animal\n PUBLIC\n VIRTUAL METHOD Speak() AS I32\n RETURN 1\n END METHOD\nEND CLASS\nCLASS Dog EXTENDS Animal\n PUBLIC\n OVERRIDE METHOD Speak() AS I32\n RETURN 42\n END METHOD\nEND CLASS\nDIM d AS Dog=NEW Dog()\nPRINT d.Speak()\n", "42"),
    "object_lifetime": ("CLASS A\n DESTRUCTOR()\n PRINT 100\n END DESTRUCTOR\nEND CLASS\nCLASS B EXTENDS A\n DESTRUCTOR()\n PRINT 200\n END DESTRUCTOR\nEND CLASS\nDIM b AS B = NEW B()\nDELETE b\nPRINT 1\n", "200\n100\n1"),
    "recursive_local": ("FUNCTION Fact(n AS I32) AS I32\n DIM result AS I32\n IF n <= 1 THEN\n  result = 1\n ELSE\n  result = n * Fact(n - 1)\n END IF\n RETURN result\nEND FUNCTION\nPRINT Fact(5)\n", "120"),
    "listget_numeric": ("DIM l AS LIST\nCALL LISTADD(l, 10)\nCALL LISTADD(l, 20)\nPRINT LISTGET(l, 1) + 5\n", "25"),
    "listget_assign": ("DIM l AS LIST\nCALL LISTADD(l, 10)\nDIM x AS I32\nx = LISTGET(l, 0)\nPRINT x\n", "10"),
    "dynamic_array": ("DIM n AS I32\nn = 5\nDIM arr(n) AS I32\narr(0) = 11\nPRINT arr(0)\n", "11"),
    "preprocessor_alias": ("%%ALIAS FIVE = 5\nPRINT FIVE\n", "5"),
    "runtime_alias": ("FUNCTION AddTwo(a AS I32, b AS I32) AS I32\n RETURN a + b\nEND FUNCTION\nALIAS TOPLA AS AddTwo\nPRINT TOPLA(2,3)\n", "5"),
    "byref": ("SUB BumpVal(BYREF x AS I32)\n x=x+1\nEND SUB\nDIM n AS I32\nn=10\nBumpVal(n)\nPRINT n\n", "11"),
    "byref_alias": ("SUB Change(BYREF x AS I32,BYREF y AS I32)\n x=1\n y=y+1\nEND SUB\nDIM n AS I32\nn=10\nChange(n,n)\nPRINT n\n", "2"),
}

def norm(value):
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()

def invoke(command, cwd):
    start = time.monotonic()
    try:
        p = subprocess.run([str(x) for x in command], cwd=cwd, capture_output=True, timeout=40)
        return {"code": p.returncode, "stdout": p.stdout.decode(errors="replace"),
                "stderr": p.stderr.decode(errors="replace"), "seconds": round(time.monotonic()-start, 3)}
    except subprocess.TimeoutExpired as e:
        return {"code": "TIMEOUT", "stdout": (e.stdout or b"").decode(errors="replace"),
                "stderr": (e.stderr or b"").decode(errors="replace"), "seconds": 40}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", type=Path, default=ROOT/"bin/uxb_codex1_oop.exe")
    parser.add_argument("--cases", default=",".join(CASES))
    parser.add_argument("--modes", default="AST,MIR,JS,x64_MIR,x64_AST")
    parser.add_argument("--label", default="fresh")
    args = parser.parse_args()
    exe = args.compiler.resolve()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = ROOT/"reports/system_audit_20260915"/(args.label+"_"+stamp)
    out.mkdir(parents=True)
    os.environ["PATH"] = str(ROOT/"bin") + os.pathsep + os.environ["PATH"]
    before = hashlib.sha256(exe.read_bytes()).hexdigest()
    results=[]
    for name in args.cases.split(","):
        source, expected=CASES[name]
        src=out/(name+".uxb")
        src.write_text(source, encoding="utf-8")
        for mode in args.modes.split(","):
            d=out/name/mode
            d.mkdir(parents=True)
            stdout=d/"stdout.txt"
            common=["--out-root",d/"out","--quiet"]
            if mode in ("AST","MIR"):
                cmd=[exe,"int",src,"--interpreter-backend",mode,
                     "--stdout-out" if mode=="AST" else "--mir-program-output-out",stdout,*common]
            elif mode=="JS":
                cmd=[exe,"jsw",src,"--js-out",d/"program.js",*common]
            else:
                cmd=[exe,"bld",src,"--x64-mode",mode.removeprefix("x64_"),*common]
            build=invoke(cmd,d)
            r={"name":name,"mode":mode,"expected":expected,"command":[str(x) for x in cmd],"compiler":build}
            actual=norm(stdout.read_text(encoding="utf-8-sig")) if stdout.exists() else ""
            if build["code"]==0 and mode not in ("AST","MIR"):
                if mode=="JS":
                    artifacts=[d/"program.js"] if (d/"program.js").exists() else []
                    run_cmd=[shutil.which("node"),*artifacts]
                else:
                    artifacts=list(d.rglob("program.exe"))
                    run_cmd=artifacts
                if len(artifacts)==1:
                    r["runtime"]=invoke(run_cmd,d)
                    actual=norm(r["runtime"]["stdout"])
                else:
                    r["missing_artifact"]=True
            r["actual"]=actual
            r["pass"]=build["code"]==0 and r.get("runtime",{}).get("code",0)==0 and actual==expected and not r.get("missing_artifact")
            results.append(r)
            print(json.dumps({"name":name,"mode":mode,"pass":r["pass"],"actual":actual,
                              "error":(build["stdout"]+build["stderr"]+r.get("runtime",{}).get("stderr",""))[-200:]}),flush=True)
            (out/"results.json").write_text(json.dumps({"compiler":str(exe),"sha256_before":before,"results":results},indent=2),encoding="utf-8")
    after=hashlib.sha256(exe.read_bytes()).hexdigest()
    (out/"results.json").write_text(json.dumps({"compiler":str(exe),"sha256_before":before,"sha256_after":after,
         "stable":before==after,"results":results},indent=2),encoding="utf-8")
    print(f"REPORT {out/'results.json'}",flush=True)
    return 0 if before==after and all(r["pass"] for r in results) else 1

if __name__=="__main__":
    sys.exit(main())
