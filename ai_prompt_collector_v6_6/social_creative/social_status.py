from __future__ import annotations
import csv, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIB=HERE/'SOCIAL_CREATIVE_LIBRARY'

def count_csv(p):
    if not p.exists(): return 0
    with open(p,encoding='utf-8-sig',newline='') as f: return sum(1 for _ in csv.DictReader(f))

def main():
    stars=count_csv(HERE/'social_top50_stars.csv')
    rec=count_csv(HERE/'social_top50_recommended.csv')
    repos=LIB/'repos'
    downloaded=sum(1 for p in repos.iterdir() if p.is_dir() and (p/'.git').exists()) if repos.exists() else 0
    summary={}
    sp=LIB/'logs'/'download_summary_stars.json'
    if sp.exists():
        try: summary=json.loads(sp.read_text(encoding='utf-8'))
        except Exception: pass
    print('='*64)
    print('SNS CREATIVE TOP50 STATUS')
    print('='*64)
    print('Stars TOP50 indexed      :',stars)
    print('Recommended TOP50 indexed:',rec)
    print('Repositories downloaded  :',downloaded)
    if summary:
        print('Last download success    :',summary.get('success'))
        print('Last download failed     :',summary.get('failed'))
        if summary.get('failed_repos'):
            print('Failed repos             :',', '.join(summary['failed_repos']))
    print('Catalog DB exists        :',(HERE/'social_creative_catalog.sqlite').exists())
    print('HTML report exists       :',(HERE/'social_top50_report.html').exists())
    print('='*64)
    return 0
if __name__=='__main__': raise SystemExit(main())
