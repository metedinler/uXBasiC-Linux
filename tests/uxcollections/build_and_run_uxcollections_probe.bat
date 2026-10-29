@echo off
setlocal
cd /d "%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "OUTDIR=uxb\dist\runtime_ext"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxcollections\build_uxcollections_dll.bat
if errorlevel 1 exit /b 1
for /f "usebackq tokens=*" %%I in (`C:\msys64\ucrt64\bin\pkg-config.exe --cflags --libs glib-2.0`) do set "GLIBFLAGS=%%I"
"%GCC%" -O2 -Iuxb\runtime_ext\uxcollections -o "%OUTDIR%\uxcollections_probe.exe" "uxb\tests\uxcollections\uxcollections_dll_probe.c" -L"%OUTDIR%" -luxcollections %GLIBFLAGS%
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUTDIR%;%PATH%"
"%OUTDIR%\uxcollections_probe.exe"
endlocal
