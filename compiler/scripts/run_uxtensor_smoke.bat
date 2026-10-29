@echo off
setlocal
cd /d "%~dp0..\..\.."
call uxb\tests\uxtensor\build_and_run_uxtensor_probe.bat
if errorlevel 1 exit /b 1
call build_compiler_64.bat
if errorlevel 1 exit /b 1
if exist "uxb\bin\uxb.exe" (
  set "UXB=uxb\bin\uxb.exe"
) else (
  set "UXB=uxb\build\uxb_main_64.exe"
)
"%UXB%" uxb\tests\uxtensor\uxtensor_include_smoke.bas --debug
if errorlevel 1 exit /b 1
echo OK: uxtensor smoke passed.
endlocal
