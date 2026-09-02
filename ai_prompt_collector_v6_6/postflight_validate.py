from __future__ import annotations
import argparse, csv, json, sqlite3
from pathlib import Path
from datetime import datetime
from collections import Counter

ap=argparse.ArgumentParser(description='Validate collected prompt library and write a shareable report.')
ap.add_argument('--root',default='AI_PROMPT_LIBRARY')
a=ap.parse_args(); root=Path(a.root).resolve(); idx=root/'indexes'; logs=root/'logs'
issues=[]; warnings=[]
def read_csv(path):
    if not path.exists(): return []
    with open(path,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def get_json(path,default=None):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {} if default is None else default
summary=get_json(idx/'summary.json',{})
repos=read_csv(idx/'repo_index.csv'); prompts=read_csv(idx/'prompt_records.csv'); models=read_csv(idx/'model_summary.csv')
overlap=read_csv(idx/'repo_overlap_report.csv'); near=read_csv(idx/'near_duplicate_report.csv')
clones=get_json(logs/'clone_status.json',[])
if not summary: issues.append('indexes/summary.json is missing or invalid.')
if not prompts: issues.append('No prompt records were produced.')
unique=len(prompts)
if summary and int(summary.get('unique_prompts',-1))!=unique: issues.append(f"summary unique_prompts={summary.get('unique_prompts')} but CSV has {unique} rows")
db=idx/'prompt_library.sqlite'; db_count=None
if db.exists():
    try:
        con=sqlite3.connect(db); db_count=con.execute('select count(*) from prompts').fetchone()[0]; con.close()
        if db_count!=unique: issues.append(f'SQLite prompt count {db_count} != CSV unique prompts {unique}')
    except Exception as e: issues.append(f'SQLite validation failed: {e}')
else: issues.append('prompt_library.sqlite is missing.')
failed=[x for x in clones if x.get('status') in {'clone_failed','update_failed','exists_non_git','sparse_checkout_failed'}]
if failed: warnings.append(f'{len(failed)} repositories failed clone/update or are non-git.')
missing=[r for r in repos if str(r.get('downloaded')).upper()!='Y']
if missing: warnings.append(f'{len(missing)} selected repositories were not downloaded.')
license_counts=Counter((r.get('license_spdx') or 'UNKNOWN') for r in prompts)
tiers=Counter((r.get('quality_tier') or '') for r in prompts)
media=Counter((r.get('media_type') or '') for r in prompts)
model_counts=Counter((r.get('model_family') or '') for r in prompts)
report={
 'version':'6.0','checked_at':datetime.now().isoformat(timespec='seconds'),'root':str(root),
 'critical_issues':issues,'warnings':warnings,'selected_repos':len(repos),'downloaded_repos':sum(str(r.get('downloaded')).upper()=='Y' for r in repos),
 'failed_clone_or_update':len(failed),'prompt_files':int(summary.get('prompt_files',0) or 0),'raw_records':int(summary.get('raw_records',0) or 0),
 'unique_prompts':unique,'sqlite_prompts':db_count,'exact_duplicate_groups':int(summary.get('duplicate_prompt_groups',0) or 0),
 'near_duplicate_review_pairs':len(near),'heavy_overlap_pairs':len(overlap),'media_counts':dict(media),'quality_tiers':dict(tiers),
 'top_models':model_counts.most_common(20),'license_counts':dict(license_counts)
}
(logs/'postflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# AI Prompt Collector v6 — Postflight Report','',f'- Checked: {report["checked_at"]}',f'- Selected repositories: **{report["selected_repos"]}**',f'- Downloaded repositories: **{report["downloaded_repos"]}**',f'- Prompt files scanned: **{report["prompt_files"]}**',f'- Raw records: **{report["raw_records"]}**',f'- Unique prompts after exact dedupe: **{unique}**',f'- Exact duplicate groups: **{report["exact_duplicate_groups"]}**',f'- Near-duplicate review pairs: **{len(near)}**',f'- Heavy repo-overlap pairs: **{len(overlap)}**','']
md += ['## Critical issues'] + (['- None'] if not issues else [f'- {x}' for x in issues]) + ['','## Warnings'] + (['- None'] if not warnings else [f'- {x}' for x in warnings])
md += ['','## Top model families'] + [f'- {m}: {n}' for m,n in model_counts.most_common(15)]
md += ['','## License labels in indexed records'] + [f'- {k}: {v}' for k,v in license_counts.most_common()]
(logs/'POSTFLIGHT_REPORT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print('\n'.join(md[:24]))
if issues: raise SystemExit(2)
