@echo off
setlocal
cd /d "%~dp0\..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set "OUTDIR=uxb\dist\runtime_ext"
if not exist "%GCC%" exit /b 2
if exist "C:\msys64\ucrt64\include\cblas.h" (
  call uxb\runtime_ext\uxnn\build_uxnn_dll.bat
) else (
  echo INFO: cblas.h is unavailable; using the built-in neural network algorithms.
  call uxb\runtime_ext\uxnn\build_uxnn_fallback_dll.bat
)
if errorlevel 1 call uxb\runtime_ext\uxnn\build_uxnn_fallback_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxnn -o "%OUTDIR%\uxnn_dll_probe.exe" "uxb\tests\uxnn\uxnn_dll_probe.c" -L"%OUTDIR%" -luxnn -lm
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxnn_dll_probe.exe"
endlocal
