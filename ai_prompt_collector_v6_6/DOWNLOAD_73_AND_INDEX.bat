@echo off
setlocal
cd /d "%~dp0"
set "LIB=%~dp0AI_PROMPT_LIBRARY"
echo ==========================================================
echo AI Prompt Collector v6 - DOWNLOAD 73 AND INDEX
echo ==========================================================
echo Target: 63 corpus + 10 tooling = 73 active repositories
echo Download + extract + dedupe + index + dashboard
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto SETUP
  set "PY=py -3"
)
where git >nul 2>nul
if errorlevel 1 goto SETUP

%PY% preflight.py --root "%LIB%"
if errorlevel 1 goto FAIL
%PY% refresh_manifest_views.py
if errorlevel 1 goto FAIL
%PY% validate_manifest.py
if errorlevel 1 goto FAIL

%PY% collect_and_index.py --root "%LIB%" --priority 3 --include-tooling --retries 4 --retry-delay 5 --clone-timeout 1200 --text-only-clone
if errorlevel 1 goto FAIL
%PY% postflight_validate.py --root "%LIB%"
if errorlevel 1 goto FAIL
%PY% build_dashboard.py --root "%LIB%"
if exist "%LIB%\dashboard.html" start "" "%LIB%\dashboard.html"

echo.
echo COMPLETE. Results: %LIB%\indexes
echo Dashboard: %LIB%\dashboard.html
pause
exit /b 0

:SETUP
echo Git or Python is missing. Starting setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
pause
exit /b 2

:FAIL
echo.
echo FAILED or incomplete. Check %LIB%\logs for details.
pause
exit /b 1
