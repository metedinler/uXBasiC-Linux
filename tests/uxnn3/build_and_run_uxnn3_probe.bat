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
call uxb\runtime_ext\uxnn3\build_uxnn3_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxnn3 -o "%OUTDIR%\uxnn3_dll_probe.exe" "uxb\tests\uxnn3\uxnn3_dll_probe.c" -L"%OUTDIR%" -luxnn3 -lm
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxnn3_dll_probe.exe"
endlocal
