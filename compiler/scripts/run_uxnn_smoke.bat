@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo === uxnn DLL probe ===
call uxb\tests\uxnn\build_and_run_uxnn_probe.bat
if errorlevel 1 exit /b 1
if exist build_compiler_64.bat (
  echo === uXBasic compiler build ===
  call build_compiler_64.bat
  if errorlevel 1 exit /b 1
  if exist uxb\bin\uxb.exe (
    echo === uxnn include smoke ===
    uxb\bin\uxb.exe uxb\tests\uxnn\uxnn_include_smoke.bas --debug
  )
)
echo OK: uxnn smoke finished.
endlocal
