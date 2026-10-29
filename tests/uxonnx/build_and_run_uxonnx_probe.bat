@echo off
setlocal
cd /d "%~dp0\..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set "DEP=uxb\dist\runtime_ext\deps\uxonnx"
set "OUT=uxb\dist\runtime_ext"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxonnx\build_uxonnx_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -I"%DEP%\include" -Iuxb\runtime_ext\uxonnx -o "%OUT%\uxonnx_probe.exe" "uxb\tests\uxonnx\uxonnx_dll_probe.c" -L"%OUT%" -luxonnx
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUT%;%CD%\%DEP%;%PATH%"
"%OUT%\uxonnx_probe.exe" "%DEP%" %*
endlocal
