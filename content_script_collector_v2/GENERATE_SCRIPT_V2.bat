@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.6 - 성과학습 광고 대본 생성
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
set /p PERF=성과 파일 CSV/JSON/XLSX 경로 (없으면 Enter): 

if not defined TARGET set "TARGET=일반 소비자"
if not defined INTENSITY set "INTENSITY=4"

echo.
echo [DB CHECK] Script Generator V2.6 + Content DB + Performance Learning 실행...
if defined PERF (
  python generator\script_generator_v2.py "%PRODUCT%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --performance-file "%PERF%" --require-db
) else (
  python generator\script_generator_v2.py "%PRODUCT%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --require-db
)

if errorlevel 1 goto FAIL

echo.
echo SUCCESS - Script Generator V2.6
echo 결과 폴더: outputs
echo JSON / Markdown에서 TOP3 Hook, 성과보정, A/B/C 실험후보, 15/30/45초 대본을 확인하세요.
echo 성과 DB: database\ad_performance.sqlite
pause
exit /b 0

:FAIL
echo.
echo FAILED - database 또는 logs\app.log를 확인하세요.
pause
exit /b 1
