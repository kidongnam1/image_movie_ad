@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
echo ==========================================================
echo Social Creative GitHub TOP50 - Refresh Stars + Index
echo ==========================================================
%PY% refresh_social_top50.py
if errorlevel 1 (
  echo.
  echo Refresh incomplete. If GitHub rate limit appears, login with GitHub CLI or set GITHUB_TOKEN.
  pause
  exit /b 1
)
echo.
echo COMPLETE: social_top50_stars.csv / social_top50_recommended.csv
pause
