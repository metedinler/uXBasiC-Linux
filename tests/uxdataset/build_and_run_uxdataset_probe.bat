@echo off
setlocal
cd /d "%~dp0\..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set "OUTDIR=uxb\dist\runtime_ext"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxdataset\build_uxdataset_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -std=c99 -Iuxb\runtime_ext\uxdataset -o "%OUTDIR%\uxdataset_probe.exe" "uxb\tests\uxdataset\uxdataset_dll_probe.c" -L"%OUTDIR%" -luxdataset -lm
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxdataset_probe.exe"
endlocal
