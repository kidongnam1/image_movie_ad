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

echo ==========================================================
echo AI Prompt Collector v6 - MAKE PROMPT
echo ==========================================================
echo This wizard helps you build a prompt from your idea.
echo Output folder: %~dp0AI_PROMPT_LIBRARY\prompt_outputs
if not exist "%~dp0AI_PROMPT_LIBRARY\indexes\prompt_library.sqlite" (
  echo.
  echo NOTE: prompt_library.sqlite was not found.
  echo The builder will still work, but it will use model profiles only.
  echo To use local prompt examples too, run download + indexing first.
  echo.
)
%PY% PROMPT_BUILDER.py
set EXITCODE=%ERRORLEVEL%
echo.
if "%EXITCODE%"=="0" (
  echo Prompt build complete.
  if exist "%~dp0AI_PROMPT_LIBRARY\prompt_outputs" start "" "%~dp0AI_PROMPT_LIBRARY\prompt_outputs"
) else (
  echo Prompt build finished with exit code %EXITCODE%.
)
pause
exit /b %EXITCODE%

:SETUP
echo Python is missing. Starting setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
pause
exit /b 2
