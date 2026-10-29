@echo off
setlocal
cd /d "%~dp0\..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if not exist "%GCC%" (echo ERROR: gcc not found & exit /b 2)
call uxb\runtime_ext\uxonnx2\fetch_uxonnx2_deps.bat
if errorlevel 1 exit /b 1
call uxb\runtime_ext\uxonnx2\build_uxonnx2_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxonnx2 -o uxb\dist\runtime_ext\uxonnx2_probe.exe uxb\tests\uxonnx2\uxonnx2_dll_probe.c -Luxb\dist\runtime_ext -luxonnx2
if errorlevel 1 exit /b 1
set "PATH=%CD%\uxb\dist\runtime_ext;%CD%\uxb\dist\runtime_ext\deps\uxonnx2;%PATH%"
uxb\dist\runtime_ext\uxonnx2_probe.exe uxb\dist\runtime_ext\deps\uxonnx2 %*
endlocal
