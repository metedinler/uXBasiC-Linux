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
call uxb\runtime_ext\uxstats2\build_uxstats2_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxstats2 -o "%OUTDIR%\uxstats2_dll_probe.exe" "uxb\tests\uxstats2\uxstats2_dll_probe.c" -L"%OUTDIR%" -luxstats2 -lm
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxstats2_dll_probe.exe"
endlocal
