@echo off
setlocal
cd /d "%~dp0..\..\.."
if "%~1"=="" (
  echo Usage: run_emit_wasm_backend.bat source.bas
  exit /b 2
)
if not exist uxb\bin\uxb.exe (
  call build_compiler_64.bat
)
python uxb\tools\uxb_js_transpiler_wasm_backend.py --source "%~1" --backend AST --emit-wasm
if errorlevel 1 exit /b %ERRORLEVEL%
echo.
echo JS/WASM backend report:
echo   uxb\dist\js_wasm\js_wasm_backend_report.md
endlocal
