from pathlib import Path
from collections import Counter, defaultdict
import csv, json, subprocess, sys

ROOT=Path(__file__).parent
MASTER=ROOT/'repos_manifest.csv'
FIELDS=None

def read_rows():
    with open(MASTER,encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); global FIELDS; FIELDS=r.fieldnames; return list(r)

def truthy(v): return str(v).strip().lower() in {'1','true','yes','y'}

def write_csv(name,rows,fields=None):
    fields=fields or FIELDS or (list(rows[0]) if rows else [])
    with open(ROOT/name,'w',newline='',encoding='utf-8-sig') as f:
        if not fields: return
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    rows=read_rows()
    active=[r for r in rows if truthy(r.get('active')) and r.get('origin_status') not in {'candidate','duplicate_excluded'}]
    corpus=[r for r in active if r.get('source_kind')=='corpus']
    tooling=[r for r in active if r.get('source_kind')=='tooling']
    watch=[r for r in rows if r.get('origin_status')=='candidate' or r.get('source_kind')=='watchlist']
    dup=[r for r in rows if r.get('origin_status')=='duplicate_excluded']
    write_csv('active_originals.csv',active)
    write_csv('active_corpus.csv',corpus)
    write_csv('active_tooling.csv',tooling)
    write_csv('candidate_watchlist.csv',watch)
    write_csv('duplicate_excluded.csv',dup)
    verified=[r for r in rows if r.get('origin_status')=='verified_original']
    write_csv('verified_originals.csv',verified)
    license_counts=Counter((r.get('license_spdx') or 'UNKNOWN') for r in rows)
    license_rows=[]
    for lic,count in sorted(license_counts.items(),key=lambda x:(-x[1],x[0])):
        lic_group=[r for r in rows if (r.get('license_spdx') or 'UNKNOWN')==lic]
        license_rows.append({'license_spdx':lic,'repos':count,'verified_license_rows':sum(str(r.get('license_verified')).lower()=='true' for r in lic_group),'active_repos':sum(r in active for r in lic_group),'repo_names':' | '.join(r['repo'] for r in lic_group)[:30000]})
    write_csv('license_summary.csv',license_rows,list(license_rows[0]) if license_rows else [])

    # model coverage
    groups=defaultdict(list)
    for r in rows: groups[(r['media_type'],r['model_family'])].append(r)
    cov=[]
    for (media,model),grp in sorted(groups.items()):
        active_grp=[r for r in grp if r in active]
        cov.append({
            'media_type':media,'model_family':model,
            'total_repos':len(grp),'active_repos':len(active_grp),
            'corpus_repos':sum(r.get('source_kind')=='corpus' and r in active for r in grp),
            'tooling_repos':sum(r.get('source_kind')=='tooling' and r in active for r in grp),
            'verified_originals':sum(r.get('origin_status')=='verified_original' for r in grp),
            'probable_originals':sum(r.get('origin_status')=='probable_original' for r in grp),
            'candidates':sum(r.get('origin_status')=='candidate' for r in grp),
            'best_repo_quality':max([int(float(r.get('repo_quality_score') or 0)) for r in grp] or [0]),
            'repos':' | '.join(r['repo'] for r in active_grp)[:30000],
        })
    write_csv('model_coverage_matrix.csv',cov,list(cov[0]) if cov else [])

    status={
        'version':'6.0', 'manifest_total':len(rows), 'active_total':len(active),
        'active_corpus':len(corpus), 'active_tooling':len(tooling),
        'watchlist_rows':len(watch), 'duplicate_excluded':len(dup),
        'origin_status_counts':dict(Counter(r.get('origin_status') for r in rows)),
        'media_counts_all':dict(Counter(r.get('media_type') for r in rows)),
        'media_counts_active':dict(Counter(r.get('media_type') for r in active)),
        'source_kind_counts':dict(Counter(r.get('source_kind') for r in rows)),
        'model_families':len(set(r.get('model_family') for r in rows)),
    }
    (ROOT/'research_status_v6.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'repos_manifest.json').write_text(json.dumps({'version':'6.0','repos':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    # refresh repo sqlite if builder exists
    builder=ROOT/'build_repo_catalog.py'
    if builder.exists(): subprocess.run([sys.executable,str(builder)],check=True)
    print(json.dumps(status,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
