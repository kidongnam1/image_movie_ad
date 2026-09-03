@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.7 - 전체 회귀 + 플랫폼 어댑터 + 대시보드 검증
echo ==========================================================
echo.

echo [1/10] Python syntax check
python -m py_compile generator\script_generator_v25.py generator\performance_store_v26.py generator\script_generator_v26.py generator\performance_registry_v27.py generator\platform_performance_adapter_v27.py generator\performance_dashboard_v27.py generator\script_generator_v27.py generator\script_generator_v2.py generator\creative_package_v26.py
if errorlevel 1 goto FAIL

echo [2/10] 기존 selftest + 5상품 V2.5 회귀
python tests\selftest_v2.py
if errorlevel 1 goto FAIL
python tests\test_script_generator_v25.py
if errorlevel 1 goto FAIL

echo [3/10] V2.6 성과 DB / Snapshot Update / 표본축소
python tests\test_ad_performance_learning.py
if errorlevel 1 goto FAIL

echo [4/10] V2.6 학습 재랭킹 / Cold Start / A-B-C
python tests\test_script_generator_v26.py
if errorlevel 1 goto FAIL

echo [5/10] V2.7 Creative Registry 자동등록
python tests\test_script_generator_v27.py
if errorlevel 1 goto FAIL

echo [6/10] V2.7 Meta/TikTok/Naver/Coupang Adapter
python tests\test_platform_adapter_v27.py
if errorlevel 1 goto FAIL

echo [7/10] V2.7 Standalone Dashboard
python tests\test_performance_dashboard_v27.py
if errorlevel 1 goto FAIL

echo [8/10] Creative Package V2.6 sidecar + 기존 회귀
python tests\test_creative_package_v26.py
if errorlevel 1 goto FAIL
python tests\test_creative_package_v1.py
if errorlevel 1 goto FAIL

echo [9/10] Real Content DB integration + isolated performance DB
if exist outputs_verify\verify_performance.sqlite del /q outputs_verify\verify_performance.sqlite
python generator\script_generator_v2.py "골프 거리측정기" --must-emphasize "0.2초 측정|손떨림 보정" --features "800m 측정|150g 초경량" --target "40~60대 골퍼" --intensity 5 --performance-db outputs_verify\verify_performance.sqlite --require-db --outdir outputs_verify
if errorlevel 1 goto FAIL
python -c "import json,sqlite3; d=json.load(open(r'outputs_verify\골프_거리측정기_script_v2.json',encoding='utf-8')); assert d['version']=='2.7'; assert d['db_integration']['connected']; assert len(d['hooks'])==30; assert d['product_analysis']['category']=='golf'; assert len(d['experiment_plan']['candidates'])==3; assert d['creative_registry']['registered_candidates']==3; c=sqlite3.connect(r'outputs_verify\verify_performance.sqlite'); n=c.execute('select count(*) from creative_registry').fetchone()[0]; c.close(); assert n==3; print('REAL_DB_V27 PASS')"
if errorlevel 1 goto FAIL

echo [10/10] Dashboard generation on isolated DB
python generator\performance_dashboard_v27.py --db outputs_verify\verify_performance.sqlite --out outputs_verify\performance_dashboard_v27.html
if errorlevel 1 goto FAIL
python -c "from pathlib import Path; p=Path(r'outputs_verify\performance_dashboard_v27.html'); assert p.exists(); t=p.read_text(encoding='utf-8'); assert 'V2.7 광고 성과 대시보드' in t; assert 'https://' not in t; print('VERIFY_DB_GENERATOR_V2_7 PASS')"
if errorlevel 1 goto FAIL

echo.
echo VERIFY_DB_GENERATOR_V2_7 PASS
pause
exit /b 0

:FAIL
echo.
echo VERIFY_DB_GENERATOR_V2_7 FAILED
pause
exit /b 1
