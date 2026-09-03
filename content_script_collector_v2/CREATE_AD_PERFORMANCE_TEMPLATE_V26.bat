@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

python generator\ad_performance_learning.py template --out ad_performance_template.csv
if errorlevel 1 goto FAIL

echo.
echo TEMPLATE CREATED: ad_performance_template.csv
pause
exit /b 0

:FAIL
echo.
echo FAILED
pause
exit /b 1
