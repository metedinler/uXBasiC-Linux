@echo off
setlocal
cd /d "%~dp0..\..\.."

if not exist "uxb\dist" mkdir "uxb\dist"

call uxb\tests\uxstats\build_and_run_uxstats_probe.bat
if errorlevel 1 exit /b 1

if exist build_compiler_64.bat (
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
)

set "UXB=uxb\bin\uxb.exe"
if not exist "%UXB%" set "UXB=uxb\build\uxb_main_64.exe"
if not exist "%UXB%" (
  echo WARN: uXBasic compiler executable not found. DLL C probe passed; uXBasic include smoke skipped.
  exit /b 0
)

set "PATH=%CD%\uxb\dist\runtime_ext;C:\msys64\ucrt64\bin;%PATH%"

"%UXB%" uxb\tests\uxstats\uxstats_include_smoke.bas --execmem --interpreter-backend AST --debug
if errorlevel 1 exit /b 1

"%UXB%" uxb\tests\uxstats\uxstats_regression_smoke.bas --execmem --interpreter-backend AST --debug
if errorlevel 1 exit /b 1

echo OK: uxstats smoke passed.
endlocal
