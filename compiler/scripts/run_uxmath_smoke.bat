@echo off
setlocal
cd /d "%~dp0..\..\.."

echo === Build and run uxmath C probe ===
call uxb\tests\uxmath\build_and_run_uxmath_probe.bat
if errorlevel 1 exit /b 1

echo === Build compiler if available ===
if exist build_compiler_64.bat call build_compiler_64.bat

set "UXB=uxb\bin\uxb.exe"
if exist "%UXB%" (
  echo === Run uxmath include smoke through uXBasiC ===
  "%UXB%" uxb\tests\uxmath\uxmath_include_smoke.bas --execmem --interpreter-backend AST --debug
) else (
  echo WARN: uXBasiC compiler executable not found, DLL probe already passed.
)
endlocal
