@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo Content Script Collector V1
echo ==========================================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found.
  pause
  exit /b 2
)
python -m pip install -r requirements.txt
if errorlevel 1 goto FAIL
python collectors\github_collector.py
if errorlevel 1 goto FAIL
python database\build_indexes.py
if errorlevel 1 goto FAIL
python reports\build_report.py
if errorlevel 1 goto FAIL
start "" reports\collection_report.html
echo.
echo DONE.
pause
exit /b 0
:FAIL
echo FAILED. Check logs\collector.log
pause
exit /b 1
