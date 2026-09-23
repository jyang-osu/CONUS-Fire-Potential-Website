@echo off
cd /d "%~dp0"
echo Open http://127.0.0.1:8766/site/
runtime\python.exe -B -m http.server 8766 --bind 127.0.0.1 --directory .
pause

