@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo MEDIA_RENDER_V1 - 미디어 생성/합성 준비

echo ==========================================================
echo.
set /p PROJECT_DIR=Creative Package 프로젝트 폴더 경로 입력: 
if "%PROJECT_DIR%"=="" goto FAIL
set /p VIDEO_MODEL=영상 모델 kling/veo/seedance (기본: kling): 
if "%VIDEO_MODEL%"=="" set VIDEO_MODEL=kling

python generator\media_render_v1.py "%PROJECT_DIR%" --variant recommended --video-model "%VIDEO_MODEL%"
if errorlevel 1 goto FAIL

echo.
echo MEDIA_RENDER_V1 PREPARED
echo render_plan.json과 media_requests 폴더를 확인하세요.
pause
exit /b 0

:FAIL
echo.
echo MEDIA_RENDER_V1 FAILED
pause
exit /b 1
