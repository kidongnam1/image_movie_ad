import argparse, sqlite3, re
ap=argparse.ArgumentParser(description='Recommend best indexed prompts using text relevance + quality + model fit + source trust.')
ap.add_argument('query')
ap.add_argument('--db',default='AI_PROMPT_LIBRARY/indexes/prompt_library.sqlite')
ap.add_argument('--media',choices=['image','video'])
ap.add_argument('--model')
ap.add_argument('--use-case',dest='use_case')
ap.add_argument('--tag')
ap.add_argument('--min-quality',type=int,default=55)
ap.add_argument('--limit',type=int,default=10)
a=ap.parse_args(); con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; cur=con.cursor()
where=['p.combined_score>=?']; params=[a.min_quality]
if a.media: where.append('p.media_type=?'); params.append(a.media)
if a.model: where.append('(p.model_family LIKE ? OR p.model_guess LIKE ?)'); params += [f'%{a.model}%',f'%{a.model}%']
if a.use_case: where.append('(p.use_case LIKE ? OR p.auto_tags LIKE ?)'); params += [f'%{a.use_case}%',f'%{a.use_case}%']
if a.tag: where.append('p.auto_tags LIKE ?'); params.append(f'%{a.tag}%')
base=' AND '.join(where)
terms=[t.lower() for t in re.findall(r'[\w-]+',a.query) if len(t)>1]
rows=[]
if a.query!='*':
    # FTS first. Quote individual terms so ordinary user text does not need FTS syntax knowledge.
    fts_query=' AND '.join('"'+t.replace('"','')+'"' for t in terms) if terms else a.query
    try:
        rows=cur.execute('SELECT p.* FROM prompts_fts f JOIN prompts p ON p.id=f.rowid WHERE prompts_fts MATCH ? AND '+base+' LIMIT 250',[fts_query]+params).fetchall()
    except sqlite3.OperationalError:
        rows=[]
if not rows:
    if a.query=='*' or not terms:
        rows=cur.execute('SELECT p.* FROM prompts p WHERE '+base+' LIMIT 250',params).fetchall()
    else:
        term_sql=[]; term_params=[]
        for t in terms:
            term_sql.append('(p.title LIKE ? OR p.prompt LIKE ? OR p.auto_tags LIKE ?)')
            q=f'%{t}%'; term_params += [q,q,q]
        rows=cur.execute('SELECT p.* FROM prompts p WHERE '+' AND '.join(term_sql)+' AND '+base+' LIMIT 250',term_params+params).fetchall()
def rank(r):
    text=((r['title'] or '')+' '+(r['prompt'] or '')+' '+(r['auto_tags'] or '')).lower()
    lexical=min(20,sum(4 for t in terms if t in text))
    trust=8 if r['origin_status']=='verified_original' else 4 if r['origin_status']=='probable_original' else 0
    corpus=4 if r['source_kind']=='corpus' else 0
    exact_model=8 if a.model and (a.model.lower() in (r['model_family'] or '').lower() or a.model.lower() in (r['model_guess'] or '').lower()) else 0
    exact_use=5 if a.use_case and a.use_case.lower() in ((r['use_case'] or '')+' '+(r['auto_tags'] or '')).lower() else 0
    return round(r['combined_score']*.55+r['model_fit_score']*.20+r['repo_quality_score']*.10+lexical+trust+corpus+exact_model+exact_use,2)
ranked=sorted(((rank(r),r) for r in rows),key=lambda x:x[0],reverse=True)[:a.limit]
if not ranked:
    print('No matching prompts. Try fewer keywords, remove --model/--use-case filters, or lower --min-quality.')
for i,(s,r) in enumerate(ranked,1):
    print(f'\n[{i}] RECOMMEND={s:.1f} | Q={r["combined_score"]} FIT={r["model_fit_score"]} | {r["media_type"]} / {r["model_family"]}')
    print('REPO:',r['repo'],'| ORIGIN:',r['origin_status'],'| TAGS:',r['auto_tags'] or '-')
    print('TITLE:',(r['title'] or '')[:220])
    print('PROMPT:',(r['prompt'] or '')[:1800])
con.close()
