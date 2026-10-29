@echo off
setlocal
cd /d "%~dp0\..\..\.."

echo === Fetch ONNX Runtime deps if needed ===
if not exist "uxb\dist\runtime_ext\deps\uxonnx\onnxruntime.dll" (
  call uxb\runtime_ext\uxonnx\fetch_uxonnx_deps.bat
  if errorlevel 1 exit /b 1
)

echo === Build and run uxonnx C probe ===
call uxb\tests\uxonnx\build_and_run_uxonnx_probe.bat %*
if errorlevel 1 exit /b 1

echo === Build compiler ===
call build_compiler_64.bat
if errorlevel 1 exit /b 1

echo === uXBasic include smoke ===
set "UXB=uxb\bin\uxb.exe"
if exist "%UXB%" (
  "%UXB%" uxb\tests\uxonnx\uxonnx_include_smoke.bas --execmem --interpreter-backend AST --debug
)

echo OK: uxonnx smoke completed.
endlocal
