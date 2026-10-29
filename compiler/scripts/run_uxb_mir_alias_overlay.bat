@echo off
setlocal
cd /d "%~dp0..\..\.."
if "%~1"=="" (
  echo Usage: run_uxb_mir_alias_overlay.bat source.bas
  exit /b 2
)
if not exist uxb\bin\uxb.exe (
  call build_compiler_64.bat
)
if not exist uxb\_work\alias mkdir uxb\_work\alias
set "TMP=uxb\_work\alias\%~n1.alias.bas"
python uxb\tools\uxb_alias_overlay_preprocessor.py --source "%~1" --out "%TMP%"
if errorlevel 1 exit /b %ERRORLEVEL%
uxb\bin\uxb.exe "%TMP%" --execmem --interpreter-backend MIR --mir-verify --console-mode direct
exit /b %ERRORLEVEL%
