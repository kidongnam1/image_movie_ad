@echo off
setlocal
cd /d "%~dp0"
set "LIB=%~dp0AI_PROMPT_LIBRARY"
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto SETUP
  set "PY=py -3"
)
where git >nul 2>nul
if errorlevel 1 goto SETUP
%PY% preflight.py --root "%LIB%" || goto FAIL
%PY% collect_and_index.py --root "%LIB%" --priority 3 --include-tooling --verified-only --text-only-clone --retries 4 --retry-delay 5 --clone-timeout 1200
%PY% postflight_validate.py --root "%LIB%"
set POSTRC=%ERRORLEVEL%
%PY% build_dashboard.py --root "%LIB%"
if exist "%LIB%\dashboard.html" start "" "%LIB%\dashboard.html"
if not "%POSTRC%"=="0" goto FAIL
pause
exit /b 0
:SETUP
echo Git or Python is missing. Starting setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
pause
exit /b 2
:FAIL
echo FAILED. Check AI_PROMPT_LIBRARY\logs
pause
exit /b 1
