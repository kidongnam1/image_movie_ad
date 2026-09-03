@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo V2.7 플랫폼 광고 성과 자동 가져오기
echo Meta / TikTok / Naver / Coupang / Generic
==========================================================
echo.
set /p FILE=플랫폼에서 내려받은 CSV/JSON/XLSX 파일 경로: 
if not defined FILE goto FAIL
set /p PLATFORM=플랫폼 auto/meta/tiktok/naver/coupang/generic (기본 auto): 
set /p PRODUCT=CR ID가 없는 파일의 기본 상품명 (선택): 
set /p CATEGORY=기본 카테고리 (선택): 
if not defined PLATFORM set "PLATFORM=auto"

python generator\platform_performance_adapter_v27.py "%FILE%" --platform %PLATFORM% --default-product "%PRODUCT%" --default-category "%CATEGORY%"
if errorlevel 1 goto FAIL

python generator\performance_dashboard_v27.py
if errorlevel 1 goto FAIL

echo.
echo SUCCESS - 플랫폼 성과를 공통 DB에 반영했습니다.
echo DB: database\ad_performance.sqlite
echo Dashboard: outputs\performance_dashboard_v27.html
echo 다음에는 OPEN_PERFORMANCE_DASHBOARD_V27.bat 을 실행하세요.
pause
exit /b 0

:FAIL
echo.
echo FAILED - 파일 헤더/상품명/CR ID 또는 logs를 확인하세요.
pause
exit /b 1
