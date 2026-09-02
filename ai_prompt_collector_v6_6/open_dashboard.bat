@echo off
set "D=%~dp0AI_PROMPT_LIBRARY\dashboard.html"
if exist "%D%" (start "" "%D%") else (echo Dashboard does not exist yet. Run run_full_auto.bat first. & pause)
