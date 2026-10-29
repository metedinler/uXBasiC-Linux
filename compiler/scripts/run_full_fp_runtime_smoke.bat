@echo off
setlocal
cd /d "%~dp0..\..\.."

echo === Build all external FP runtimes ===
call uxb\runtime_ext\build_fp_runtime_all.bat
if errorlevel 1 exit /b 1

echo === Run BIGF/BIGD/BALL C probe ===
call uxb\tests\fp_runtime\build_and_run_bigfp_runtime_probe.bat
if errorlevel 1 exit /b 1

echo === Build compiler ===
call build_compiler_64.bat
if errorlevel 1 exit /b 1

echo === uXBasiC policy JSON ===
uxb\bin\uxb.exe uxb\tests\fp_ext\bigf_runtime_policy.bas --enable-extfp-runtime --extfp-runtime-dir uxb\dist\runtime_ext --extfp-policy-json-out uxb\dist\extfp_policy_bigf.json --extfp-diagnostics --debug
if errorlevel 1 exit /b 1

python -c "import json,pathlib; p=pathlib.Path('uxb/dist/extfp_policy_bigf.json'); d=json.loads(p.read_text(encoding='utf-8')); print('POLICY_JSON_OK', d.get('schema_version'))"
if errorlevel 1 exit /b 1

echo OK: full FP runtime smoke passed.
endlocal
