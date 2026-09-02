@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
if not exist social_top50_recommended.csv (
  %PY% refresh_social_top50.py
  if errorlevel 1 goto FAIL
)
%PY% download_social_top50.py --rank recommended --retries 3 --retry-delay 4 --timeout 1800
if errorlevel 1 goto FAIL
pause
exit /b 0
:FAIL
echo Download incomplete. Check SOCIAL_CREATIVE_LIBRARY\logs.
pause
exit /b 1
