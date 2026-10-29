@echo off
setlocal
cd /d "%~dp0..\..\.."

echo === Build and run uxmathcore DLL probe ===
call uxb\tests\uxmathcore\build_and_run_uxmathcore_probe.bat
if errorlevel 1 exit /b 1

echo === Build compiler if available ===
if exist build_compiler_64.bat (
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
) else (
  echo WARN: build_compiler_64.bat not found. Skipping uXBasic include smoke.
  exit /b 0
)

set "UXB=uxb\bin\uxb.exe"
if not exist "%UXB%" set "UXB=uxb\build\uxb_main_64.exe"
if not exist "%UXB%" (
  echo WARN: compiler exe not found. DLL probe passed, include smoke skipped.
  exit /b 0
)

"%UXB%" uxb\tests\uxmathcore\uxmathcore_include_smoke.bas --execmem --interpreter-backend AST --debug
if errorlevel 1 exit /b 1

echo OK: uxmathcore smoke passed.
endlocal
