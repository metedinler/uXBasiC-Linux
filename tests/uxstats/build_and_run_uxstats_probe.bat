@echo off
setlocal
cd /d "%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "OUTDIR=uxb\dist\runtime_ext"
set "LIBDIR=uxb\dist\libraries\lib"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
call uxb\runtime_ext\uxstats\build_uxstats_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -std=c99 -Iuxb\runtime_ext\uxstats -o "%OUTDIR%\uxstats_dll_probe.exe" "uxb\tests\uxstats\uxstats_dll_probe.c" -L"%LIBDIR%" -luxstats -lm >"%OUTDIR%\uxstats_probe_build.log" 2>&1
set "PROBE_BUILD_RC=%ERRORLEVEL%"
if not "%PROBE_BUILD_RC%"=="0" (
  type "%OUTDIR%\uxstats_probe_build.log"
  echo ERROR: uxstats probe build failed.
  exit /b %PROBE_BUILD_RC%
)
set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxstats_dll_probe.exe"
endlocal
