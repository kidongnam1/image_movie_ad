@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "LIB=%~dp0AI_PROMPT_LIBRARY"
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto NOPYTHON
  set "PY=py -3"
)

echo ==========================================================
echo AI Prompt Collector v6.1 - ROBUST DOWNLOAD 73 + INDEX
echo ==========================================================
echo 1. Git clone first
echo 2. Failed Git repos fallback to GitHub ZIP
echo 3. Index all downloaded repositories
echo 4. Keep a detailed log

echo.
%PY% refresh_manifest_views.py
if errorlevel 1 goto FAIL
%PY% validate_manifest.py
if errorlevel 1 goto FAIL

echo.
echo [STEP 1/3] Downloading 73 active repositories...
%PY% ROBUST_DOWNLOAD_73.py --root "%LIB%"
set "DLRC=%ERRORLEVEL%"

echo.
echo [STEP 2/3] Indexing everything that was downloaded...
%PY% collect_and_index.py --root "%LIB%" --priority 3 --include-tooling --index-only
set "IDXRC=%ERRORLEVEL%"

echo.
echo [STEP 3/3] Validating and building dashboard...
%PY% postflight_validate.py --root "%LIB%"
set "POSTRC=%ERRORLEVEL%"
%PY% build_dashboard.py --root "%LIB%"
if exist "%LIB%\dashboard.html" start "" "%LIB%\dashboard.html"

echo.
echo ==========================================================
echo DONE
if exist "%LIB%\logs\ROBUST_DOWNLOAD_73_SUMMARY.json" type "%LIB%\logs\ROBUST_DOWNLOAD_73_SUMMARY.json"
echo.
echo Detailed log:
echo %LIB%\logs\ROBUST_DOWNLOAD_73.log
echo Status:
echo %LIB%\logs\ROBUST_DOWNLOAD_73_STATUS.json
echo Index summary:
echo %LIB%\indexes\summary.json
echo ==========================================================
if not "%DLRC%"=="0" echo NOTE: Some repositories failed. The log tells which ones.
if not "%IDXRC%"=="0" echo NOTE: Indexing reported an error.
if not "%POSTRC%"=="0" echo NOTE: Postflight validation reported an issue.
pause
exit /b 0

:NOPYTHON
echo Python 3 was not found.
echo Run setup_windows.ps1 or install Python 3.10+.
pause
exit /b 2

:FAIL
echo Preparation failed before download.
echo Keep this window open and review the error above.
pause
exit /b 1
