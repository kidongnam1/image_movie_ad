@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo V2.7 과거 experiment_plan / script JSON Creative Registry 등록
echo ==========================================================
echo.
set /p PLAN=experiment_plan.json 또는 script JSON 경로: 
if not defined PLAN goto FAIL
python generator\performance_registry_v27.py "%PLAN%" --db database\ad_performance.sqlite
if errorlevel 1 goto FAIL
echo.
echo SUCCESS - Creative Registry 등록 완료
pause
exit /b 0
:FAIL
echo.
echo FAILED - JSON 구조 또는 파일 경로를 확인하세요.
pause
exit /b 1
