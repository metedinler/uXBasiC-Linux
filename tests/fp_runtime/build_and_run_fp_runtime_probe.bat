@echo off
setlocal
cd /d "%~dp0..\..\.."

set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "OUTDIR=uxb\dist\runtime_ext"

if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)

set "PATH=C:\msys64\ucrt64\bin;%PATH%"

call uxb\runtime_ext\build_fp_runtime_all.bat
if errorlevel 1 exit /b 1

"%GCC%" -O2 ^
  -Iuxb\runtime_ext\fp128 ^
  -o "%OUTDIR%\fp_runtime_probe.exe" ^
  "uxb\tests\fp_runtime\fp_runtime_probe.c" ^
  -L"%OUTDIR%" -luxb_fp80 -luxb_fp128 -lquadmath

if errorlevel 1 (
  echo ERROR: probe build failed.
  exit /b 1
)

set "PATH=%CD%\%OUTDIR%;%PATH%"
"%OUTDIR%\fp_runtime_probe.exe"
endlocal
