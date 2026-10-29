@echo off
setlocal
cd /d "%~dp0..\..\.."

if not exist uxb\dist mkdir uxb\dist
if not exist uxb\dist\extfp_audit mkdir uxb\dist\extfp_audit

call uxb\runtime_ext\build_fp_runtime_all.bat
if errorlevel 1 (
  echo WARN: FP runtime build failed. Codegen emit can still be tested, strict link/run may fail.
)

call uxb\compiler\scripts\build_uxb_main_64.bat
if errorlevel 1 exit /b 1

set UXB=uxb\bin\uxb.exe
if not exist "%UXB%" set UXB=uxb\build\uxb_main_64.exe
if not exist "%UXB%" (
  echo ERROR: compiler executable not found.
  exit /b 1
)

"%UXB%" uxb\tests\fp_ext\f80_local_global_assignment_binary_print.bas --enable-extfp-runtime --extfp-runtime-dir uxb\dist\runtime_ext --emit-x64-nasm --emit-x64-nasm-out uxb\dist\f80_extfp_local_global.nasm --debug
if errorlevel 1 exit /b 1
python uxb\tools\uxb_extfp_codegen_audit.py --asm uxb\dist\f80_extfp_local_global.nasm --family f80 --json-out uxb\dist\extfp_audit\f80_local_global.json
if errorlevel 1 exit /b 1

"%UXB%" uxb\tests\fp_ext\f80_array_field_assignment_binary_print.bas --enable-extfp-runtime --extfp-runtime-dir uxb\dist\runtime_ext --emit-x64-nasm --emit-x64-nasm-out uxb\dist\f80_extfp_array_field.nasm --debug
if errorlevel 1 exit /b 1
python uxb\tools\uxb_extfp_codegen_audit.py --asm uxb\dist\f80_extfp_array_field.nasm --family f80 --json-out uxb\dist\extfp_audit\f80_array_field.json
if errorlevel 1 exit /b 1

"%UXB%" uxb\tests\fp_ext\f128_local_global_assignment_binary_print.bas --enable-extfp-runtime --extfp-runtime-dir uxb\dist\runtime_ext --emit-x64-nasm --emit-x64-nasm-out uxb\dist\f128_extfp_local_global.nasm --debug
if errorlevel 1 exit /b 1
python uxb\tools\uxb_extfp_codegen_audit.py --asm uxb\dist\f128_extfp_local_global.nasm --family f128 --json-out uxb\dist\extfp_audit\f128_local_global.json
if errorlevel 1 exit /b 1

"%UXB%" uxb\tests\fp_ext\f128_array_field_assignment_binary_print.bas --enable-extfp-runtime --extfp-runtime-dir uxb\dist\runtime_ext --emit-x64-nasm --emit-x64-nasm-out uxb\dist\f128_extfp_array_field.nasm --debug
if errorlevel 1 exit /b 1
python uxb\tools\uxb_extfp_codegen_audit.py --asm uxb\dist\f128_extfp_array_field.nasm --family f128 --json-out uxb\dist\extfp_audit\f128_array_field.json
if errorlevel 1 exit /b 1

echo PASS: F80/F128 external FP codegen smoke passed.
endlocal
