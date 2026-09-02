@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================================
echo Script Generator V2.3 - DB + TOP3 Diversity Verification
echo ==========================================================
echo.

python generator\script_generator_v2.py serum --require-db --outdir outputs_verify
if errorlevel 1 goto FAIL

python -c "import json; d=json.load(open(r'outputs_verify\serum_script_v2.json',encoding='utf-8')); x=d['db_integration']; refs=x['hook_reference_ids']; print('DB_CONNECTED=',x['connected']); print('COUNTS=',x['counts']); print('TOP3_DB_REFS=',refs); print('TOP3_DIVERSITY=',x.get('top3_diversity')); assert x['connected']; assert any(v>0 for k,v in x['counts'].items() if k!='sources'); ids=[r['hook_id'] for r in refs if r['hook_id'] is not None]; cats=[r['category'] for r in refs]; assert len(set(ids))>=2, 'TOP3 hook_id diversity too low'; assert len(set(cats))>=2, 'TOP3 category diversity too low'; print('VERIFY_DB_GENERATOR_V2_3 PASS')"
if errorlevel 1 goto FAIL

echo.
echo VERIFY_DB_GENERATOR_V2_3 PASS
pause
exit /b 0

:FAIL
echo.
echo VERIFY_DB_GENERATOR_V2_3 FAILED
pause
exit /b 1
