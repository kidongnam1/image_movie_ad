from __future__ import annotations
import argparse,csv,sqlite3
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROMPT_DB=HERE/'AI_PROMPT_LIBRARY'/'indexes'/'prompt_library.sqlite'
SOCIAL=HERE/'social_creative'/'social_top50_recommended.csv'

def search_prompts(q,limit=10):
    if not PROMPT_DB.exists(): return []
    con=sqlite3.connect(PROMPT_DB); con.row_factory=sqlite3.Row
    terms=[t for t in q.split() if t]
    rows=[]
    try:
        match=' AND '.join('"'+t.replace('"','')+'"' for t in terms)
        rows=con.execute('SELECT p.* FROM prompts_fts f JOIN prompts p ON p.id=f.rowid WHERE prompts_fts MATCH ? ORDER BY p.combined_score DESC LIMIT ?', (match,limit)).fetchall()
    except Exception:
        like='%'+q+'%'
        try: rows=con.execute('SELECT * FROM prompts WHERE prompt LIKE ? OR title LIKE ? ORDER BY combined_score DESC LIMIT ?', (like,like,limit)).fetchall()
        except Exception: rows=[]
    con.close(); return [dict(r) for r in rows]

def search_social(q,limit=10):
    if not SOCIAL.exists(): return []
    rows=list(csv.DictReader(open(SOCIAL,encoding='utf-8-sig')));out=[];ql=q.lower()
    for r in rows:
        hay=' '.join([r.get('repo',''),r.get('category',''),r.get('capability',''),r.get('sns_use_case','')]).lower()
        if all(t.lower() in hay for t in q.split()): out.append(r)
    return out[:limit]

def main():
    ap=argparse.ArgumentParser(description='Search both prompt library and social creative repo catalog.')
    ap.add_argument('query');ap.add_argument('--limit',type=int,default=10);a=ap.parse_args()
    print('\n=== PROMPT LIBRARY ===')
    ps=search_prompts(a.query,a.limit)
    if not ps: print('(no prompt DB result)')
    for i,r in enumerate(ps,1): print(f'{i}. [{r.get("model_family","-")}] {str(r.get("prompt",""))[:180]}')
    print('\n=== SOCIAL CREATIVE REPOS ===')
    ss=search_social(a.query,a.limit)
    if not ss: print('(run social_creative/REFRESH_SOCIAL_TOP50.bat first, or no match)')
    for i,r in enumerate(ss,1): print(f'{i}. ★{int(r.get("stars") or 0):,} {r.get("repo")} | {r.get("category")} | {r.get("capability")}')
if __name__=='__main__':main()
