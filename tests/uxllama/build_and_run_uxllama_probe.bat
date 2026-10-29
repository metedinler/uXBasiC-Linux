@echo off
setlocal
cd /d "%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxllama\build_uxllama_dll.bat
if errorlevel 1 exit /b 1
set "OUTDIR=uxb\dist\runtime_ext"
"%GCC%" -O2 -Iuxb\runtime_ext\uxllama -o "%OUTDIR%\uxllama_dll_probe.exe" "uxb\tests\uxllama\uxllama_dll_probe.c" -L"%OUTDIR%" -luxllama
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;%PATH%"
"%OUTDIR%\uxllama_dll_probe.exe" %*
endlocal
