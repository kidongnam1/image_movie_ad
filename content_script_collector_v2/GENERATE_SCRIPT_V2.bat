@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.7 - 성과학습 + Creative Registry
echo ==========================================================
echo.

set "PRODUCT=%~1"
if not defined PRODUCT set /p PRODUCT=상품명 입력: 
if not defined PRODUCT goto FAIL

set /p MUST=반드시 강조할 특징 (예: 0.2초 측정, 손떨림 보정 / 선택): 
set /p FEATURES=추가 특징 (예: 800m 측정, 150g 초경량 / 선택): 
set /p PAIN=고객이 겪는 불편/Pain Point (선택): 
set /p TARGET=타깃 고객 (기본: 일반 소비자): 
set /p INTENSITY=광고 강도 1~5 (기본: 4): 
set /p PERF=이미 V2.6 공통형식으로 변환된 성과 파일 경로 (없으면 Enter): 

if not defined TARGET set "TARGET=일반 소비자"
if not defined INTENSITY set "INTENSITY=4"

echo.
echo [RUN] Script Generator V2.7 + Content DB + Performance Learning + Creative Registry
if defined PERF (
  python generator\script_generator_v2.py "%PRODUCT%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --performance-file "%PERF%" --require-db
) else (
  python generator\script_generator_v2.py "%PRODUCT%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --require-db
)
if errorlevel 1 goto FAIL

echo.
echo SUCCESS - Script Generator V2.7
echo 결과 폴더: outputs
echo A/B/C 광고명에는 결과의 CR-XXXXXXXXXXXX Creative ID를 넣으세요.
echo 플랫폼 원본 성과는 IMPORT_PLATFORM_PERFORMANCE_V27.bat 으로 가져오세요.
echo 성과 DB: database\ad_performance.sqlite
pause
exit /b 0

:FAIL
echo.
echo FAILED - database 또는 logs\app.log를 확인하세요.
pause
exit /b 1
