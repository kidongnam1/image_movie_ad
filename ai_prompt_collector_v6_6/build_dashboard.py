from __future__ import annotations
import argparse, csv, html, json
from pathlib import Path
from collections import Counter
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='AI_PROMPT_LIBRARY'); a=ap.parse_args(); root=Path(a.root).resolve(); idx=root/'indexes'; logs=root/'logs'
def jc(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except:return d
def cc(p):
    if not p.exists(): return []
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
summary=jc(idx/'summary.json',{}); post=jc(logs/'postflight.json',{}); models=cc(idx/'model_summary.csv'); repos=cc(idx/'repo_index.csv'); tops=cc(idx/'top_prompts_by_model.csv'); overlaps=cc(idx/'repo_overlap_report.csv'); near=cc(idx/'near_duplicate_report.csv')
def esc(x):return html.escape(str(x or ''))
def num(x):
    try:return f'{int(float(x)):,}'
    except:return esc(x)
failed=[r for r in repos if str(r.get('downloaded')).upper()!='Y']
model_rows=''.join(f'<tr><td>{esc(r.get("model_family"))}</td><td>{esc(r.get("media_type"))}</td><td>{num(r.get("unique_prompts"))}</td><td>{esc(r.get("avg_combined_score"))}</td><td>{esc(r.get("avg_model_fit"))}</td></tr>' for r in sorted(models,key=lambda x:int(float(x.get('unique_prompts') or 0)),reverse=True))
top_rows=''.join(f'<tr><td>{esc(r.get("model_family"))}</td><td>{esc(r.get("quality_tier"))}</td><td>{esc(r.get("combined_score"))}</td><td>{esc(r.get("repo"))}</td><td class="prompt">{esc((r.get("prompt") or "")[:420])}</td></tr>' for r in tops[:150])
fail_rows=''.join(f'<tr><td>{esc(r.get("repo"))}</td><td>{esc(r.get("model_family"))}</td><td>{esc(r.get("local_path"))}</td></tr>' for r in failed[:100]) or '<tr><td colspan="3">None</td></tr>'
html_doc=f'''<!doctype html><html><head><meta charset="utf-8"><title>AI Prompt Library v6</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f6f8fb;color:#172033}}h1{{margin-bottom:4px}}.muted{{color:#667085}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:20px 0}}.card{{background:white;border:1px solid #e3e8ef;border-radius:12px;padding:16px;box-shadow:0 1px 2px #00000008}}.k{{font-size:12px;color:#667085}}.v{{font-size:28px;font-weight:700;margin-top:5px}}table{{border-collapse:collapse;width:100%;background:white;margin:12px 0 28px}}th,td{{border-bottom:1px solid #e8edf3;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef4fb;position:sticky;top:0}}.prompt{{max-width:760px}}input{{padding:10px;width:min(560px,90%);border:1px solid #ccd5e0;border-radius:8px}}.warn{{color:#a15c00}}.bad{{color:#b42318}}.ok{{color:#027a48}}</style></head><body>
<h1>AI Prompt Library v6</h1><div class="muted">Local collection dashboard. Search applies to the Top Prompts table below.</div>
<div class="grid">
<div class="card"><div class="k">Selected repos</div><div class="v">{num(summary.get('repos_selected',post.get('selected_repos',0)))}</div></div>
<div class="card"><div class="k">Downloaded repos</div><div class="v">{num(post.get('downloaded_repos',0))}</div></div>
<div class="card"><div class="k">Unique prompts</div><div class="v">{num(summary.get('unique_prompts',0))}</div></div>
<div class="card"><div class="k">Raw records</div><div class="v">{num(summary.get('raw_records',0))}</div></div>
<div class="card"><div class="k">Exact dup groups</div><div class="v">{num(summary.get('duplicate_prompt_groups',0))}</div></div>
<div class="card"><div class="k">Near-dup review</div><div class="v">{num(summary.get('near_duplicate_review_pairs',len(near)))}</div></div>
<div class="card"><div class="k">Repo overlap pairs</div><div class="v">{num(summary.get('heavy_repo_overlap_pairs',len(overlaps)))}</div></div>
</div>
<h2>Model coverage after indexing</h2><table><thead><tr><th>Model</th><th>Media</th><th>Unique prompts</th><th>Avg quality</th><th>Avg model fit</th></tr></thead><tbody>{model_rows}</tbody></table>
<h2>Repositories not downloaded</h2><table><thead><tr><th>Repository</th><th>Model</th><th>Expected local path</th></tr></thead><tbody>{fail_rows}</tbody></table>
<h2>Top prompts</h2><input id="q" placeholder="Search model, repo, title or prompt..." oninput="filterRows()"><table id="prompts"><thead><tr><th>Model</th><th>Tier</th><th>Score</th><th>Repo</th><th>Prompt preview</th></tr></thead><tbody>{top_rows}</tbody></table>
<script>function filterRows(){{let q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('#prompts tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none')}};</script>
</body></html>'''
(root/'dashboard.html').write_text(html_doc,encoding='utf-8')
print(root/'dashboard.html')
