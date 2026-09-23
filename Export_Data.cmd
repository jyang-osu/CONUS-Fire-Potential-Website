@echo off
cd /d "%~dp0"
runtime\python.exe -B export_site.py
if errorlevel 1 exit /b 1
runtime\python.exe -B verify_site.py
if errorlevel 1 exit /b 1
runtime\python.exe -B package_site.py
pause
