@echo off
setlocal
cd /d "%~dp0"
set "LIB=%~dp0AI_PROMPT_LIBRARY"
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (where py >nul 2>nul && set "PY=py -3")
%PY% collect_and_index.py --root "%LIB%" --priority 3 --include-tooling --index-only
%PY% postflight_validate.py --root "%LIB%"
%PY% build_dashboard.py --root "%LIB%"
if exist "%LIB%\dashboard.html" start "" "%LIB%\dashboard.html"
pause
