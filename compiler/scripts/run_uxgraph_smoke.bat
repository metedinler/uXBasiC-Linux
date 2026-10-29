@echo off
setlocal
cd /d "%~dp0..\..\.."

echo === Build and run uxgraph DLL probe ===
call uxb\tests\uxgraph\build_and_run_uxgraph_probe.bat
if errorlevel 1 exit /b 1

echo === Build uXBasiC compiler if possible ===
if exist build_compiler_64.bat (
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
)

if exist uxb\bin\uxb.exe (
  echo === uXBasic include smoke ===
  uxb\bin\uxb.exe uxb\tests\uxgraph\uxgraph_include_smoke.bas --execmem --interpreter-backend AST --debug
  if errorlevel 1 exit /b 1
) else (
  echo WARN: uXBasic compiler exe not found; DLL probe passed, include smoke skipped.
)

echo OK: uxgraph smoke complete.
endlocal
