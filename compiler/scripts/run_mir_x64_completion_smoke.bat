@echo off
setlocal
cd /d "%~dp0\..\..\.."

if not exist "uxb\dist" mkdir "uxb\dist"

call build_compiler_64.bat
if errorlevel 1 exit /b 1

set "UXB=uxb\bin\uxb.exe"
if not exist "%UXB%" set "UXB=uxb\build\uxb_main_64.exe"
if not exist "%UXB%" (
  echo ERROR: uXBasiC compiler executable not found.
  exit /b 2
)

for %%F in (array_index builtin_scalar field_synthetic control_select_for) do (
  echo === MIR x64 completion smoke: %%F ===
  "%UXB%" "uxb\tests\mir_x64_completion\mir_x64_%%F.bas" --codegen-source MIR --enable-mir-x64-experimental --mir-verify --emit-x64-nasm --emit-x64-nasm-out "uxb\dist\mir_x64_%%F.nasm" --x64-codegen-policy-json-out "uxb\dist\mir_x64_%%F.policy.json" --debug
  if errorlevel 1 (
    echo ERROR: MIR x64 completion smoke failed: %%F
    exit /b 1
  )
)

echo OK: MIR x64 completion smoke passed.
endlocal
