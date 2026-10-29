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
call uxb\runtime_ext\bigfp\build_bigfp_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\bigfp -o "%OUTDIR%\bigfp_runtime_probe.exe" "uxb\tests\fp_runtime\bigfp_runtime_probe.c" -L"%OUTDIR%" -luxb_bigfp -lmpfr -lgmp
if errorlevel 1 (
  echo ERROR: bigfp probe build failed.
  exit /b 1
)
set "PATH=%CD%\%OUTDIR%;%PATH%"
"%OUTDIR%\bigfp_runtime_probe.exe"
endlocal
