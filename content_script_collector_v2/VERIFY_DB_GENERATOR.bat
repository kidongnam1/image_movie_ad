@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.6 - DB + 성과학습 + 전수 회귀 검증
echo ==========================================================
echo.

echo [1/7] Python syntax check
python -m py_compile generator\script_generator_v25.py generator\performance_store_v26.py generator\ad_performance_learning.py generator\script_generator_v26.py generator\script_generator_v2.py generator\creative_package_v26.py
if errorlevel 1 goto FAIL

echo [2/7] 기존 selftest + 5상품 회귀테스트
python tests\selftest_v2.py
if errorlevel 1 goto FAIL
python tests\test_script_generator_v25.py
if errorlevel 1 goto FAIL

echo [3/7] V2.6 성과 DB / Snapshot Update / 표본축소 / Hook-Creative 학습
python tests\test_ad_performance_learning.py
if errorlevel 1 goto FAIL

echo [4/7] V2.6 학습 재랭킹 / Cold Start / A-B-C 테스트
python tests\test_script_generator_v26.py
if errorlevel 1 goto FAIL

echo [5/7] Creative Package V2.6 sidecar 테스트
python tests\test_creative_package_v26.py
if errorlevel 1 goto FAIL

echo [6/7] 기존 Creative Package 회귀테스트
python tests\test_creative_package_v1.py
if errorlevel 1 goto FAIL

echo [7/7] Real Content DB integration + isolated Cold Start performance DB
if exist outputs_verify\verify_performance.sqlite del /q outputs_verify\verify_performance.sqlite
python generator\script_generator_v2.py "골프 거리측정기" --must-emphasize "0.2초 측정|손떨림 보정" --features "800m 측정|150g 초경량" --target "40~60대 골퍼" --intensity 5 --performance-db outputs_verify\verify_performance.sqlite --require-db --outdir outputs_verify
if errorlevel 1 goto FAIL

python -c "import json; d=json.load(open(r'outputs_verify\골프_거리측정기_script_v2.json',encoding='utf-8')); assert d['version']=='2.6'; assert d['db_integration']['connected']; assert len(d['hooks'])==30; assert d['product_analysis']['category']=='golf'; assert d['product_analysis']['primary_selling_point'] in d['top3'][0]['text']; assert d['quality_audit']['generic_hook_hits']==0; assert d['quality_audit']['banned_hook_hits']==0; assert d['quality_audit']['must_emphasize_coverage']['30s']==100.0; assert len(d['experiment_plan']['candidates'])==3; assert not d['performance_learning']['active']; print('VERIFY_DB_GENERATOR_V2_6 PASS')"
if errorlevel 1 goto FAIL

echo.
echo VERIFY_DB_GENERATOR_V2_6 PASS
pause
exit /b 0

:FAIL
echo.
echo VERIFY_DB_GENERATOR_V2_6 FAILED
pause
exit /b 1
