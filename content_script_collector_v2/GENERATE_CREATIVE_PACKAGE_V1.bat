@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Creative Package V1 - 광고 제작 패키지 자동 생성
echo ==========================================================
echo.

set /p PRODUCT=상품명 입력: 
if "%PRODUCT%"=="" goto FAIL

set /p DESCRIPTION=상품 설명 입력 (선택): 
set /p TARGET=타깃 고객 입력 (기본: 일반 소비자): 
set /p DURATION=광고 길이 15/30/60 (기본: 30): 

if "%DURATION%"=="" set DURATION=30

python generator\creative_package_v1.py "%PRODUCT%" --description "%DESCRIPTION%" --target "%TARGET%" --duration %DURATION% --require-db
if errorlevel 1 goto FAIL

echo.
echo CREATIVE_PACKAGE_V1 PASS
echo 결과 폴더: outputs_creative
pause
exit /b 0

:FAIL
echo.
echo CREATIVE_PACKAGE_V1 FAILED
pause
exit /b 1
