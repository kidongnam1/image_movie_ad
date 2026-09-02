@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PRODUCT=%~1"
if not defined PRODUCT (
  set /p PRODUCT=Product name: 
)

echo.
echo [DB CHECK] Running Script Generator V2.2 with the real Content DB...
python generator\script_generator_v2.py "%PRODUCT%" --require-db

if errorlevel 1 goto FAIL

echo.
echo SUCCESS
echo Check the outputs folder.
pause
exit /b 0

:FAIL
echo.
echo FAILED - Check database and logs.
pause
exit /b 1
