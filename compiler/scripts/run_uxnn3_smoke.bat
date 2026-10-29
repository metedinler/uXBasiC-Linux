@echo off
setlocal
cd /d "%~dp0..\..\.."
echo === uxnn3 DLL probe ===
call uxb\tests\uxnn3\build_and_run_uxnn3_probe.bat
if errorlevel 1 exit /b 1
echo === uxnn3 uXBasic include smoke ===
if exist build_compiler_64.bat call build_compiler_64.bat
if exist uxb\bin\uxb.exe (
  uxb\bin\uxb.exe uxb\tests\uxnn3\uxnn3_include_smoke.bas --execmem --interpreter-backend AST --debug
) else (
  echo WARN: compiler executable not found; DLL probe passed.
)
endlocal
