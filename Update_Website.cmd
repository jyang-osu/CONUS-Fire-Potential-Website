@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Update_Website.ps1"
set "update_exit=%errorlevel%"
pause
exit /b %update_exit%
