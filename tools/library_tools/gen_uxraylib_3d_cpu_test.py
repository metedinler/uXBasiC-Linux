#!/usr/bin/env python3
"""uxraylib pencere gerektirmeyen 3B geometri duman testi uretici (S-052, raylib Models/3D dilimi 2).

Beklenen degerler, raylib'in KENDI islevlerini (libraylib) DOGRUDAN cagiran bir C referans programindan gelir; test
sarmalayicinin yuva/tutamac/kayit mekanigini sinar. Cikti: tests/libraries/uxraylib/uxraylib_3d_cpu_smoke.uxb
(dort motorda ayni sonucu vermek zorundadir). Kullanim: python tools/library_tools/gen_uxraylib_3d_cpu_test.py --root .
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

GCC = r"C:\msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe"
MSYS = r"C:\msys64\ucrt64"

# Her adim: (uxb_satirlari, c_satirlari, [(uxb_ifadesi, c_ifadesi), ...]) ; kontroller sayisal (double)
STEPS = [
    ("kure - kure",
     [],
     [],
     [("uxraylib.CheckCollisionSpheres(0, 0, 0, 1, 1.5, 0, 0, 1)", "CheckCollisionSpheres((Vector3){0,0,0},1,(Vector3){1.5f,0,0},1)"),
      ("uxraylib.CheckCollisionSpheres(0, 0, 0, 1, 3, 0, 0, 1)", "CheckCollisionSpheres((Vector3){0,0,0},1,(Vector3){3,0,0},1)")]),
    ("kutu - kutu / kutu - kure",
     ["uxraylib.VectorSlotSet(0, 0, 0, 0, 0)", "uxraylib.VectorSlotSet(1, 2, 2, 2, 0)",
      "uxraylib.VectorSlotSet(2, 1, 1, 1, 0)", "uxraylib.VectorSlotSet(3, 3, 3, 3, 0)",
      "uxraylib.VectorSlotSet(4, 5, 5, 5, 0)", "uxraylib.VectorSlotSet(5, 6, 6, 6, 0)"],
     ["BoundingBox b0={{0,0,0},{2,2,2}}, b1={{1,1,1},{3,3,3}}, b2={{5,5,5},{6,6,6}};"],
     [("uxraylib.CheckCollisionBoxesSlots(0, 1, 2, 3)", "CheckCollisionBoxes(b0,b1)"),
      ("uxraylib.CheckCollisionBoxesSlots(0, 1, 4, 5)", "CheckCollisionBoxes(b0,b2)"),
      ("uxraylib.CheckCollisionBoxSphereSlots(0, 1, 3, 1, 1, 1.5)", "CheckCollisionBoxSphere(b0,(Vector3){3,1,1},1.5f)"),
      ("uxraylib.CheckCollisionBoxSphereSlots(0, 1, 3, 1, 1, 0.5)", "CheckCollisionBoxSphere(b0,(Vector3){3,1,1},0.5f)")]),
    ("isin - kure",
     ["uxraylib.VectorSlotSet(0, 0, 0, -5, 0)", "uxraylib.VectorSlotSet(1, 0, 0, 1, 0)", "uxraylib.VectorSlotSet(2, 0, 3, -5, 0)"],
     ["Ray r0={{0,0,-5},{0,0,1}}; Ray rMiss={{0,3,-5},{0,0,1}};"],
     [("uxraylib.RayCollisionSphereSlots(0, 1, 0, 0, 0, 1)", "(rc=GetRayCollisionSphere(r0,(Vector3){0,0,0},1)).hit"),
      ("uxraylib.RayHit()", "rc.hit"),
      ("uxraylib.RayDistance()", "rc.distance"),
      ("uxraylib.RayPoint(0)", "rc.point.x"), ("uxraylib.RayPoint(1)", "rc.point.y"), ("uxraylib.RayPoint(2)", "rc.point.z"),
      ("uxraylib.RayNormal(0)", "rc.normal.x"), ("uxraylib.RayNormal(1)", "rc.normal.y"), ("uxraylib.RayNormal(2)", "rc.normal.z"),
      ("uxraylib.RayCollisionSphereSlots(2, 1, 0, 0, 0, 1)", "(rc=GetRayCollisionSphere(rMiss,(Vector3){0,0,0},1)).hit"),
      ("uxraylib.RayHit()", "rc.hit")]),
    ("isin - kutu",
     ["uxraylib.VectorSlotSet(0, 1, 1, -5, 0)", "uxraylib.VectorSlotSet(1, 0, 0, 1, 0)",
      "uxraylib.VectorSlotSet(2, 0, 0, 0, 0)", "uxraylib.VectorSlotSet(3, 2, 2, 2, 0)"],
     ["Ray rb={{1,1,-5},{0,0,1}}; BoundingBox bb={{0,0,0},{2,2,2}};"],
     [("uxraylib.RayCollisionBoxSlots(0, 1, 2, 3)", "(rc=GetRayCollisionBox(rb,bb)).hit"),
      ("uxraylib.RayDistance()", "rc.distance"),
      ("uxraylib.RayPoint(2)", "rc.point.z"), ("uxraylib.RayNormal(2)", "rc.normal.z")]),
    ("isin - ucgen / dortgen",
     ["uxraylib.VectorSlotSet(0, 0.5, 0.5, -3, 0)", "uxraylib.VectorSlotSet(1, 0, 0, 1, 0)",
      "uxraylib.VectorSlotSet(2, 0, 0, 0, 0)", "uxraylib.VectorSlotSet(3, 2, 0, 0, 0)",
      "uxraylib.VectorSlotSet(4, 0, 2, 0, 0)", "uxraylib.VectorSlotSet(5, 2, 2, 0, 0)"],
     ["Ray rt={{0.5f,0.5f,-3},{0,0,1}};"],
     [("uxraylib.RayCollisionTriangleSlots(0, 1, 2, 3, 4)", "(rc=GetRayCollisionTriangle(rt,(Vector3){0,0,0},(Vector3){2,0,0},(Vector3){0,2,0})).hit"),
      ("uxraylib.RayDistance()", "rc.distance"), ("uxraylib.RayPoint(0)", "rc.point.x"), ("uxraylib.RayPoint(1)", "rc.point.y"),
      ("uxraylib.RayNormal(2)", "rc.normal.z"),
      ("uxraylib.RayCollisionQuadSlots(0, 1, 2, 3, 5, 4)", "(rc=GetRayCollisionQuad(rt,(Vector3){0,0,0},(Vector3){2,0,0},(Vector3){2,2,0},(Vector3){0,2,0})).hit"),
      ("uxraylib.RayDistance()", "rc.distance"), ("uxraylib.RayNormal(2)", "rc.normal.z")]),
    ("kamera tutamaci ve donusumler",
     ["uxraylib.VectorSlotSet(0, 0, 2, 5, 0)", "uxraylib.VectorSlotSet(1, 0, 0, 0, 0)", "uxraylib.VectorSlotSet(2, 0, 1, 0, 0)",
      "cam = uxraylib.CameraCreate(0, 1, 2, 45.0, 0)"],
     ["Camera3D cam={{0,2,5},{0,0,0},{0,1,0},45.0f,CAMERA_PERSPECTIVE}; Vector2 sp; Ray sr; Matrix vm;"],
     [("uxraylib.CameraValid(cam)", "1"),
      ("uxraylib.CameraGet(cam, 0, 1)", "cam.position.y"), ("uxraylib.CameraGet(cam, 0, 2)", "cam.position.z"),
      ("uxraylib.CameraGet(cam, 2, 1)", "cam.up.y"), ("uxraylib.CameraGet(cam, 3, 0)", "cam.fovy"),
      ("uxraylib.CameraGet(cam, 4, 0)", "(double)cam.projection")]),
    ("kamera donusumleri",
     ["uxraylib.WorldToScreen(cam, 0, 0, 0, 800, 600)"],
     ["sp = GetWorldToScreenEx((Vector3){0,0,0}, cam, 800, 600);"],
     [("uxraylib.ResX()", "sp.x"), ("uxraylib.ResY()", "sp.y")]),
    ("kamera donusumleri 2",
     ["uxraylib.WorldToScreen(cam, 1.5, 0.5, -1, 800, 600)"],
     ["sp = GetWorldToScreenEx((Vector3){1.5f,0.5f,-1}, cam, 800, 600);"],
     [("uxraylib.ResX()", "sp.x"), ("uxraylib.ResY()", "sp.y")]),
    ("ekrandan dunya isini",
     ["uxraylib.ScreenToWorldRay(cam, 400, 300, 800, 600)"],
     ["sr = GetScreenToWorldRayEx((Vector2){400,300}, cam, 800, 600);"],
     [("uxraylib.ResGet(0, 0)", "sr.position.x"), ("uxraylib.ResGet(0, 1)", "sr.position.y"), ("uxraylib.ResGet(0, 2)", "sr.position.z"),
      ("uxraylib.ResGet(1, 0)", "sr.direction.x"), ("uxraylib.ResGet(1, 1)", "sr.direction.y"), ("uxraylib.ResGet(1, 2)", "sr.direction.z")]),
    ("UpdateCameraPro",
     ["uxraylib.CameraUpdatePro(cam, 1.0, 0.5, 0.25, 10.0, 5.0, 0.0, 0.0)"],
     ["UpdateCameraPro(&cam,(Vector3){1.0f,0.5f,0.25f},(Vector3){10.0f,5.0f,0.0f},0.0f);"],
     [("uxraylib.CameraGet(cam, 0, 0)", "cam.position.x"), ("uxraylib.CameraGet(cam, 0, 1)", "cam.position.y"), ("uxraylib.CameraGet(cam, 0, 2)", "cam.position.z"),
      ("uxraylib.CameraGet(cam, 1, 0)", "cam.target.x"), ("uxraylib.CameraGet(cam, 1, 1)", "cam.target.y"), ("uxraylib.CameraGet(cam, 1, 2)", "cam.target.z"),
      ("uxraylib.CameraGet(cam, 2, 0)", "cam.up.x"), ("uxraylib.CameraGet(cam, 2, 1)", "cam.up.y"), ("uxraylib.CameraGet(cam, 2, 2)", "cam.up.z")]),
    ("gorunum matrisi",
     ["m = uxraylib.CameraMatrix(cam)"],
     ["vm = GetCameraMatrix(cam); float vc[16]; memcpy(vc,&vm,sizeof vc);"],
     [(f"uxraylib.MatrixElement(m, {i})", f"vc[{i}]") for i in range(16)]),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    root = Path(ns.root)

    c = ['#include <stdio.h>', '#include <string.h>', '#include <raylib.h>', '#include <raymath.h>', 'int main(void){', '  RayCollision rc; (void)rc;']
    for _name, _u, clines, checks in STEPS:
        for l in clines:
            c.append("  " + l)
        for _ux, ce in checks:
            c.append(f'  printf("%.9g\\n", (double)({ce}));')
    c.append("  return 0; }")
    env = dict(os.environ)
    env["PATH"] = MSYS + r"\bin" + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory() as td:
        srcp = Path(td) / "ref.c"
        exep = Path(td) / "ref.exe"
        srcp.write_text("\n".join(c), encoding="utf-8")
        comp = subprocess.run([GCC, "-std=c11", "-O0", f"-I{MSYS}\\include", "-o", str(exep), str(srcp), f"-L{MSYS}\\lib", "-lraylib", "-lm"],
                              capture_output=True, text=True, env=env)
        if comp.returncode != 0:
            raise SystemExit("C referans programi derlenemedi:\n" + comp.stdout[:2000] + comp.stderr[:3000])
        out = subprocess.run([str(exep)], check=True, capture_output=True, text=True, env=env).stdout.strip().splitlines()

    it = iter(out)
    body = []
    for name, ulines, _c, checks in STEPS:
        body.append(f"    ' --- {name}")
        for l in ulines:
            body.append("    " + l)
        for ux, _ce in checks:
            val = next(it).strip()
            if ux.startswith("uxraylib.CheckCollision") or ux == "uxraylib.RayHit()" or ux.startswith("uxraylib.RayCollision") or ux == "uxraylib.CameraValid(cam)":
                body.append(f"    ASSERT {ux} = {int(float(val))}")
            else:
                body.append(f"    ASSERT Near({ux}, {val}) = 1")
    header = '''INCLUDE "include/modules/uxraylib_3d.uxmh"

' uxraylib pencere gerektirmeyen 3B geometri (S-052, raylib Models/3D dilimi 2) duman testi. GENERATED by
' tools/library_tools/gen_uxraylib_3d_cpu_test.py: beklenen degerler raylib'in kendi islevlerini DOGRUDAN cagiran bir C programindan gelir.
FUNCTION Near(a AS F64, b AS F64) AS I32
    DIM d AS F64
    DIM tol AS F64
    d = a - b
    IF d < 0.0 THEN d = 0.0 - d
    tol = 0.0005
    IF b > 1000.0 THEN tol = 0.05
    IF d < tol THEN RETURN 1
    RETURN 0
END FUNCTION

MAIN
    DIM cam AS I32
    DIM m AS I32
    ASSERT uxraylib.MatrixLiveCount() = 0
'''
    tail = '''    uxraylib.MatrixRelease(m)
    uxraylib.CameraRelease(cam)
    ASSERT uxraylib.CameraValid(cam) = 0
    ASSERT uxraylib.MatrixLiveCount() = 0
    uxraylib.MathClearError()
    ASSERT Near(uxraylib.CameraGet(0, 3, 0), 45.0) = 1
    ASSERT uxraylib.MathLastError() = 4
    uxraylib.MathClearError()
    PRINT "RAY3DCPU_PASS"
END MAIN
'''
    outp = root / "tests/libraries/uxraylib/uxraylib_3d_cpu_smoke.uxb"
    outp.write_text(header + "\n".join(body) + "\n" + tail, encoding="utf-8")
    print(f"yazildi: {outp} ({len(body)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
