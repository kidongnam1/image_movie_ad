@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Creative Package V1 Verification

echo ==========================================================
echo.

echo [1/2] Unit tests
python -m unittest discover -s tests -p "test_creative_package_v1.py" -v
if errorlevel 1 goto FAIL

echo.
echo [2/2] Real DB end-to-end verification
python generator\creative_package_v1.py serum --description "daily skincare serum" --target "40-60 women" --duration 30 --project-id verify_creative_package_v1 --outdir outputs_verify --require-db
if errorlevel 1 goto FAIL

python -c "import json, pathlib; p=pathlib.Path(r'outputs_verify\verify_creative_package_v1'); m=json.load(open(p/'manifest.json',encoding='utf-8')); c=json.load(open(p/'compliance_report.json',encoding='utf-8')); s=json.load(open(p/'creative_scores.json',encoding='utf-8')); print('MILESTONE=',m['milestone']); print('STATUS=',m['status']); print('COMPLIANCE=',c['status']); print('RECOMMENDED=',s['recommended_variant']); assert m['status']=='PASS'; assert c['status']=='PASS'; assert len(m['missing_files'])==0; print('VERIFY_CREATIVE_PACKAGE_V1 PASS')"
if errorlevel 1 goto FAIL

echo.
echo VERIFY_CREATIVE_PACKAGE_V1 PASS
pause
exit /b 0

:FAIL
echo.
echo VERIFY_CREATIVE_PACKAGE_V1 FAILED
pause
exit /b 1
