@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-aegis.ps1"
set "AEGIS_EXIT=%ERRORLEVEL%"
echo.
if not "%AEGIS_EXIT%"=="0" echo Setup failed. Review the error above.
pause
exit /b %AEGIS_EXIT%

