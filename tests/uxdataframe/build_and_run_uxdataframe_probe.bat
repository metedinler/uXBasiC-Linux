@echo off
setlocal
cd /d "%~dp0\..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "OUT=uxb\dist\runtime_ext"
set "DEP=%OUT%\deps\uxdataframe"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if not exist "%GCC%" (
  echo ERROR: MSYS2 UCRT64 gcc not found.
  exit /b 2
)
call uxb\runtime_ext\uxdataframe\build_uxdataframe_dll.bat
if errorlevel 1 exit /b 1
"%GCC%" -O2 -Iuxb\runtime_ext\uxdataframe -o "%OUT%\uxdataframe_probe.exe" "uxb\tests\uxdataframe\uxdataframe_dll_probe.c" -L"%OUT%" -luxdataframe
if errorlevel 1 exit /b 1
set "PATH=%CD%\%OUT%;%CD%\%DEP%\bin;%PATH%"
"%OUT%\uxdataframe_probe.exe"
endlocal
