@echo off
setlocal
cd /d "%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxnn2\build_uxnn2_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxnn2 -o uxb\dist\runtime_ext\uxnn2_dll_probe.exe uxb\tests\uxnn2\uxnn2_dll_probe.c -Luxb\dist\runtime_ext -luxnn2 -lm
if errorlevel 1 exit /b 1
set "PATH=%CD%\uxb\dist\runtime_ext;C:\msys64\ucrt64\bin;%PATH%"
uxb\dist\runtime_ext\uxnn2_dll_probe.exe
endlocal
