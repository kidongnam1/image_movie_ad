@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo AI Prompt Collector v6 - RESULT SUMMARY
echo ==========================================================
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto NOPY
  set "PY=py -3"
)
%PY% "%~dp0result_summary.py"
if errorlevel 1 goto FAIL
if exist "%~dp0AI_PROMPT_LIBRARY\reports\RESULT_SUMMARY.html" start "" "%~dp0AI_PROMPT_LIBRARY\reports\RESULT_SUMMARY.html"
echo.
echo Reports saved in: %~dp0AI_PROMPT_LIBRARY\reports
pause
exit /b 0
:NOPY
echo Python is not installed or not on PATH.
pause
exit /b 2
:FAIL
echo Result summary generation failed.
pause
exit /b 1
