from pathlib import Path
from collections import Counter
import csv, json, sys
ROOT=Path(__file__).parent
rows=list(csv.DictReader(open(ROOT/'repos_manifest.csv',encoding='utf-8-sig')))
required=['active','origin_status','origin_confidence','verified_fork_false','media_type','model_family','repo','url','priority','tier','repo_quality_score','source_role','specialization','use_case','verification_note','notes','source_kind','license_spdx','license_verified','verified_at','prompt_count_claimed','prompt_count_verified','content_structure_verified','evidence_url']
errors=[]; warnings=[]
valid_origin={'verified_original','probable_original','candidate','duplicate_excluded'}
valid_kind={'corpus','tooling','watchlist'}
seen={}
for i,r in enumerate(rows,2):
    for k in required:
        if k not in r: errors.append(f'row {i}: missing column {k}')
    repo=r.get('repo','').strip()
    if not repo: errors.append(f'row {i}: empty repo')
    if repo in seen: errors.append(f'row {i}: duplicate repo {repo} (first row {seen[repo]})')
    seen[repo]=i
    if r.get('origin_status') not in valid_origin: errors.append(f'row {i}: invalid origin_status {r.get("origin_status")}')
    if r.get('source_kind') not in valid_kind: errors.append(f'row {i}: invalid source_kind {r.get("source_kind")}')
    if r.get('media_type') not in {'image','video'}: errors.append(f'row {i}: invalid media_type {r.get("media_type")}')
    try:
        q=int(float(r.get('repo_quality_score') or 0))
        if not 0<=q<=100: errors.append(f'row {i}: repo_quality_score out of range')
    except: errors.append(f'row {i}: invalid repo_quality_score')
    try:
        c=float(r.get('origin_confidence') or 0)
        if not 0<=c<=1: errors.append(f'row {i}: origin_confidence out of range')
    except: errors.append(f'row {i}: invalid origin_confidence')
    if r.get('origin_status')=='verified_original' and str(r.get('verified_fork_false')).lower()!='true': warnings.append(f'row {i}: verified_original without verified_fork_false=true: {repo}')
    if r.get('origin_status') in {'candidate','duplicate_excluded'} and str(r.get('active')).lower()=='true': warnings.append(f'row {i}: candidate/duplicate marked active: {repo}')
    if str(r.get('license_verified')).lower()=='true' and not (r.get('license_spdx') or '').strip(): errors.append(f'row {i}: license_verified=true but empty license_spdx: {repo}')
    if str(r.get('license_verified')).lower()=='true' and (r.get('license_spdx') or '').strip().upper()=='UNKNOWN': errors.append(f'row {i}: license_verified=true cannot use UNKNOWN: {repo}')
    if r.get('origin_status')=='verified_original' and not (r.get('verified_at') or '').strip(): warnings.append(f'row {i}: verified_original without verified_at: {repo}')
    if str(r.get('verified_fork_false')).lower()=='true' and not (r.get('evidence_url') or '').strip(): warnings.append(f'row {i}: verified_fork_false=true without evidence_url: {repo}')
    va=(r.get('verified_at') or '').strip()
    if va and (len(va)!=10 or va[4]!='-' or va[7]!='-'): errors.append(f'row {i}: invalid verified_at date format: {repo} -> {va}')
    for fld in ('prompt_count_claimed','prompt_count_verified'):
        v=(r.get(fld) or '').strip()
        if v:
            try:
                if int(float(v)) < 0: errors.append(f'row {i}: {fld} cannot be negative: {repo}')
            except: errors.append(f'row {i}: invalid {fld}: {repo} -> {v}')
summary={'rows':len(rows),'errors':len(errors),'warnings':len(warnings),'origin_counts':dict(Counter(r['origin_status'] for r in rows)),'source_kind_counts':dict(Counter(r['source_kind'] for r in rows)),'model_families':len(set(r['model_family'] for r in rows))}
print(json.dumps(summary,ensure_ascii=False,indent=2))
if warnings:
    print('\nWARNINGS:'); [print('-',x) for x in warnings]
if errors:
    print('\nERRORS:'); [print('-',x) for x in errors]; sys.exit(1)
print('\nPASS: manifest is structurally valid.')
