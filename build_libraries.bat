@echo off
setlocal
call "%~dp0compiler\scripts\build_libraries.bat" %*
exit /b %ERRORLEVEL%
