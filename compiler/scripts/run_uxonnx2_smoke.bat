@echo off
setlocal
cd /d "%~dp0\..\..\.."
call uxb\tests\uxonnx2\build_and_run_uxonnx2_probe.bat %*
if errorlevel 1 exit /b 1
if exist build_compiler_64.bat (
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
  if exist uxb\bin\uxb.exe (
    uxb\bin\uxb.exe uxb\tests\uxonnx2\uxonnx2_include_smoke.bas --execmem --interpreter-backend AST --debug
  )
)
echo OK: uxonnx2 smoke finished.
endlocal
