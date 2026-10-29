@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo === Build/run uxdataset DLL probe ===
call uxb\tests\uxdataset\build_and_run_uxdataset_probe.bat
if errorlevel 1 exit /b 1

echo === Build compiler ===
call build_compiler_64.bat
if errorlevel 1 exit /b 1

echo === uXBasic include smoke ===
set "UXB=uxb\bin\uxb.exe"
if not exist "%UXB%" set "UXB=uxb\build\uxb_main_64.exe"
"%UXB%" uxb\tests\uxdataset\uxdataset_include_smoke.bas --execmem --interpreter-backend AST --debug
endlocal
