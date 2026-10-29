@echo off
setlocal
where pwsh.exe >nul 2>nul
if %ERRORLEVEL%==0 (
  pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0package_uxwasm_distribution.ps1" -Root "%~dp0.." %*
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0package_uxwasm_distribution.ps1" -Root "%~dp0.." %*
)
exit /b %ERRORLEVEL%
