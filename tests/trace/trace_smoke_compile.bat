@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."

echo [1/3] build compiler
call compiler\scripts\build_uxb_main_64.bat || exit /b 1

echo [2/3] run trace smoke
set "UXB_EXE=build\uxb_main_64.exe"
if not exist "%UXB_EXE%" set "UXB_EXE=bin\uxb.exe"
if not exist "%UXB_EXE%" (
	echo ERROR: compiler executable not found
	exit /b 1
)

"%UXB_EXE%" tests\basicCodeTests\42_uxb_native_console_codegen_smoke.bas --hook-trace --session-live-json-out dist\session.live.json --layer-timing-json-out dist\layer_timing.json --debug || exit /b 1

echo [3/3] outputs
if exist dist\session.live.json echo OK: dist\session.live.json
if exist dist\layer_timing.json echo OK: dist\layer_timing.json
endlocal
