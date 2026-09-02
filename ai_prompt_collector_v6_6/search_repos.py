import argparse, sqlite3
from pathlib import Path
ap=argparse.ArgumentParser(description='Search repository catalog before/after download')
ap.add_argument('query',nargs='?',default='*')
ap.add_argument('--db',default=str(Path(__file__).with_name('repo_catalog.sqlite')))
ap.add_argument('--media',choices=['image','video'])
ap.add_argument('--model')
ap.add_argument('--source-kind',choices=['corpus','tooling','watchlist'])
ap.add_argument('--origin-status')
ap.add_argument('--license')
ap.add_argument('--verified-license-only',action='store_true')
ap.add_argument('--max-priority',type=int,default=3)
ap.add_argument('--limit',type=int,default=30)
a=ap.parse_args(); con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; cur=con.cursor()
where=['CAST(r.priority AS INTEGER)<=?']; params=[a.max_priority]
if a.media: where.append('r.media_type=?'); params.append(a.media)
if a.model: where.append('r.model_family LIKE ?'); params.append(f'%{a.model}%')
if a.source_kind: where.append('r.source_kind=?'); params.append(a.source_kind)
if a.origin_status: where.append('r.origin_status=?'); params.append(a.origin_status)
if a.license: where.append('r.license_spdx LIKE ?'); params.append(f'%{a.license}%')
if a.verified_license_only: where.append('LOWER(r.license_verified)=?'); params.append('true')
base=' AND '.join(where)
rows=[]
try:
    if a.query!='*': rows=cur.execute('SELECT r.* FROM repos_fts f JOIN repos r ON r.id=f.rowid WHERE repos_fts MATCH ? AND '+base+' ORDER BY CAST(r.repo_quality_score AS INTEGER) DESC LIMIT ?',[a.query]+params+[a.limit]).fetchall()
    else: rows=cur.execute('SELECT r.* FROM repos r WHERE '+base+' ORDER BY CAST(r.repo_quality_score AS INTEGER) DESC LIMIT ?',params+[a.limit]).fetchall()
except sqlite3.OperationalError:
    q=f'%{a.query}%'; rows=cur.execute('SELECT r.* FROM repos r WHERE (r.repo LIKE ? OR r.specialization LIKE ? OR r.use_case LIKE ?) AND '+base+' ORDER BY CAST(r.repo_quality_score AS INTEGER) DESC LIMIT ?',[q,q,q]+params+[a.limit]).fetchall()
for i,r in enumerate(rows,1):
    print(f'[{i}] {r["repo_quality_score"]} {r["tier"]} | {r["media_type"]} | {r["model_family"]} | {r["source_kind"]} | {r["origin_status"]}')
    print('   ',r['repo'])
    print('    USE:',r['use_case'],'| SPEC:',r['specialization'])
    if 'license_spdx' in r.keys(): print('    LICENSE:',r['license_spdx'],'| LICENSE VERIFIED:',r['license_verified'] or '-')
    if 'prompt_count_verified' in r.keys() and (r['prompt_count_verified'] or r['prompt_count_claimed']): print('    PROMPTS:',r['prompt_count_verified'] or '?','verified /',r['prompt_count_claimed'] or '?','claimed')
    print('    ',r['url'])
con.close()
