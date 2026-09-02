@echo off
setlocal
cd /d "%~dp0"
set "MANIFEST="
set "OVERLAP="
if exist "..\repos_manifest.csv" set "MANIFEST=..\repos_manifest.csv"
if exist "..\AI_PROMPT_LIBRARY\indexes\repo_overlap_report.csv" set "OVERLAP=..\AI_PROMPT_LIBRARY\indexes\repo_overlap_report.csv"
if "%MANIFEST%"=="" (
  echo Could not find repos_manifest.csv one folder above.
  echo Copy this V2 folder into the AI Prompt Collector root or edit this BAT path.
  pause
  exit /b 2
)
if "%OVERLAP%"=="" (
  echo [WARN] repo_overlap_report.csv not found. Running metadata/diversity audit.
  python prompt_core\full_audit_core25.py --manifest "%MANIFEST%" --outdir prompt_core\final
) else (
  python prompt_core\full_audit_core25.py --manifest "%MANIFEST%" --overlap "%OVERLAP%" --outdir prompt_core\final
)
pause
