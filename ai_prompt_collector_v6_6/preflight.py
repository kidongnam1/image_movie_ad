from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, platform
from pathlib import Path
from datetime import datetime

ap=argparse.ArgumentParser(description='Windows/local preflight for AI Prompt Collector v6.')
ap.add_argument('--root',default='AI_PROMPT_LIBRARY')
ap.add_argument('--min-free-gb',type=float,default=5.0)
ap.add_argument('--skip-network',action='store_true')
a=ap.parse_args()
root=Path(a.root).resolve(); root.mkdir(parents=True,exist_ok=True); (root/'logs').mkdir(exist_ok=True)
checks=[]
def add(name,ok,detail,critical=True): checks.append({'name':name,'ok':bool(ok),'critical':critical,'detail':str(detail)})

add('Python >= 3.10', sys.version_info >= (3,10), sys.version.split()[0])
git=shutil.which('git'); add('Git available',bool(git),git or 'git not found on PATH')
if git:
    try:
        pv=subprocess.run([git,'--version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=10)
        ver=(pv.stdout or '').strip(); add('Git sparse-checkout support',True,ver,critical=False)
    except Exception as e: add('Git sparse-checkout support',False,e,critical=False)
try:
    probe=root/'logs'/'.write_test'; probe.write_text('ok',encoding='utf-8'); probe.unlink(); add('Output folder writable',True,root)
except Exception as e: add('Output folder writable',False,e)
try:
    usage=shutil.disk_usage(root); free_gb=usage.free/(1024**3); add(f'Free disk >= {a.min_free_gb:.1f} GB',free_gb>=a.min_free_gb,f'{free_gb:.2f} GB free',critical=False)
except Exception as e: add('Disk space readable',False,e,critical=False)
if git and not a.skip_network:
    try:
        env=dict(os.environ); env['GIT_TERMINAL_PROMPT']='0'; env['GIT_LFS_SKIP_SMUDGE']='1'
        p=subprocess.run([git,'ls-remote','https://github.com/Toolcentral-ai/awesome-gpt-image-2-prompts.git','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=30,env=env)
        add('GitHub reachable',p.returncode==0,(p.stdout or '').strip()[-600:] or f'exit={p.returncode}')
    except Exception as e: add('GitHub reachable',False,e)
else:
    add('GitHub reachable',True,'skipped',critical=False)

report={'version':'6.0','checked_at':datetime.now().isoformat(timespec='seconds'),'platform':platform.platform(),'root':str(root),'checks':checks}
(root/'logs'/'preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('\nAI Prompt Collector v6 - Preflight')
print('='*55)
for c in checks: print(('PASS' if c['ok'] else 'FAIL' if c['critical'] else 'WARN').ljust(5), c['name'], '-', c['detail'])
critical_fail=[c for c in checks if c['critical'] and not c['ok']]
if critical_fail:
    print('\nPreflight FAILED. Fix the FAIL items, then rerun.')
    sys.exit(2)
print('\nPreflight PASS. Collection can start.')
