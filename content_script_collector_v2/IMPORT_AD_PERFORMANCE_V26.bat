@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo V2.6 광고 성과 데이터 가져오기
echo ==========================================================
echo.
set /p PERF=성과 파일 CSV/JSON/XLSX 경로 입력: 
if not defined PERF goto FAIL

python generator\ad_performance_learning.py import "%PERF%" --db database\ad_performance.sqlite
if errorlevel 1 goto FAIL

echo.
echo SUCCESS - 성과 데이터가 database\ad_performance.sqlite 에 반영되었습니다.
pause
exit /b 0

:FAIL
echo.
echo FAILED - 파일 경로/형식 또는 logs를 확인하세요.
pause
exit /b 1
