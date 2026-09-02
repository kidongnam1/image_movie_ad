@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo MEDIA_RENDER_V1 - 최종 MP4 합성

echo ==========================================================
echo.
set /p PROJECT_DIR=Creative Package 프로젝트 폴더 경로 입력: 
if "%PROJECT_DIR%"=="" goto FAIL
set /p VIDEO_MODEL=영상 모델 kling/veo/seedance (기본: kling): 
if "%VIDEO_MODEL%"=="" set VIDEO_MODEL=kling

python generator\media_render_v1.py "%PROJECT_DIR%" --variant recommended --video-model "%VIDEO_MODEL%" --execute
if errorlevel 1 goto FAIL

echo.
echo FINAL AD RENDER PASS
pause
exit /b 0

:FAIL
echo.
echo FINAL AD RENDER FAILED
echo render_readiness.json에서 누락된 Scene/voiceover/FFmpeg 상태를 확인하세요.
pause
exit /b 1
