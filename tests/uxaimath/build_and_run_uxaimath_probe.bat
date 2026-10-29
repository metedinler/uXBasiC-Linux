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
if exist "C:\msys64\ucrt64\include\cblas.h" (
  call uxb\runtime_ext\uxaimath\build_uxaimath_dll.bat
) else (
  echo INFO: cblas.h is unavailable; using the built-in AI math algorithms.
  call uxb\runtime_ext\uxaimath\build_uxaimath_fallback_dll.bat
)
if errorlevel 1 call uxb\runtime_ext\uxaimath\build_uxaimath_fallback_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxaimath -o "%OUTDIR%\uxaimath_dll_probe.exe" "uxb\tests\uxaimath\uxaimath_dll_probe.c" -L"%OUTDIR%" -luxaimath
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;%CD%\%OUTDIR%\deps\uxaimath;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxaimath_dll_probe.exe"
endlocal
