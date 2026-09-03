@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo V2.7 상품 이미지 입력창
echo Ctrl+V / 파일 / 직접 이미지 URL / 상품 페이지 URL

echo ==========================================================
python generator\product_image_input_v27.py
if errorlevel 1 goto FAIL
exit /b 0
:FAIL
echo.
echo GUI 실행 실패 - Pillow/requests 설치 및 logs를 확인하세요.
pause
exit /b 1
