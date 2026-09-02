from __future__ import annotations
import csv, json, math, os, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE=Path(__file__).resolve().parent
CAND=HERE/'social_repo_candidates.csv'
OUT_ALL=HERE/'social_repo_index.csv'
OUT_STARS=HERE/'social_top50_stars.csv'
OUT_REC=HERE/'social_top50_recommended.csv'
OUT_JSON=HERE/'social_top50_summary.json'
DB=HERE/'social_creative_catalog.sqlite'

FIELDS=['repo','category','sns_directness_score','capability','sns_use_case','stars','fork','archived','license_spdx','language','updated_at','pushed_at','metadata_status','stars_rank','recommended_score','recommended_rank']

def get_token():
    token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    if token: return token.strip()
    try:
        r=subprocess.run(['gh','auth','token'],capture_output=True,text=True,timeout=10)
        if r.returncode==0 and r.stdout.strip(): return r.stdout.strip()
    except Exception: pass
    return ''

def fetch_repo(repo, token=''):
    url='https://api.github.com/repos/'+repo
    headers={'Accept':'application/vnd.github+json','User-Agent':'AI-Prompt-Collector-Social-Top50'}
    if token: headers['Authorization']='Bearer '+token
    req=Request(url,headers=headers)
    try:
        with urlopen(req,timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8')), None
    except HTTPError as e:
        return None, f'HTTP {e.code}'
    except URLError as e:
        return None, f'URL {e.reason}'
    except Exception as e:
        return None, type(e).__name__+': '+str(e)

def activity_score(pushed_at, archived=False):
    if archived: return 0.0
    if not pushed_at: return 2.0
    try:
        dt=datetime.fromisoformat(pushed_at.replace('Z','+00:00'))
        days=(datetime.now(timezone.utc)-dt).days
        if days<=180:return 10.0
        if days<=365:return 8.0
        if days<=730:return 5.0
        if days<=1460:return 3.0
        return 1.0
    except Exception:return 2.0

def automation_score(cat):
    direct={'social_card_generator','social_card_generator_ai','thumbnail_generator','thumbnail_generator_ai','programmatic_video'}
    strong={'social_render_engine','canvas_engine','design_ai','image_editor','background_removal_ai','video_thumbnail'}
    if cat in direct:return 10.0
    if cat in strong:return 8.0
    return 6.0

def ai_prompt_score(cat):
    if 'ai' in cat:return 10.0
    if cat in {'ai_image_engine','ai_control','ai_training','programmatic_video'}:return 10.0
    if cat in {'social_card_generator','social_render_engine','thumbnail_generator','design_ai'}:return 8.0
    return 4.0

def license_score(spdx):
    return 5.0 if spdx and spdx not in {'NOASSERTION','UNKNOWN','NONE'} else 0.0

def write_csv(path, rows):
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)

def build_sqlite(rows, stars50, rec50):
    if DB.exists(): DB.unlink()
    con=sqlite3.connect(DB)
    cols='repo TEXT PRIMARY KEY, category TEXT, sns_directness_score REAL, capability TEXT, sns_use_case TEXT, stars INTEGER, fork INTEGER, archived INTEGER, license_spdx TEXT, language TEXT, updated_at TEXT, pushed_at TEXT, metadata_status TEXT, stars_rank INTEGER, recommended_score REAL, recommended_rank INTEGER'
    con.execute('CREATE TABLE repos ('+cols+')')
    placeholders=','.join('?' for _ in FIELDS)
    for r in rows:
        vals=[r.get(k,'') for k in FIELDS]
        con.execute(f'INSERT OR REPLACE INTO repos VALUES ({placeholders})',vals)
    con.execute('CREATE INDEX idx_stars ON repos(stars DESC)')
    con.execute('CREATE INDEX idx_rec ON repos(recommended_score DESC)')
    con.execute('CREATE INDEX idx_cat ON repos(category)')
    con.execute('CREATE TABLE top50_stars AS SELECT * FROM repos WHERE stars_rank BETWEEN 1 AND 50 ORDER BY stars_rank')
    con.execute('CREATE TABLE top50_recommended AS SELECT * FROM repos WHERE recommended_rank BETWEEN 1 AND 50 ORDER BY recommended_rank')
    try:
        con.execute("CREATE VIRTUAL TABLE repos_fts USING fts5(repo, category, capability, sns_use_case, content='repos', content_rowid='rowid')")
        con.execute("INSERT INTO repos_fts(rowid,repo,category,capability,sns_use_case) SELECT rowid,repo,category,capability,sns_use_case FROM repos")
    except sqlite3.OperationalError: pass
    con.commit();con.close()

def build_html(stars50, rec50, summary):
    import html as _html
    def esc(s):
        return _html.escape(str(s or ''))
    def table(rows, rankfield):
        trs=[]
        for r in rows:
            trs.append(
                '<tr>'
                f'<td>{esc(r.get(rankfield))}</td>'
                f'<td><a href="https://github.com/{esc(r.get("repo"))}">{esc(r.get("repo"))}</a></td>'
                f'<td>{int(r.get("stars") or 0):,}</td>'
                f'<td>{esc(r.get("category"))}</td>'
                f'<td>{esc(r.get("license_spdx"))}</td>'
                f'<td>{esc(r.get("capability"))}</td>'
                '</tr>'
            )
        return '<table><thead><tr><th>Rank</th><th>Repository</th><th>Stars</th><th>Category</th><th>License</th><th>Capability</th></tr></thead><tbody>'+''.join(trs)+'</tbody></table>'
    html_text = (
        '<!doctype html><html><head><meta charset="utf-8"><title>SNS Creative GitHub TOP50</title>'
        '<style>body{font-family:Segoe UI,Arial,sans-serif;margin:28px;color:#222}h1,h2{color:#1f4e78}'
        '.kpi{display:flex;gap:16px;flex-wrap:wrap}.card{padding:12px 18px;background:#f4f7fb;border:1px solid #d7e1ec;border-radius:10px}'
        'table{border-collapse:collapse;width:100%;margin:12px 0 28px}th,td{border-bottom:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}'
        'th{background:#1f4e78;color:white;position:sticky;top:0}tr:nth-child(even){background:#fafafa}a{color:#1769aa;text-decoration:none}'
        '.note{background:#fff4ce;padding:12px;border-radius:8px}</style></head><body>'
        '<h1>SNS Creative GitHub TOP50</h1>'
        f'<div class="kpi"><div class="card"><b>Candidates</b><br>{summary["candidate_count"]}</div>'
        f'<div class="card"><b>Metadata OK</b><br>{summary["metadata_ok"]}</div>'
        f'<div class="card"><b>Eligible</b><br>{summary["eligible_original_active"]}</div>'
        f'<div class="card"><b>Top50</b><br>{summary["top50_stars_count"]}</div></div>'
        '<p class="note">Stars Rank는 순수 GitHub Stars 기준입니다. Recommended Rank는 Stars 40% + SNS 직접성 25% + 활성도 10% + 자동화 10% + AI/프롬프트 10% + 라이선스 5%입니다.</p>'
        '<h2>Stars TOP50</h2>'+table(stars50,'stars_rank')+
        '<h2>Recommended TOP50</h2>'+table(rec50,'recommended_rank')+
        '</body></html>'
    )
    (HERE/'social_top50_report.html').write_text(html_text,encoding='utf-8')

def main():
    rows=list(csv.DictReader(open(CAND,encoding='utf-8-sig')))
    token=get_token()
    print(f'Candidates: {len(rows)} | Authenticated: {bool(token)}')
    refreshed=[]
    for i,r in enumerate(rows,1):
        print(f'[{i}/{len(rows)}] {r["repo"]}')
        data,err=fetch_repo(r['repo'],token)
        rr=dict(r)
        if data:
            rr.update({
                'stars':int(data.get('stargazers_count') or 0),
                'fork':bool(data.get('fork')),
                'archived':bool(data.get('archived')),
                'license_spdx':((data.get('license') or {}).get('spdx_id') or 'UNKNOWN'),
                'language':data.get('language') or '',
                'updated_at':data.get('updated_at') or '',
                'pushed_at':data.get('pushed_at') or '',
                'metadata_status':'ok',
            })
        else:
            rr['metadata_status']='error:'+str(err)
            rr['stars']=0; rr['fork']=''; rr['archived']=''; rr['license_spdx']='UNKNOWN'
        refreshed.append(rr)
        time.sleep(0.05)

    eligible=[r for r in refreshed if r['metadata_status']=='ok' and not bool(r['fork']) and not bool(r['archived'])]
    eligible.sort(key=lambda r:int(r['stars']),reverse=True)
    for idx,r in enumerate(eligible,1): r['stars_rank']=idx
    maxlog=max([math.log10(int(r['stars'])+1) for r in eligible] or [1])
    for r in eligible:
        stars_component=(math.log10(int(r['stars'])+1)/maxlog)*40.0
        direct=(float(r['sns_directness_score'])/100.0)*25.0
        act=activity_score(r.get('pushed_at',''),bool(r.get('archived')))
        auto=automation_score(r['category'])
        ai=ai_prompt_score(r['category'])
        lic=license_score(r.get('license_spdx',''))
        r['recommended_score']=round(stars_component+direct+act+auto+ai+lic,2)
    rec=sorted(eligible,key=lambda r:(float(r.get('recommended_score') or 0),int(r['stars'])),reverse=True)
    for idx,r in enumerate(rec,1): r['recommended_rank']=idx

    # propagate ranks to all refreshed rows
    byrepo={r['repo']:r for r in eligible}
    for r in refreshed:
        if r['repo'] in byrepo:
            r.update({k:byrepo[r['repo']].get(k,'') for k in ['stars_rank','recommended_score','recommended_rank']})
        else:
            r['stars_rank']='';r['recommended_score']='';r['recommended_rank']=''

    all_sorted=sorted(refreshed,key=lambda r:(r['metadata_status']!='ok',-int(r.get('stars') or 0)))
    stars50=eligible[:50]
    rec50=rec[:50]
    write_csv(OUT_ALL,all_sorted);write_csv(OUT_STARS,stars50);write_csv(OUT_REC,rec50)
    build_sqlite(all_sorted,stars50,rec50)
    summary={
        'generated_at':datetime.now().isoformat(timespec='seconds'),
        'candidate_count':len(refreshed),'metadata_ok':sum(r['metadata_status']=='ok' for r in refreshed),
        'eligible_original_active':len(eligible),'errors':sum(r['metadata_status']!='ok' for r in refreshed),
        'top50_stars_count':len(stars50),'top50_recommended_count':len(rec50),
        'authenticated_github':bool(token),
        'top10_stars':[{'repo':r['repo'],'stars':r['stars'],'category':r['category']} for r in stars50[:10]],
        'top10_recommended':[{'repo':r['repo'],'score':r['recommended_score'],'stars':r['stars']} for r in rec50[:10]],
    }
    OUT_JSON.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if len(stars50)<50:
        print('WARNING: fewer than 50 eligible repos. Add candidates or inspect errors.',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
