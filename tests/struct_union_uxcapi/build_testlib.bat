@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..") do set "UXB_ROOT=%%~fI"
if defined UXB_MSYS2_ROOT (set "MSYS2_ROOT=%UXB_MSYS2_ROOT%") else set "MSYS2_ROOT=C:\msys64"
if defined UXB_GCC (
  set "GCC=%UXB_GCC%"
) else if exist "%MSYS2_ROOT%\ucrt64\bin\x86_64-w64-mingw32-gcc.exe" (
  set "GCC=%MSYS2_ROOT%\ucrt64\bin\x86_64-w64-mingw32-gcc.exe"
) else (
  set "GCC=%MSYS2_ROOT%\ucrt64\bin\gcc.exe"
)
if not exist "%GCC%" (
  echo ERROR: GCC bulunamadi: %GCC%
  exit /b 2
)
for %%I in ("%GCC%") do set "GCC_BIN=%%~dpI"
set "PATH=%GCC_BIN%;%PATH%"
if not exist "%UXB_ROOT%\bin" mkdir "%UXB_ROOT%\bin"
"%GCC%" -std=c11 -O2 -Wall -Wextra -Werror -shared -static-libgcc ^
  -o "%UXB_ROOT%\bin\uxcabi_aggregate_test.dll" ^
  "%~dp0uxcabi_aggregate_testlib.c"
if errorlevel 1 exit /b 1
echo OK: %UXB_ROOT%\bin\uxcabi_aggregate_test.dll
exit /b 0
