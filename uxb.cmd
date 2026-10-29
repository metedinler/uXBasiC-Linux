@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "UXB_CLI_EXE=%~dp0bin\uxb.exe"
if not defined UXB_EXE if exist "%~dp0build\compilers\codex33\uxb.exe" set "UXB_CLI_EXE=%~dp0build\compilers\codex33\uxb.exe"
if "%UXB_CLI_EXE%"=="%~dp0build\compilers\codex33\uxb.exe" if not defined UXB_NATIVE_RUNTIME_DIR if exist "%~dp0build\runtime\codex7\uxb_runtime.dll" set "UXB_NATIVE_RUNTIME_DIR=%~dp0build\runtime\codex7"
if defined UXB_EXE set "UXB_CLI_EXE=%UXB_EXE%"
if not exist "%UXB_CLI_EXE%" (
  echo ERROR: Derleyici bulunamadi: "%UXB_CLI_EXE%" 1>&2
  exit /b 2
)
if "%~1"=="" goto shell
"%UXB_CLI_EXE%" %*
exit /b %ERRORLEVEL%

:shell
set "PATH=%~dp0;%~dp0bin;%PATH%"
title uXBasic CLI
prompt uXBasic $P$G
pushd "%~dp0"
echo uXBasic komut penceresi. Ornek: uxb.cmd help
echo Derleyici: "%UXB_CLI_EXE%"
echo Komut dosyasi: uxb.cmd @tests\options\run.uxcli
echo Cikis: exit
"%ComSpec%" /d /k
set "UXB_CLI_RC=%ERRORLEVEL%"
popd
exit /b %UXB_CLI_RC%
