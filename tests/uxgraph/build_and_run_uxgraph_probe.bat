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

call uxb\runtime_ext\uxgraph\build_uxgraph_dll.bat
if errorlevel 1 (
  echo INFO: igraph is unavailable; using the complete built-in graph algorithms.
  call uxb\runtime_ext\uxgraph\build_uxgraph_fallback_dll.bat
  if errorlevel 1 exit /b 1
)

"%GCC%" -O2 -Iuxb\runtime_ext\uxgraph -o "%OUTDIR%\uxgraph_dll_probe.exe" "uxb\tests\uxgraph\uxgraph_dll_probe.c" -L"%OUTDIR%" -luxgraph
if errorlevel 1 (
  echo ERROR: uxgraph probe build failed.
  exit /b 1
)

set "PATH=%CD%\%OUTDIR%;C:\msys64\ucrt64\bin;%PATH%"
"%OUTDIR%\uxgraph_dll_probe.exe"
endlocal
