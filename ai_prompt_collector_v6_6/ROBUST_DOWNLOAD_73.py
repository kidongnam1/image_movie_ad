from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error, zipfile
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent


def run(cmd, timeout=600, cwd=None):
    env = dict(os.environ)
    env.setdefault('GIT_TERMINAL_PROMPT', '0')
    env.setdefault('GIT_LFS_SKIP_SMUDGE', '1')
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                           timeout=timeout, env=env)
        return p.returncode, p.stdout or ''
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or '') + '\nTIMEOUT'
    except Exception as e:
        return 125, f'{type(e).__name__}: {e}'


def slug(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('_')


def select_repos(manifest: dict) -> list[dict]:
    out = []
    for r in manifest.get('repos', []):
        active = str(r.get('active', '')).strip().lower() in {'1','true','yes','y'} or r.get('active') is True
        if not active:
            continue
        if r.get('origin_status') in {'candidate', 'duplicate_excluded'}:
            continue
        if r.get('source_kind') not in {'corpus', 'tooling'}:
            continue
        try:
            if int(float(r.get('priority', 2) or 2)) > 3:
                continue
        except Exception:
            pass
        out.append(r)
    return out


def github_parts(url: str):
    m = re.match(r'https?://github\.com/([^/]+)/([^/#]+?)(?:\.git)?$', url.strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def github_api_default_branch(owner: str, repo: str, timeout=30) -> str:
    url = f'https://api.github.com/repos/{owner}/{repo}'
    req = urllib.request.Request(url, headers={'User-Agent':'AI-Prompt-Collector-v6.1','Accept':'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
            return data.get('default_branch') or 'main'
    except Exception:
        return 'main'


def download_zip_fallback(repo: dict, dest: Path, temp_root: Path, timeout=300) -> tuple[bool, str]:
    owner, name = github_parts(repo['url'])
    if not owner:
        return False, 'Not a supported GitHub URL for ZIP fallback.'
    branches = []
    api_branch = github_api_default_branch(owner, name)
    for b in [api_branch, 'main', 'master']:
        if b and b not in branches:
            branches.append(b)

    temp_root.mkdir(parents=True, exist_ok=True)
    zpath = temp_root / f'{slug(owner+"_"+name)}.zip'
    last = ''
    for branch in branches:
        url = f'https://codeload.github.com/{owner}/{name}/zip/refs/heads/{branch}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'AI-Prompt-Collector-v6.1'})
            with urllib.request.urlopen(req, timeout=timeout) as resp, open(zpath, 'wb') as f:
                shutil.copyfileobj(resp, f)
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            extract_dir = temp_root / f'extract_{slug(owner+"_"+name)}'
            shutil.rmtree(extract_dir, ignore_errors=True)
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zpath) as z:
                z.extractall(extract_dir)
            roots = [p for p in extract_dir.iterdir() if p.is_dir()]
            src = roots[0] if len(roots) == 1 else extract_dir
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            marker = {
                'repo': repo['repo'], 'url': repo['url'], 'method':'github_codeload_zip',
                'branch': branch, 'downloaded_at': datetime.now().isoformat(timespec='seconds')
            }
            (dest/'.github_zip_source.json').write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding='utf-8')
            shutil.rmtree(extract_dir, ignore_errors=True)
            try: zpath.unlink()
            except Exception: pass
            return True, f'ZIP fallback OK ({branch})'
        except Exception as e:
            last = f'{type(e).__name__}: {e}'
    return False, f'ZIP fallback failed: {last}'


def git_try(repo: dict, dest: Path, timeout=1200) -> tuple[bool, str]:
    if not shutil.which('git'):
        return False, 'git not found'
    if (dest/'.git').exists():
        code, out = run(['git','-c','core.longpaths=true','-C',str(dest),'pull','--ff-only'], timeout=timeout)
        return code == 0, ('git update OK' if code == 0 else out[-2500:])
    if dest.exists() and any(dest.iterdir()):
        marker = dest/'.github_zip_source.json'
        if marker.exists():
            return True, 'existing ZIP fallback repository'
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['git','-c','core.longpaths=true','clone','--depth','1','--no-tags','--single-branch',
           '--filter=blob:none','--no-checkout',repo['url'],str(dest)]
    code, out = run(cmd, timeout=timeout)
    if code != 0:
        shutil.rmtree(dest, ignore_errors=True)
        return False, out[-2500:]
    patterns=['*.json','*.jsonl','*.ndjson','*.csv','*.tsv','*.md','*.markdown','*.txt','*.yaml','*.yml','*.js','*.ts','*.jsx','*.tsx','*.py','*.html','*.htm','*.toml','*.ini','*.xml','*.vue','*.svelte','LICENSE*','COPYING*']
    c1,o1 = run(['git','-C',str(dest),'sparse-checkout','init','--no-cone'], timeout=120)
    c2,o2 = run(['git','-C',str(dest),'sparse-checkout','set','--no-cone',*patterns], timeout=180) if c1 == 0 else (c1,o1)
    c3,o3 = run(['git','-C',str(dest),'checkout'], timeout=timeout) if c2 == 0 else (c2,o2)
    if c3 != 0:
        shutil.rmtree(dest, ignore_errors=True)
        return False, (o1+'\n'+o2+'\n'+o3)[-2500:]
    return True, 'git sparse clone OK'


def connectivity_tests(log):
    log('=== CONNECTIVITY TEST ===')
    log('Python: ' + sys.version.replace('\n',' '))
    log('Git: ' + (shutil.which('git') or 'NOT FOUND'))
    if shutil.which('git'):
        code,out=run(['git','--version'],timeout=15); log(f'git --version: rc={code} {out.strip()}')
        code,out=run(['git','ls-remote','https://github.com/Toolcentral-ai/awesome-gpt-image-2-prompts.git','HEAD'],timeout=45)
        log(f'GitHub git test: rc={code} {out.strip()[-1000:]}')
    try:
        req=urllib.request.Request('https://api.github.com/repos/Toolcentral-ai/awesome-gpt-image-2-prompts',headers={'User-Agent':'AI-Prompt-Collector-v6.1'})
        with urllib.request.urlopen(req,timeout=30) as r:
            log(f'GitHub HTTPS/API test: HTTP {getattr(r,"status",200)}')
    except Exception as e:
        log(f'GitHub HTTPS/API test FAILED: {type(e).__name__}: {e}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='AI_PROMPT_LIBRARY')
    ap.add_argument('--manifest',default=str(HERE/'repos_manifest.json'))
    ap.add_argument('--git-timeout',type=int,default=1200)
    args=ap.parse_args()
    root=Path(args.root).resolve(); logs=root/'logs'; logs.mkdir(parents=True,exist_ok=True)
    temp=root/'_download_temp'; temp.mkdir(parents=True,exist_ok=True)
    logfile=logs/'ROBUST_DOWNLOAD_73.log'
    def log(msg):
        line=f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}'
        print(line, flush=True)
        with open(logfile,'a',encoding='utf-8') as f: f.write(line+'\n')

    connectivity_tests(log)
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    repos=select_repos(manifest)
    log(f'Selected active repositories: {len(repos)}')
    statuses=[]
    for i,r in enumerate(repos,1):
        dest=root/'repos'/r['media_type']/r['model_family']/slug(r['repo'])
        log(f'[{i}/{len(repos)}] {r["repo"]}')
        ok,msg=git_try(r,dest,timeout=args.git_timeout)
        method='git'
        log('  git: '+msg.replace('\n',' ')[:2000])
        if not ok:
            method='zip_fallback'
            ok,msg=download_zip_fallback(r,dest,temp)
            log('  zip: '+msg.replace('\n',' ')[:2000])
        statuses.append({'repo':r['repo'],'url':r['url'],'dest':str(dest),'ok':ok,'method':method,'message':msg})
        (logs/'ROBUST_DOWNLOAD_73_STATUS.json').write_text(json.dumps(statuses,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.rmtree(temp,ignore_errors=True)
    okn=sum(1 for x in statuses if x['ok']); fail=len(statuses)-okn
    summary={'selected':len(repos),'success':okn,'failed':fail,'git_success':sum(1 for x in statuses if x['ok'] and x['method']=='git'),'zip_fallback_success':sum(1 for x in statuses if x['ok'] and x['method']=='zip_fallback'),'log':str(logfile)}
    (logs/'ROBUST_DOWNLOAD_73_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    log('SUMMARY: '+json.dumps(summary,ensure_ascii=False))
    return 0 if fail==0 else 1

if __name__=='__main__':
    raise SystemExit(main())
