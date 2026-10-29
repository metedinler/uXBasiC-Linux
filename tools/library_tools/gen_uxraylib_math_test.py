#!/usr/bin/env python3
"""uxraylib raymath duman testi uretici (S-052).

Beklenen degerler UXBASIC/ADAPTER kullanmadan, raymath.h'yi DOGRUDAN cagiran kucuk bir C programindan gelir
(gcc ile derlenip calistirilir): boylece test, sarmalayicinin argüman siralamasi / bilesen eslemesi / kayit-tutamac
mekanigini sinar, matematigin kendisini degil. Uretilen dosya tests/libraries/uxraylib/uxraylib_math_smoke.uxb'dir
ve dort motorda (AST, canonical-MIR, native x64, legacy AST-x64) ayni sonucu vermek zorundadir.

Kullanim: python tools/library_tools/gen_uxraylib_math_test.py --root .
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

GCC = r"C:\msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe"
INC = r"C:\msys64\ucrt64\include"

# --- olgular ------------------------------------------------------------------------------------------------------
# ('f', uxb_ifadesi, c_ifadesi)                  -> skaler (F64)
# ('i', uxb_ifadesi, c_ifadesi)                  -> tamsayi
# ('v2'|'v3'|'v4', uxb_cagrisi, c_ifadesi)       -> kayit 0 bilesenleri
# ('m', [uxb satirlari], 'sonuc_degiskeni', c_ifadesi) -> matris (16 eleman)
SCALARS = [
    ("f", "uxraylib.Clamp(5, 0, 3)", "Clamp(5, 0, 3)"),
    ("f", "uxraylib.Clamp(-1, 0, 3)", "Clamp(-1, 0, 3)"),
    ("f", "uxraylib.Lerp(10, 20, 0.25)", "Lerp(10, 20, 0.25f)"),
    ("f", "uxraylib.Normalize(15, 10, 20)", "Normalize(15, 10, 20)"),
    ("f", "uxraylib.Remap(5, 0, 10, 100, 200)", "Remap(5, 0, 10, 100, 200)"),
    ("f", "uxraylib.Wrap(7, 0, 5)", "Wrap(7, 0, 5)"),
    ("f", "uxraylib.Wrap(-1, 0, 5)", "Wrap(-1, 0, 5)"),
    ("i", "uxraylib.FloatEquals(1.0, 1.0)", "FloatEquals(1.0f, 1.0f)"),
    ("i", "uxraylib.FloatEquals(1.0, 1.1)", "FloatEquals(1.0f, 1.1f)"),
    ("f", "uxraylib.Vector2Length(3, 4)", "Vector2Length((Vector2){3, 4})"),
    ("f", "uxraylib.Vector2LengthSqr(3, 4)", "Vector2LengthSqr((Vector2){3, 4})"),
    ("f", "uxraylib.Vector2DotProduct(1, 2, 3, 4)", "Vector2DotProduct((Vector2){1, 2}, (Vector2){3, 4})"),
    ("f", "uxraylib.Vector2Distance(1, 1, 4, 5)", "Vector2Distance((Vector2){1, 1}, (Vector2){4, 5})"),
    ("f", "uxraylib.Vector2Angle(1, 0, 0, 1)", "Vector2Angle((Vector2){1, 0}, (Vector2){0, 1})"),
    ("f", "uxraylib.Vector2LineAngle(0, 0, 1, 1)", "Vector2LineAngle((Vector2){0, 0}, (Vector2){1, 1})"),
    ("f", "uxraylib.Vector3Length(2, 3, 6)", "Vector3Length((Vector3){2, 3, 6})"),
    ("f", "uxraylib.Vector3LengthSqr(2, 3, 6)", "Vector3LengthSqr((Vector3){2, 3, 6})"),
    ("f", "uxraylib.Vector3DotProduct(1, 2, 3, 4, 5, 6)", "Vector3DotProduct((Vector3){1, 2, 3}, (Vector3){4, 5, 6})"),
    ("f", "uxraylib.Vector3Distance(1, 2, 3, 4, 6, 15)", "Vector3Distance((Vector3){1, 2, 3}, (Vector3){4, 6, 15})"),
    ("f", "uxraylib.Vector3Angle(1, 0, 0, 0, 1, 0)", "Vector3Angle((Vector3){1, 0, 0}, (Vector3){0, 1, 0})"),
    ("f", "uxraylib.Vector4Length(1, 2, 2, 4)", "Vector4Length((Vector4){1, 2, 2, 4})"),
    ("f", "uxraylib.Vector4DotProduct(1, 2, 3, 4, 5, 6, 7, 8)", "Vector4DotProduct((Vector4){1, 2, 3, 4}, (Vector4){5, 6, 7, 8})"),
    ("f", "uxraylib.QuaternionLength(1, 2, 2, 4)", "QuaternionLength((Quaternion){1, 2, 2, 4})"),
    ("i", "uxraylib.Vector3Equals(1, 2, 3, 1, 2, 3)", "Vector3Equals((Vector3){1, 2, 3}, (Vector3){1, 2, 3})"),
    ("i", "uxraylib.Vector2Equals(1, 2, 1, 3)", "Vector2Equals((Vector2){1, 2}, (Vector2){1, 3})"),
]

VECTORS = [
    ("v2", "uxraylib.Vector2Zero()", "Vector2Zero()"),
    ("v2", "uxraylib.Vector2One()", "Vector2One()"),
    ("v2", "uxraylib.Vector2Add(1, 2, 3, 4)", "Vector2Add((Vector2){1, 2}, (Vector2){3, 4})"),
    ("v2", "uxraylib.Vector2AddValue(1, 2, 10)", "Vector2AddValue((Vector2){1, 2}, 10)"),
    ("v2", "uxraylib.Vector2Subtract(1, 2, 3, 5)", "Vector2Subtract((Vector2){1, 2}, (Vector2){3, 5})"),
    ("v2", "uxraylib.Vector2SubtractValue(5, 6, 2)", "Vector2SubtractValue((Vector2){5, 6}, 2)"),
    ("v2", "uxraylib.Vector2Scale(1, 2, 3)", "Vector2Scale((Vector2){1, 2}, 3)"),
    ("v2", "uxraylib.Vector2Multiply(2, 3, 4, 5)", "Vector2Multiply((Vector2){2, 3}, (Vector2){4, 5})"),
    ("v2", "uxraylib.Vector2Negate(1, -2)", "Vector2Negate((Vector2){1, -2})"),
    ("v2", "uxraylib.Vector2Divide(8, 9, 2, 3)", "Vector2Divide((Vector2){8, 9}, (Vector2){2, 3})"),
    ("v2", "uxraylib.Vector2Normalize(3, 4)", "Vector2Normalize((Vector2){3, 4})"),
    ("v2", "uxraylib.Vector2Lerp(0, 0, 10, 20, 0.5)", "Vector2Lerp((Vector2){0, 0}, (Vector2){10, 20}, 0.5f)"),
    ("v2", "uxraylib.Vector2Reflect(1, -1, 0, 1)", "Vector2Reflect((Vector2){1, -1}, (Vector2){0, 1})"),
    ("v2", "uxraylib.Vector2Min(1, 5, 3, 2)", "Vector2Min((Vector2){1, 5}, (Vector2){3, 2})"),
    ("v2", "uxraylib.Vector2Max(1, 5, 3, 2)", "Vector2Max((Vector2){1, 5}, (Vector2){3, 2})"),
    ("v2", "uxraylib.Vector2Rotate(1, 0, 1.5707963)", "Vector2Rotate((Vector2){1, 0}, 1.5707963f)"),
    ("v2", "uxraylib.Vector2MoveTowards(0, 0, 10, 0, 3)", "Vector2MoveTowards((Vector2){0, 0}, (Vector2){10, 0}, 3)"),
    ("v2", "uxraylib.Vector2Invert(2, 4)", "Vector2Invert((Vector2){2, 4})"),
    ("v2", "uxraylib.Vector2Clamp(5, -5, 0, 0, 2, 2)", "Vector2Clamp((Vector2){5, -5}, (Vector2){0, 0}, (Vector2){2, 2})"),
    ("v2", "uxraylib.Vector2ClampValue(3, 4, 1, 2)", "Vector2ClampValue((Vector2){3, 4}, 1, 2)"),
    ("v3", "uxraylib.Vector3Zero()", "Vector3Zero()"),
    ("v3", "uxraylib.Vector3One()", "Vector3One()"),
    ("v3", "uxraylib.Vector3Add(1, 2, 3, 4, 5, 6)", "Vector3Add((Vector3){1, 2, 3}, (Vector3){4, 5, 6})"),
    ("v3", "uxraylib.Vector3AddValue(1, 2, 3, 10)", "Vector3AddValue((Vector3){1, 2, 3}, 10)"),
    ("v3", "uxraylib.Vector3Subtract(4, 5, 6, 1, 2, 3)", "Vector3Subtract((Vector3){4, 5, 6}, (Vector3){1, 2, 3})"),
    ("v3", "uxraylib.Vector3SubtractValue(4, 5, 6, 1)", "Vector3SubtractValue((Vector3){4, 5, 6}, 1)"),
    ("v3", "uxraylib.Vector3Scale(1, 2, 3, 2)", "Vector3Scale((Vector3){1, 2, 3}, 2)"),
    ("v3", "uxraylib.Vector3Multiply(1, 2, 3, 4, 5, 6)", "Vector3Multiply((Vector3){1, 2, 3}, (Vector3){4, 5, 6})"),
    ("v3", "uxraylib.Vector3CrossProduct(1, 0, 0, 0, 1, 0)", "Vector3CrossProduct((Vector3){1, 0, 0}, (Vector3){0, 1, 0})"),
    ("v3", "uxraylib.Vector3CrossProduct(1, 2, 3, 4, 5, 6)", "Vector3CrossProduct((Vector3){1, 2, 3}, (Vector3){4, 5, 6})"),
    ("v3", "uxraylib.Vector3Perpendicular(1, 2, 3)", "Vector3Perpendicular((Vector3){1, 2, 3})"),
    ("v3", "uxraylib.Vector3Negate(1, -2, 3)", "Vector3Negate((Vector3){1, -2, 3})"),
    ("v3", "uxraylib.Vector3Divide(8, 9, 10, 2, 3, 5)", "Vector3Divide((Vector3){8, 9, 10}, (Vector3){2, 3, 5})"),
    ("v3", "uxraylib.Vector3Normalize(0, 3, 4)", "Vector3Normalize((Vector3){0, 3, 4})"),
    ("v3", "uxraylib.Vector3Project(3, 4, 0, 1, 0, 0)", "Vector3Project((Vector3){3, 4, 0}, (Vector3){1, 0, 0})"),
    ("v3", "uxraylib.Vector3Reject(3, 4, 0, 1, 0, 0)", "Vector3Reject((Vector3){3, 4, 0}, (Vector3){1, 0, 0})"),
    ("v3", "uxraylib.Vector3RotateByAxisAngle(1, 0, 0, 0, 0, 1, 1.5707963)", "Vector3RotateByAxisAngle((Vector3){1, 0, 0}, (Vector3){0, 0, 1}, 1.5707963f)"),
    ("v3", "uxraylib.Vector3RotateByQuaternion(1, 0, 0, 0, 0, 0.70710678, 0.70710678)", "Vector3RotateByQuaternion((Vector3){1, 0, 0}, (Quaternion){0, 0, 0.70710678f, 0.70710678f})"),
    ("v3", "uxraylib.Vector3MoveTowards(0, 0, 0, 0, 0, 10, 4)", "Vector3MoveTowards((Vector3){0, 0, 0}, (Vector3){0, 0, 10}, 4)"),
    ("v3", "uxraylib.Vector3Lerp(0, 0, 0, 10, 20, 30, 0.25)", "Vector3Lerp((Vector3){0, 0, 0}, (Vector3){10, 20, 30}, 0.25f)"),
    ("v3", "uxraylib.Vector3Reflect(1, -1, 0, 0, 1, 0)", "Vector3Reflect((Vector3){1, -1, 0}, (Vector3){0, 1, 0})"),
    ("v3", "uxraylib.Vector3Min(1, 5, 3, 3, 2, 4)", "Vector3Min((Vector3){1, 5, 3}, (Vector3){3, 2, 4})"),
    ("v3", "uxraylib.Vector3Max(1, 5, 3, 3, 2, 4)", "Vector3Max((Vector3){1, 5, 3}, (Vector3){3, 2, 4})"),
    ("v3", "uxraylib.Vector3Invert(2, 4, 8)", "Vector3Invert((Vector3){2, 4, 8})"),
    ("v3", "uxraylib.Vector3Clamp(5, -5, 1, 0, 0, 0, 2, 2, 2)", "Vector3Clamp((Vector3){5, -5, 1}, (Vector3){0, 0, 0}, (Vector3){2, 2, 2})"),
    ("v3", "uxraylib.Vector3ClampValue(3, 4, 0, 1, 2)", "Vector3ClampValue((Vector3){3, 4, 0}, 1, 2)"),
    ("v3", "uxraylib.Vector3Refract(1, -1, 0, 0, 1, 0, 0.5)", "Vector3Refract((Vector3){1, -1, 0}, (Vector3){0, 1, 0}, 0.5f)"),
    ("v4", "uxraylib.Vector4Add(1, 2, 3, 4, 5, 6, 7, 8)", "Vector4Add((Vector4){1, 2, 3, 4}, (Vector4){5, 6, 7, 8})"),
    ("v4", "uxraylib.Vector4Scale(1, 2, 3, 4, 2)", "Vector4Scale((Vector4){1, 2, 3, 4}, 2)"),
    ("v4", "uxraylib.Vector4Normalize(1, 2, 2, 4)", "Vector4Normalize((Vector4){1, 2, 2, 4})"),
    ("v4", "uxraylib.Vector4Lerp(0, 0, 0, 0, 4, 8, 12, 16, 0.5)", "Vector4Lerp((Vector4){0, 0, 0, 0}, (Vector4){4, 8, 12, 16}, 0.5f)"),
    ("v4", "uxraylib.QuaternionIdentity()", "QuaternionIdentity()"),
    ("v4", "uxraylib.QuaternionMultiply(0, 0, 0.70710678, 0.70710678, 0, 0, 0.70710678, 0.70710678)", "QuaternionMultiply((Quaternion){0, 0, 0.70710678f, 0.70710678f}, (Quaternion){0, 0, 0.70710678f, 0.70710678f})"),
    ("v4", "uxraylib.QuaternionInvert(0, 0, 0.5, 0.5)", "QuaternionInvert((Quaternion){0, 0, 0.5f, 0.5f})"),
    ("v4", "uxraylib.QuaternionNormalize(0, 0, 3, 4)", "QuaternionNormalize((Quaternion){0, 0, 3, 4})"),
    ("v4", "uxraylib.QuaternionSlerp(0, 0, 0, 1, 0, 0, 0.70710678, 0.70710678, 0.5)", "QuaternionSlerp((Quaternion){0, 0, 0, 1}, (Quaternion){0, 0, 0.70710678f, 0.70710678f}, 0.5f)"),
    ("v4", "uxraylib.QuaternionNlerp(0, 0, 0, 1, 0, 0, 0.70710678, 0.70710678, 0.5)", "QuaternionNlerp((Quaternion){0, 0, 0, 1}, (Quaternion){0, 0, 0.70710678f, 0.70710678f}, 0.5f)"),
    ("v4", "uxraylib.QuaternionFromAxisAngle(0, 1, 0, 1.5707963)", "QuaternionFromAxisAngle((Vector3){0, 1, 0}, 1.5707963f)"),
    ("v4", "uxraylib.QuaternionFromEuler(0.1, 0.2, 0.3)", "QuaternionFromEuler(0.1f, 0.2f, 0.3f)"),
    ("v3", "uxraylib.QuaternionToEuler(0.0996, 0.0, 0.0, 0.995)", "QuaternionToEuler((Quaternion){0.0996f, 0.0f, 0.0f, 0.995f})"),
    ("v4", "uxraylib.QuaternionFromVector3ToVector3(1, 0, 0, 0, 1, 0)", "QuaternionFromVector3ToVector3((Vector3){1, 0, 0}, (Vector3){0, 1, 0})"),
    ("v4", "uxraylib.QuaternionScale(1, 2, 3, 4, 0.5)", "QuaternionScale((Quaternion){1, 2, 3, 4}, 0.5f)"),
    ("v4", "uxraylib.QuaternionAdd(1, 2, 3, 4, 4, 3, 2, 1)", "QuaternionAdd((Quaternion){1, 2, 3, 4}, (Quaternion){4, 3, 2, 1})"),
]

# matris olgulari: (uxb satirlari, sonuc tutamac degiskeni, C ifadesi)
MATRICES = [
    (["a = uxraylib.MatrixIdentity()"], "a", "MatrixIdentity()"),
    (["a = uxraylib.MatrixTranslate(1, 2, 3)"], "a", "MatrixTranslate(1, 2, 3)"),
    (["a = uxraylib.MatrixScale(2, 3, 4)"], "a", "MatrixScale(2, 3, 4)"),
    (["a = uxraylib.MatrixRotateX(0.5)"], "a", "MatrixRotateX(0.5f)"),
    (["a = uxraylib.MatrixRotateY(0.5)"], "a", "MatrixRotateY(0.5f)"),
    (["a = uxraylib.MatrixRotateZ(0.5)"], "a", "MatrixRotateZ(0.5f)"),
    (["a = uxraylib.MatrixRotate(0, 1, 0, 0.7)"], "a", "MatrixRotate((Vector3){0, 1, 0}, 0.7f)"),
    (["a = uxraylib.MatrixRotateXYZ(0.1, 0.2, 0.3)"], "a", "MatrixRotateXYZ((Vector3){0.1f, 0.2f, 0.3f})"),
    (["a = uxraylib.MatrixRotateZYX(0.1, 0.2, 0.3)"], "a", "MatrixRotateZYX((Vector3){0.1f, 0.2f, 0.3f})"),
    (["a = uxraylib.MatrixTranslate(1, 2, 3)", "b = uxraylib.MatrixScale(2, 3, 4)", "c = uxraylib.MatrixMultiply(a, b)"],
     "c", "MatrixMultiply(MatrixTranslate(1, 2, 3), MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixTranslate(1, 2, 3)", "b = uxraylib.MatrixScale(2, 3, 4)", "c = uxraylib.MatrixAdd(a, b)"],
     "c", "MatrixAdd(MatrixTranslate(1, 2, 3), MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixTranslate(1, 2, 3)", "b = uxraylib.MatrixScale(2, 3, 4)", "c = uxraylib.MatrixSubtract(a, b)"],
     "c", "MatrixSubtract(MatrixTranslate(1, 2, 3), MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixTranslate(1, 2, 3)", "c = uxraylib.MatrixInvert(a)"], "c", "MatrixInvert(MatrixTranslate(1, 2, 3))"),
    (["a = uxraylib.MatrixRotateY(0.5)", "c = uxraylib.MatrixTranspose(a)"], "c", "MatrixTranspose(MatrixRotateY(0.5f))"),
    (["a = uxraylib.MatrixLookAt(0, 2, 5, 0, 0, 0, 0, 1, 0)"], "a", "MatrixLookAt((Vector3){0, 2, 5}, (Vector3){0, 0, 0}, (Vector3){0, 1, 0})"),
    (["a = uxraylib.MatrixPerspective(1.0471976, 1.5, 0.1, 100)"], "a", "MatrixPerspective(1.0471976, 1.5, 0.1, 100)"),
    (["a = uxraylib.MatrixOrtho(-4, 4, -3, 3, 0.1, 50)"], "a", "MatrixOrtho(-4, 4, -3, 3, 0.1, 50)"),
    (["a = uxraylib.MatrixFrustum(-1, 1, -0.75, 0.75, 0.5, 20)"], "a", "MatrixFrustum(-1, 1, -0.75, 0.75, 0.5, 20)"),
    (["q = uxraylib.QuaternionToMatrix(0, 0, 0.70710678, 0.70710678)"], "q", "QuaternionToMatrix((Quaternion){0, 0, 0.70710678f, 0.70710678f})"),
]

# matris -> skaler/vektor (uxb, c)
MATRIX_SCALARS = [
    (["a = uxraylib.MatrixScale(2, 3, 4)"], "uxraylib.MatrixDeterminant(a)", "MatrixDeterminant(MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixScale(2, 3, 4)"], "uxraylib.MatrixTrace(a)", "MatrixTrace(MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixRotateXYZ(0.1, 0.2, 0.3)"], "uxraylib.MatrixDeterminant(a)", "MatrixDeterminant(MatrixRotateXYZ((Vector3){0.1f, 0.2f, 0.3f}))"),
]
MATRIX_VECTORS = [
    (["a = uxraylib.MatrixTranslate(1, 2, 3)"], "uxraylib.Vector3Transform(1, 1, 1, a)", "v3",
     "Vector3Transform((Vector3){1, 1, 1}, MatrixTranslate(1, 2, 3))"),
    (["a = uxraylib.MatrixRotateZ(1.5707963)"], "uxraylib.Vector3Transform(1, 0, 0, a)", "v3",
     "Vector3Transform((Vector3){1, 0, 0}, MatrixRotateZ(1.5707963f))"),
    (["a = uxraylib.MatrixScale(2, 3, 4)"], "uxraylib.Vector2Transform(1, 1, a)", "v2",
     "Vector2Transform((Vector2){1, 1}, MatrixScale(2, 3, 4))"),
    (["a = uxraylib.MatrixRotateY(0.4)"], "uxraylib.QuaternionTransform(0, 0, 0, 1, a)", "v4",
     "QuaternionTransform((Quaternion){0, 0, 0, 1}, MatrixRotateY(0.4f))"),
    (["p = uxraylib.MatrixPerspective(1.0471976, 1.5, 0.1, 100)", "v = uxraylib.MatrixLookAt(0, 2, 5, 0, 0, 0, 0, 1, 0)"],
     "uxraylib.Vector3Unproject(0.1, -0.2, 0.5, p, v)", "v3",
     "Vector3Unproject((Vector3){0.1f, -0.2f, 0.5f}, MatrixPerspective(1.0471976, 1.5, 0.1, 100), MatrixLookAt((Vector3){0, 2, 5}, (Vector3){0, 0, 0}, (Vector3){0, 1, 0}))"),
    (["a = uxraylib.MatrixRotateXYZ(0.3, 0.4, 0.5)", "u = uxraylib.MatrixCopy(a)", "b = uxraylib.MatrixTranslate(0, 0, 0)"],
     "uxraylib.Vector3Transform(1, 2, 3, u)", "v3", "Vector3Transform((Vector3){1, 2, 3}, MatrixRotateXYZ((Vector3){0.3f, 0.4f, 0.5f}))"),
]


def cfloat(v: float) -> str:
    return f"{v:.9g}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    root = Path(ns.root)

    # ---- C referans programi: her olgu icin degerleri yazdir
    lines = ['#include <stdio.h>', '#define RAYMATH_IMPLEMENTATION', '#include <raymath.h>',
             'static void PM(Matrix m){ const float*f=(const float*)&m; for(int i=0;i<16;i++) printf(" %.9g", (double)f[i]); printf("\\n"); }',
             'int main(void){']
    for kind, _u, c in SCALARS:
        lines.append(f'  printf("%.9g\\n", (double)({c}));' if kind == "f" else f'  printf("%d\\n", (int)({c}));')
    for kind, _u, c in VECTORS:
        n = {"v2": 2, "v3": 3, "v4": 4}[kind]
        comps = ["x", "y", "z", "w"][:n]
        fmt = " ".join(["%.9g"] * n)
        args = ", ".join(f"(double)_r.{cc}" for cc in comps)
        lines.append(f'  {{ {"Vector2" if kind=="v2" else "Vector3" if kind=="v3" else "Vector4"} _r = {c}; printf("{fmt}\\n", {args}); }}')
    for _ul, _h, c in MATRICES:
        lines.append(f'  PM({c});')
    for _ul, _u, c in MATRIX_SCALARS:
        lines.append(f'  printf("%.9g\\n", (double)({c}));')
    for _ul, _u, kind, c in MATRIX_VECTORS:
        n = {"v2": 2, "v3": 3, "v4": 4}[kind]
        comps = ["x", "y", "z", "w"][:n]
        fmt = " ".join(["%.9g"] * n)
        args = ", ".join(f"(double)_r.{cc}" for cc in comps)
        lines.append(f'  {{ {"Vector2" if kind=="v2" else "Vector3" if kind=="v3" else "Vector4"} _r = {c}; printf("{fmt}\\n", {args}); }}')
    lines += ['  return 0; }']

    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "ref.c"
        exe = Path(td) / "ref.exe"
        src.write_text("\n".join(lines), encoding="utf-8")
        env = dict(os.environ)
        env["PATH"] = str(Path(GCC).parent) + os.pathsep + env.get("PATH", "")
        comp = subprocess.run([GCC, "-std=c11", "-O0", f"-I{INC}", "-o", str(exe), str(src), "-lm"], capture_output=True, text=True, env=env)
        if comp.returncode != 0:
            raise SystemExit("C referans programi derlenemedi:\n" + comp.stdout[:2000] + comp.stderr[:3000])
        out = subprocess.run([str(exe)], check=True, capture_output=True, text=True, env=env).stdout.strip().splitlines()

    it = iter(out)
    body = []

    def vec_asserts(call: str, kind: str, values: list[str]) -> list[str]:
        n = {"v2": 2, "v3": 3, "v4": 4}[kind]
        res = [f"    {call}"]
        for i, comp in enumerate(["X", "Y", "Z", "W"][:n]):
            res.append(f"    ASSERT Near(uxraylib.Res{comp}(), {values[i]}) = 1")
        return res

    body.append("    ' --- skalerler / bool sonuclar")
    for kind, ux, _c in SCALARS:
        val = next(it).strip()
        if kind == "f":
            body.append(f"    ASSERT Near({ux}, {val}) = 1")
        else:
            body.append(f"    ASSERT {ux} = {val}")
    body.append("    ' --- vektor / kuaterniyon sonuclari (kayit 0)")
    for kind, ux, _c in VECTORS:
        vals = next(it).split()
        body.extend(vec_asserts(ux, kind, vals))
    body.append("    ' --- matrisler (16 eleman, raylib alan sirasi m0 m4 m8 m12 / m1 ...: indeks = sutun*4 + satir)")
    for ulines, hvar, _c in MATRICES:
        vals = next(it).split()
        for l in ulines:
            body.append("    " + l)
        for i, v in enumerate(vals):
            body.append(f"    ASSERT Near(uxraylib.MatrixElement({hvar}, {i}), {v}) = 1")
        # olusan tum tutamaclari birak
        for name in sorted({l.split("=")[0].strip() for l in ulines}):
            body.append(f"    uxraylib.MatrixRelease({name})")
    body.append("    ' --- matris -> skaler")
    for ulines, ux, _c in MATRIX_SCALARS:
        val = next(it).strip()
        for l in ulines:
            body.append("    " + l)
        body.append(f"    ASSERT Near({ux}, {val}) = 1")
        for name in sorted({l.split("=")[0].strip() for l in ulines}):
            body.append(f"    uxraylib.MatrixRelease({name})")
    body.append("    ' --- matris -> vektor")
    for ulines, ux, kind, _c in MATRIX_VECTORS:
        vals = next(it).split()
        for l in ulines:
            body.append("    " + l)
        body.extend(vec_asserts(ux, kind, vals))
        for name in sorted({l.split("=")[0].strip() for l in ulines}):
            body.append(f"    uxraylib.MatrixRelease({name})")

    header = '''INCLUDE "include/modules/uxraylib_math.uxmh"

' uxraylib raymath (S-052, raylib Models/3D dilimi 1) duman testi: pencere/GL baglami GEREKTIRMEZ.
' GENERATED by tools/library_tools/gen_uxraylib_math_test.py -- beklenen degerler raymath.h'yi DOGRUDAN cagiran bir C programindan
' gelir (sarmalayici degil, sarmalayicinin argüman siralamasi ve kayit/tutamac mekanigi sinanir).
FUNCTION Near(a AS F64, b AS F64) AS I32
    DIM d AS F64
    d = a - b
    IF d < 0.0 THEN d = 0.0 - d
    IF d < 0.0001 THEN RETURN 1
    RETURN 0
END FUNCTION

MAIN
    DIM a AS I32
    DIM b AS I32
    DIM c AS I32
    DIM q AS I32
    DIM p AS I32
    DIM v AS I32
    DIM u AS I32
    ASSERT uxraylib.MatrixLiveCount() = 0
'''
    tail = '''
    ' --- yardimci islevler: yuvalar, birden cok sonuc, cikis parametreli islevler
    uxraylib.Vector3OrthoNormalize(3, 0, 0, 1, 2, 0)
    ASSERT Near(uxraylib.ResGet(0, 0), 1.0) = 1
    ASSERT Near(uxraylib.ResGet(0, 1), 0.0) = 1
    ASSERT Near(uxraylib.ResGet(1, 0), 0.0) = 1
    ASSERT Near(uxraylib.ResGet(1, 1), 1.0) = 1
    uxraylib.VectorSlotSet(0, 0.0, 0.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(1, 1.0, 0.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(2, 4.0, 0.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(3, 1.0, 0.0, 0.0, 0.0)
    uxraylib.Vector3CubicHermiteSlots(0, 1, 2, 3, 0.5)
    ASSERT Near(uxraylib.ResX(), 2.0) = 1
    ASSERT Near(uxraylib.ResY(), 0.0) = 1
    uxraylib.VectorSlotSet(4, 1.0, 1.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(5, 0.0, 0.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(6, 4.0, 0.0, 0.0, 0.0)
    uxraylib.VectorSlotSet(7, 0.0, 4.0, 0.0, 0.0)
    uxraylib.Vector3BarycenterSlots(4, 5, 6, 7)
    ASSERT Near(uxraylib.ResX(), 0.5) = 1
    ASSERT Near(uxraylib.ResY(), 0.25) = 1
    ASSERT Near(uxraylib.ResZ(), 0.25) = 1
    DIM angle AS F64
    angle = uxraylib.QuaternionToAxisAngle(0, 0, 0.70710678, 0.70710678)
    ASSERT Near(angle, 1.5707963) = 1
    ASSERT Near(uxraylib.ResZ(), 1.0) = 1
    a = uxraylib.MatrixScale(2, 3, 4)
    b = uxraylib.MatrixTranslate(5, 6, 7)
    c = uxraylib.MatrixMultiply(a, b)
    uxraylib.MatrixDecompose(c)
    ASSERT Near(uxraylib.ResGet(0, 0), 5.0) = 1
    ASSERT Near(uxraylib.ResGet(0, 1), 6.0) = 1
    ASSERT Near(uxraylib.ResGet(0, 2), 7.0) = 1
    ASSERT Near(uxraylib.ResGet(2, 0), 2.0) = 1
    ASSERT Near(uxraylib.ResGet(2, 1), 3.0) = 1
    ASSERT Near(uxraylib.ResGet(2, 2), 4.0) = 1
    ASSERT Near(uxraylib.ResGet(1, 3), 1.0) = 1
    uxraylib.MatrixRelease(a)
    uxraylib.MatrixRelease(b)
    uxraylib.MatrixRelease(c)
    ' --- tutamac yasam dongusu ve hata bildirimi
    ASSERT uxraylib.MatrixLiveCount() = 0
    a = uxraylib.MatrixIdentity()
    ASSERT a <> 0
    ASSERT uxraylib.MatrixLiveCount() = 1
    b = uxraylib.MatrixCopy(a)
    ASSERT b <> a
    ASSERT uxraylib.MatrixSetElement(b, 12, 9.5) = 1
    ASSERT Near(uxraylib.MatrixElement(b, 12), 9.5) = 1
    ASSERT Near(uxraylib.MatrixElement(a, 12), 0.0) = 1
    ASSERT Near(uxraylib.MatrixAt(a, 3, 3), 1.0) = 1
    ASSERT Near(uxraylib.MatrixAt(b, 0, 3), 9.5) = 1
    uxraylib.MathClearError()
    ASSERT uxraylib.MathLastError() = 0
    ASSERT Near(uxraylib.MatrixElement(999, 0), 1.0) = 1
    ASSERT uxraylib.MathLastError() = 1
    uxraylib.MathClearError()
    uxraylib.MatrixRelease(a)
    uxraylib.MatrixRelease(b)
    uxraylib.MatrixRelease(b)
    ASSERT uxraylib.MatrixLiveCount() = 0
    PRINT "RAYMATH_PASS"
END MAIN
'''
    out_path = root / "tests/libraries/uxraylib/uxraylib_math_smoke.uxb"
    out_path.write_text(header + "\n".join(body) + "\n" + tail, encoding="utf-8")
    print(f"yazildi: {out_path} ({len(body)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
