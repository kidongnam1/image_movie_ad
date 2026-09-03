@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.5 - DB + 5상품 회귀 검증
echo ==========================================================
echo.

echo [1/3] Python syntax check
python -m py_compile generator\script_generator_v25.py generator\script_generator_v2.py
if errorlevel 1 goto FAIL

echo [2/3] 5상품 / 강조점 / 강도 회귀테스트
python tests\test_script_generator_v25.py
if errorlevel 1 goto FAIL

echo [3/3] Real Content DB integration
python generator\script_generator_v2.py "골프 거리측정기" --must-emphasize "0.2초 측정|손떨림 보정" --features "800m 측정|150g 초경량" --target "40~60대 골퍼" --intensity 5 --require-db --outdir outputs_verify
if errorlevel 1 goto FAIL

python -c "import json; d=json.load(open(r'outputs_verify\골프_거리측정기_script_v2.json',encoding='utf-8')); assert d['version']=='2.5'; assert d['db_integration']['connected']; assert len(d['hooks'])==30; assert d['product_analysis']['category']=='golf'; assert d['product_analysis']['primary_selling_point'] in d['top3'][0]['text']; assert d['quality_audit']['generic_hook_hits']==0; assert d['quality_audit']['banned_hook_hits']==0; assert d['quality_audit']['must_emphasize_coverage']['30s']==100.0; print('VERIFY_DB_GENERATOR_V2_5 PASS')"
if errorlevel 1 goto FAIL

echo.
echo VERIFY_DB_GENERATOR_V2_5 PASS
pause
exit /b 0

:FAIL
echo.
echo VERIFY_DB_GENERATOR_V2_5 FAILED
pause
exit /b 1
