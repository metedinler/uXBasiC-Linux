@echo off
setlocal
cd /d "%~dp0..\..\.."

if not exist "uxb\dist" mkdir "uxb\dist"

echo === Build compiler ===
call uxb\compiler\scripts\build_uxb_main_64.bat
if errorlevel 1 (
  echo ERROR: compiler build failed.
  exit /b 1
)

set "EXE=uxb\bin\uxb.exe"
if not exist "%EXE%" set "EXE=uxb\build\uxb_main_64.exe"
if not exist "%EXE%" (
  echo ERROR: compiler executable not found.
  exit /b 1
)

echo === MIR x64 Prompt-3 smoke 1: DIM/arithmetic/PRINT ===
"%EXE%" uxb\tests\mir_x64_prompt3\mir_x64_dim_arith_print.bas --codegen-source MIR --enable-mir-x64-experimental --mir-verify --emit-x64-nasm --emit-x64-nasm-out uxb\dist\mir_x64_dim_arith_print.nasm --x64-codegen-policy-json-out uxb\dist\mir_x64_dim_arith_print.policy.json --debug
if errorlevel 1 exit /b 1

echo === MIR x64 Prompt-3 smoke 2: DO/IF/logical lowering ===
"%EXE%" uxb\tests\mir_x64_prompt3\mir_x64_if_loop_logic.bas --codegen-source MIR --enable-mir-x64-experimental --mir-verify --emit-x64-nasm --emit-x64-nasm-out uxb\dist\mir_x64_if_loop_logic.nasm --x64-codegen-policy-json-out uxb\dist\mir_x64_if_loop_logic.policy.json --debug
if errorlevel 1 exit /b 1

echo === MIR x64 Prompt-3 smoke 3: FOR/NEXT lowering ===
"%EXE%" uxb\tests\mir_x64_prompt3\mir_x64_for_next_logic.bas --codegen-source MIR --enable-mir-x64-experimental --mir-verify --emit-x64-nasm --emit-x64-nasm-out uxb\dist\mir_x64_for_next_logic.nasm --x64-codegen-policy-json-out uxb\dist\mir_x64_for_next_logic.policy.json --debug
if errorlevel 1 exit /b 1

python - <<PY
import json, pathlib, sys
for name in [
    "mir_x64_dim_arith_print",
    "mir_x64_if_loop_logic",
    "mir_x64_for_next_logic",
]:
    p = pathlib.Path("uxb/dist") / f"{name}.policy.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    pol = d.get("codegen_policy", {})
    if pol.get("policy") != "MIR_X64_EXPERIMENTAL" or pol.get("actual_emitter") != "MIR_X64":
        raise SystemExit(f"bad policy for {name}: {pol}")
print("POLICY_JSON_OK")
PY
if errorlevel 1 exit /b 1

echo OK: MIR x64 Prompt-3 smoke tests passed.
endlocal
