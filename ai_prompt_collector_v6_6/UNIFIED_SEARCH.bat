@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
set /p Q=Search prompt + social creative tools: 
%PY% search_all_assets.py "%Q%" --limit 15
pause
