@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Creative Package - V2.7 성과학습 + Creative Registry 연동
echo ==========================================================
echo.

set /p PRODUCT=상품명 입력: 
if "%PRODUCT%"=="" goto FAIL

set /p DESCRIPTION=상품 설명 입력 (선택): 
set /p MUST=반드시 강조할 특징 (선택): 
set /p FEATURES=추가 특징 (선택): 
set /p PAIN=고객 Pain Point (선택): 
set /p TARGET=타깃 고객 입력 (기본: 일반 소비자): 
set /p INTENSITY=광고 강도 1~5 (기본: 4): 
set /p DURATION=광고 길이 15/30/45/60 (기본: 30): 
set /p PERF=이미 공통형식으로 변환된 성과 파일 경로 (없으면 Enter): 

if "%TARGET%"=="" set TARGET=일반 소비자
if "%INTENSITY%"=="" set INTENSITY=4
if "%DURATION%"=="" set DURATION=30

if defined PERF (
  python generator\creative_package_v26.py "%PRODUCT%" --description "%DESCRIPTION%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --duration %DURATION% --performance-file "%PERF%" --require-db
) else (
  python generator\creative_package_v26.py "%PRODUCT%" --description "%DESCRIPTION%" --must-emphasize "%MUST%" --features "%FEATURES%" --pain-point "%PAIN%" --target "%TARGET%" --intensity %INTENSITY% --duration %DURATION% --require-db
)
if errorlevel 1 goto FAIL

echo.
echo CREATIVE PACKAGE PASS - V2.7 Registry Enabled
echo 결과 폴더: outputs_creative
echo 광고명에 experiment_plan.json의 CR-... ID를 포함하세요.
echo 플랫폼 원본 성과는 IMPORT_PLATFORM_PERFORMANCE_V27.bat 으로 가져오세요.
pause
exit /b 0

:FAIL
echo.
echo CREATIVE PACKAGE FAILED
pause
exit /b 1
