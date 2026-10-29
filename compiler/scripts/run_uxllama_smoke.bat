@echo off
setlocal
cd /d "%~dp0..\..\.."
call uxb\tests\uxllama\build_and_run_uxllama_probe.bat %*
if errorlevel 1 exit /b 1
if exist build_compiler_64.bat (
  call build_compiler_64.bat
)
if exist uxb\bin\uxb.exe (
  uxb\bin\uxb.exe uxb\tests\uxllama\uxllama_include_smoke.bas --debug
)
endlocal
