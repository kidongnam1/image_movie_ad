@echo off
cd /d "%~dp0"
where python >nul 2>nul && (python quick_status.py) || (py -3 quick_status.py)
pause
