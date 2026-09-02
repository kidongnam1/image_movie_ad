@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
set /p Q=Search keyword (thumbnail, social, product, video, background...): 
%PY% search_social_repos.py "%Q%" --rank recommended --limit 30
pause
