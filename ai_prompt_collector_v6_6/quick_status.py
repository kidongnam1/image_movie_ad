from pathlib import Path
import json, csv, argparse
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='AI_PROMPT_LIBRARY'); a=ap.parse_args(); root=Path(a.root).resolve()
base=Path(__file__).parent
try: manifest=json.loads((base/'research_status_v6.json').read_text(encoding='utf-8'))
except: manifest={}
try: summary=json.loads((root/'indexes'/'summary.json').read_text(encoding='utf-8'))
except: summary={}
try: post=json.loads((root/'logs'/'postflight.json').read_text(encoding='utf-8'))
except: post={}
print('AI Prompt Collector v6 - STATUS')
print('='*52)
print(f"Manifest: {manifest.get('manifest_total','?')} repos | active {manifest.get('active_total','?')} | corpus {manifest.get('active_corpus','?')} | tooling {manifest.get('active_tooling','?')}")
if summary:
    print(f"Last collection: selected {summary.get('repos_selected',0)} | downloaded {summary.get('repos_downloaded',0)} | unique prompts {summary.get('unique_prompts',0):,}")
    print(f"Duplicates: exact groups {summary.get('duplicate_prompt_groups',0):,} | near review {summary.get('near_duplicate_review_pairs',0):,} | repo overlap {summary.get('heavy_repo_overlap_pairs',0):,}")
    print(f"Mode: text-only={summary.get('text_only_clone',False)} | candidates={summary.get('include_candidates',False)} | tooling={summary.get('include_tooling',False)}")
else:
    print('No collection result yet. Run START_HERE.bat or run_corpus_auto.bat.')
if post:
    print(f"Postflight: critical issues {len(post.get('critical_issues',[]))} | warnings {len(post.get('warnings',[]))}")
print('Root:',root)
