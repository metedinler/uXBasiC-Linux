@echo off
setlocal
cd /d "%~dp0"
if "%UXB_FORCE_REBUILD%"=="" set "UXB_FORCE_REBUILD=0"
if "%UXB_FORCE_REBUILD%"=="0" (
	if exist "bin\uxb.exe" (
		echo INFO: uxb_main_wrapper_64.exe already exists. Skipping rebuild. Set UXB_FORCE_REBUILD=1 to force.
		exit /b 0
	)
)
call compiler\scripts\build_uxb_main_64.bat
exit /b %ERRORLEVEL%
