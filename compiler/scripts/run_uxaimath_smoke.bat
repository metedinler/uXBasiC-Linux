@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo === UXAIMATH DLL probe ===
call uxb\tests\uxaimath\build_and_run_uxaimath_probe.bat
if errorlevel 1 exit /b 1

echo === UXAIMATH include smoke ===
call build_compiler_64.bat
if errorlevel 1 exit /b 1
set "UXB=uxb\bin\uxb.exe"
if not exist "%UXB%" set "UXB=uxb\build\uxb_main_64.exe"
if exist "%UXB%" (
  "%UXB%" uxb\tests\uxaimath\uxaimath_include_smoke.bas --execmem --interpreter-backend AST --debug
)
echo OK: uxaimath smoke completed.
endlocal
