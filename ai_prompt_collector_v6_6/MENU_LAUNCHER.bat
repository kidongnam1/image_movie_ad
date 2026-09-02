@echo off
setlocal
cd /d "%~dp0"

:MENU
cls
echo ==========================================================
echo AI Prompt Collector v6 - MENU LAUNCHER
echo ==========================================================
echo.
echo [1] Download 63 Corpus Only
echo [2] Download Verified Originals Only
echo [3] Download 73 + Index + Dashboard
echo [4] Check Status
echo [5] Open Dashboard
echo [6] Reindex Only
echo [7] Result Summary
echo [8] Make Prompt - Text Wizard
echo [9] Make Prompt - GUI
echo [10] Refresh SNS Creative TOP50
echo [11] Refresh + Download ALL SNS Creative Stars TOP50
echo [12] Search SNS Creative TOP50
echo [13] Unified Search (Prompts + SNS Tools)
echo [14] Check SNS Creative TOP50 Status
echo [0] Exit
echo.
set "CHOICE="
set /p CHOICE=Select: 

if "%CHOICE%"=="1" goto OPT1
if "%CHOICE%"=="2" goto OPT2
if "%CHOICE%"=="3" goto OPT3
if "%CHOICE%"=="4" goto OPT4
if "%CHOICE%"=="5" goto OPT5
if "%CHOICE%"=="6" goto OPT6
if "%CHOICE%"=="7" goto OPT7
if "%CHOICE%"=="8" goto OPT8
if "%CHOICE%"=="9" goto OPT9
if "%CHOICE%"=="10" goto OPT10
if "%CHOICE%"=="11" goto OPT11
if "%CHOICE%"=="12" goto OPT12
if "%CHOICE%"=="13" goto OPT13
if "%CHOICE%"=="14" goto OPT14
if "%CHOICE%"=="0" goto END

echo.
echo Invalid selection. Please choose 0-14.
pause
goto MENU

:OPT1
call "%~dp0DOWNLOAD_63_CORPUS_ONLY.bat"
goto MENU

:OPT2
call "%~dp0DOWNLOAD_VERIFIED_ONLY.bat"
goto MENU

:OPT3
call "%~dp0DOWNLOAD_73_AND_INDEX.bat"
goto MENU

:OPT4
call "%~dp0CHECK_STATUS.bat"
goto MENU

:OPT5
call "%~dp0open_dashboard.bat"
goto MENU

:OPT6
call "%~dp0run_reindex_only.bat"
goto MENU

:OPT7
call "%~dp0RESULT_SUMMARY.bat"
goto MENU

:OPT8
call "%~dp0MAKE_PROMPT.bat"
goto MENU

:OPT9
call "%~dp0PROMPT_BUILDER_GUI.bat"
goto MENU

:OPT10
call "%~dp0social_creative\REFRESH_SOCIAL_TOP50.bat"
goto MENU

:OPT11
call "%~dp0social_creative\SOCIAL_TOP50_ALL.bat"
goto MENU

:OPT12
call "%~dp0social_creative\SEARCH_SOCIAL_TOP50.bat"
goto MENU

:OPT13
call "%~dp0UNIFIED_SEARCH.bat"
goto MENU

:OPT14
call "%~dp0social_creative\CHECK_SOCIAL_TOP50.bat"
goto MENU

:END
endlocal
exit /b 0
