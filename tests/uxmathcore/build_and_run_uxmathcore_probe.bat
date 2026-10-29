@echo off
setlocal
cd /d "%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set "OUTDIR=uxb\dist\runtime_ext"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxmathcore\build_uxmathcore_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxmathcore -o "%OUTDIR%\uxmathcore_probe.exe" "uxb\tests\uxmathcore\uxmathcore_dll_probe.c" -L"%OUTDIR%" -luxmathcore -lm
if errorlevel 1 (
  echo ERROR: uxmathcore probe build failed.
  exit /b 1
)
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxmathcore_probe.exe"
endlocal
