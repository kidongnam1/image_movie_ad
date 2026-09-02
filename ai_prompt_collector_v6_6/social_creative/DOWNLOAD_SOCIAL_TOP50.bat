@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
echo ==========================================================
echo SNS Creative - Download Stars TOP50
 echo Current source only / shallow clone / Git LFS skipped
 echo ==========================================================
if not exist social_top50_stars.csv (
  echo TOP50 index not found. Refreshing first...
  %PY% refresh_social_top50.py
  if errorlevel 1 goto FAIL
)
%PY% download_social_top50.py --rank stars --retries 3 --retry-delay 4 --timeout 1800
if errorlevel 1 goto FAIL
echo.
echo COMPLETE: 50 repositories downloaded/updated.
echo Folder: %~dp0SOCIAL_CREATIVE_LIBRARY\repos
pause
exit /b 0
:FAIL
echo.
echo Download incomplete. Check:
echo %~dp0SOCIAL_CREATIVE_LIBRARY\logs\download_status_stars.json
echo %~dp0SOCIAL_CREATIVE_LIBRARY\logs\download_summary_stars.json
pause
exit /b 1
