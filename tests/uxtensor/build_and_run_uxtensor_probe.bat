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
call uxb\runtime_ext\uxtensor\build_uxtensor_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxtensor -o "%OUTDIR%\uxtensor_probe.exe" "uxb\tests\uxtensor\uxtensor_dll_probe.c" -L"%OUTDIR%" -luxtensor -lopenblas
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;%CD%\uxb\dist\runtime_ext\deps\uxtensor;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxtensor_probe.exe"
endlocal
