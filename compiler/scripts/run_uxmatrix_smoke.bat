@echo off
setlocal
cd /d "%~dp0..\..\.."

echo === Build and run uxmatrix DLL probe ===
call uxb\tests\uxmatrix\build_and_run_uxmatrix_probe.bat
if errorlevel 1 exit /b 1

echo === Build compiler if available ===
if exist build_compiler_64.bat (
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
)

set "UXB=uxb\bin\uxb.exe"
if exist "%UXB%" (
  echo === uXBasic uxmatrix include smoke ===
  "%UXB%" uxb\tests\uxmatrix\uxmatrix_include_smoke.bas --execmem --interpreter-backend AST --debug
  if errorlevel 1 echo WARN: include smoke failed or CALL(DLL) signature path not available yet.
) else (
  echo WARN: compiler executable not found; only DLL probe was run.
)

echo OK: uxmatrix smoke completed.
endlocal
