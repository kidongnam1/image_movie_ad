@echo off
cd /d "%~dp0"
if not exist social_top50_report.html (
  echo Report not found. Running refresh first...
  call REFRESH_SOCIAL_TOP50.bat
)
if exist social_top50_report.html start "" "%~dp0social_top50_report.html"
