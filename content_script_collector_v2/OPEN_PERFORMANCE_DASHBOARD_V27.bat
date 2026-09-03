@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo V2.7 광고 성과 대시보드 생성 / 열기
echo ==========================================================
echo.
python generator\performance_dashboard_v27.py
if errorlevel 1 goto FAIL
start "" "%CD%\outputs\performance_dashboard_v27.html"
echo Dashboard opened: outputs\performance_dashboard_v27.html
exit /b 0
:FAIL
echo FAILED - database\ad_performance.sqlite 를 확인하세요.
pause
exit /b 1
