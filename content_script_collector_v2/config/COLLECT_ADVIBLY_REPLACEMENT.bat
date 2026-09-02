@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo Content Script Collector V2.1 - Advibly replacement only
echo ==========================================================
python collectors\github_collector.py --repo Advibly/skills
if errorlevel 1 goto FAIL
python database\build_indexes.py
if errorlevel 1 goto FAIL
python reports\build_report.py
if errorlevel 1 goto FAIL
echo.
echo SUCCESS - Advibly replacement collected and indexes rebuilt.
pause
exit /b 0
:FAIL
echo FAILED. Check logs\collector.log
pause
exit /b 1
