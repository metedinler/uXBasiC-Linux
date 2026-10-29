@echo off
setlocal
cd /d "%~dp0..\..\.."
call uxb\tests\uxnn2\build_and_run_uxnn2_probe.bat
if errorlevel 1 exit /b 1
if exist build_compiler_64.bat call build_compiler_64.bat
if exist uxb\bin\uxb.exe (
  uxb\bin\uxb.exe uxb\tests\uxnn2\uxnn2_include_smoke.bas --execmem --interpreter-backend AST --debug
)
echo OK: uxnn2 smoke completed.
endlocal
