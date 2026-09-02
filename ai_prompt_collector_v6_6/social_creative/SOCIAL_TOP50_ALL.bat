@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
where git >nul 2>nul
if errorlevel 1 (
  echo Git is not installed or not on PATH.
  pause
  exit /b 2
)
echo ==========================================================
echo SNS Creative TOP50 - REFRESH + DOWNLOAD ALL 50
 echo 1. Refresh live GitHub Stars / metadata
 echo 2. Build Stars TOP50 + Recommended TOP50 + SQLite
 echo 3. Download Stars TOP50 repositories
 echo 4. Open HTML report
 echo ==========================================================
echo.
%PY% refresh_social_top50.py
if errorlevel 1 goto FAIL

echo.
echo [INDEX] Refresh complete. Starting all 50 downloads...
%PY% download_social_top50.py --rank stars --retries 3 --retry-delay 4 --timeout 1800
if errorlevel 1 goto FAIL

echo.
echo ==========================================================
echo COMPLETE
 echo TOP50 metadata DB: social_creative_catalog.sqlite
 echo Stars TOP50: social_top50_stars.csv
 echo Recommended TOP50: social_top50_recommended.csv
 echo Repositories: SOCIAL_CREATIVE_LIBRARY\repos
 echo Download summary: SOCIAL_CREATIVE_LIBRARY\logs\download_summary_stars.json
 echo ==========================================================
if exist social_top50_report.html start "" social_top50_report.html
pause
exit /b 0
:FAIL
echo.
echo FAILED or incomplete.
echo Check social_top50_summary.json and SOCIAL_CREATIVE_LIBRARY\logs.
pause
exit /b 1
