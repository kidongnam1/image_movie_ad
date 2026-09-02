@echo off
setlocal
cd /d "%~dp0"
set "LIB=%~dp0AI_PROMPT_LIBRARY"
echo ==========================================================
echo AI Prompt Collector v6 - DOWNLOAD VERIFIED ONLY
echo ==========================================================
echo Target: verified_original repositories only
echo Download only ^(no indexing^)
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

%PY% download_only.py --root "%LIB%" --priority 3 --verified-only --retries 4 --retry-delay 5 --clone-timeout 1200 --text-only-clone
if errorlevel 1 goto FAIL

echo.
echo DOWNLOAD COMPLETE.
echo Repo root: %LIB%\repos
echo Status JSON: %LIB%\logs\clone_status_download_only.json
echo Summary JSON: %LIB%\logs\download_only_summary.json
pause
exit /b 0

:SETUP
echo Git or Python is missing. Starting setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
pause
exit /b 2

:FAIL
echo.
echo DOWNLOAD FAILED or incomplete. Check %LIB%\logs for details.
pause
exit /b 1
