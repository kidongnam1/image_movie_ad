@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto SETUP
  set "PY=py -3"
)

%PY% PROMPT_BUILDER_GUI.py
exit /b %ERRORLEVEL%

:SETUP
echo Python is missing. Starting setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
pause
exit /b 2
