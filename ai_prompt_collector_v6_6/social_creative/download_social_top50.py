from __future__ import annotations
import argparse, csv, json, os, shutil, subprocess, time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

def run(cmd, timeout=1200, env=None):
    try:
        e=os.environ.copy()
        if env: e.update(env)
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,env=e)
        return p.returncode,(p.stdout+'\n'+p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124,'timeout'
    except Exception as ex:
        return 1,f'{type(ex).__name__}: {ex}'

def main():
    ap=argparse.ArgumentParser(description='Download all selected SNS Creative TOP50 repositories.')
    ap.add_argument('--rank',choices=['stars','recommended'],default='stars')
    ap.add_argument('--root',default=str(HERE/'SOCIAL_CREATIVE_LIBRARY'))
    ap.add_argument('--retries',type=int,default=3)
    ap.add_argument('--retry-delay',type=int,default=4)
    ap.add_argument('--timeout',type=int,default=1800)
    args=ap.parse_args()

    if not shutil.which('git'):
        raise SystemExit('Git not found. Install Git for Windows first.')

    csvp=HERE/('social_top50_stars.csv' if args.rank=='stars' else 'social_top50_recommended.csv')
    if not csvp.exists():
        raise SystemExit('TOP50 CSV not found. Run REFRESH_SOCIAL_TOP50.bat first.')
    rows=list(csv.DictReader(open(csvp,encoding='utf-8-sig')))
    if len(rows) < 50:
        raise SystemExit(f'Expected 50 repositories, found {len(rows)}. Refresh TOP50 first.')

    root=Path(args.root)
    repos_root=root/'repos'
    logs=root/'logs'
    repos_root.mkdir(parents=True,exist_ok=True)
    logs.mkdir(parents=True,exist_ok=True)
    status=[]
    status_path=logs/f'download_status_{args.rank}.json'
    summary_path=logs/f'download_summary_{args.rank}.json'
    git_env={'GIT_LFS_SKIP_SMUDGE':'1','GIT_TERMINAL_PROMPT':'0'}

    for i,r in enumerate(rows,1):
        repo=r['repo'].strip()
        dest=repos_root/repo.replace('/','__')
        print(f'[{i}/{len(rows)}] {repo} | stars={r.get("stars","")}')
        success=False; last_code=1; last_out=''; last_status='failed'; attempts=0
        for attempt in range(1,args.retries+1):
            attempts=attempt
            if (dest/'.git').exists():
                cmd=['git','-C',str(dest),'pull','--ff-only']
                code,out=run(cmd,args.timeout,git_env)
                st='updated' if code==0 else 'update_failed'
            else:
                if dest.exists(): shutil.rmtree(dest,ignore_errors=True)
                cmd=['git','clone','--depth','1','--filter=blob:none','--single-branch','https://github.com/'+repo+'.git',str(dest)]
                code,out=run(cmd,args.timeout,git_env)
                st='cloned' if code==0 else 'clone_failed'
            last_code,last_out,last_status=code,out,st
            if code==0:
                success=True
                break
            time.sleep(args.retry_delay*attempt)
        item={
            'repo':repo,'rank_mode':args.rank,'rank':r.get('stars_rank') if args.rank=='stars' else r.get('recommended_rank'),
            'stars':r.get('stars'),'status':last_status,'success':success,'attempts':attempts,'code':last_code,
            'local_path':str(dest),'message':last_out[-2000:]
        }
        status.append(item)
        status_path.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
        print(' ',last_status,'attempts=',attempts)

    ok=sum(x['success'] for x in status)
    failed=[x['repo'] for x in status if not x['success']]
    summary={
        'generated_at':datetime.now().isoformat(timespec='seconds'),
        'rank_mode':args.rank,'selected':len(status),'success':ok,'failed':len(failed),
        'failed_repos':failed,'repo_root':str(repos_root),'status_file':str(status_path),
        'download_policy':'shallow current source; Git history omitted; Git LFS smudge disabled'
    }
    summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if ok==len(status) else 1

if __name__=='__main__':
    raise SystemExit(main())
