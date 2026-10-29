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
call uxb\runtime_ext\uxmatrix\build_uxmatrix_dll.bat
if errorlevel 1 (
  echo WARN: OpenBLAS build failed. Trying fallback.
  call uxb\runtime_ext\uxmatrix\build_uxmatrix_fallback_dll.bat
  if errorlevel 1 exit /b 1
)
"%GCC%" -O2 -Iuxb\runtime_ext\uxmatrix -o "%OUTDIR%\uxmatrix_probe.exe" "uxb\tests\uxmatrix\uxmatrix_dll_probe.c" -L"%OUTDIR%" -luxmatrix
if errorlevel 1 (
  echo ERROR: uxmatrix probe build failed.
  exit /b 1
)
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxmatrix_probe.exe"
endlocal
