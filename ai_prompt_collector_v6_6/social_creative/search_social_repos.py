from __future__ import annotations
import argparse,csv
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('query',nargs='?',default='*')
    ap.add_argument('--rank',choices=['stars','recommended'],default='recommended')
    ap.add_argument('--category')
    ap.add_argument('--min-stars',type=int,default=0)
    ap.add_argument('--limit',type=int,default=20)
    a=ap.parse_args()
    path=HERE/('social_top50_stars.csv' if a.rank=='stars' else 'social_top50_recommended.csv')
    if not path.exists():
        raise SystemExit('Run refresh_social_top50.py first.')
    rows=list(csv.DictReader(open(path,encoding='utf-8-sig')))
    q=a.query.lower().strip()
    out=[]
    for r in rows:
        if int(r.get('stars') or 0)<a.min_stars: continue
        if a.category and a.category.lower() not in r.get('category','').lower(): continue
        hay=' '.join([r.get('repo',''),r.get('category',''),r.get('capability',''),r.get('sns_use_case','')]).lower()
        if q!='*' and q not in hay: continue
        out.append(r)
    for r in out[:a.limit]:
        rank=r.get('recommended_rank') if a.rank=='recommended' else r.get('stars_rank')
        print(f'#{rank:>2}  ★{int(r.get("stars") or 0):>7,}  {r["repo"]}')
        print(f'     {r["category"]} | {r["capability"]}')
        print(f'     use: {r["sns_use_case"]} | license={r.get("license_spdx") or "UNKNOWN"}')

if __name__=='__main__': main()
