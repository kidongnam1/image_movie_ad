import sqlite3, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"database/content_script.sqlite"
OUT=ROOT/"reports/collection_report.html"

def main():
    conn=sqlite3.connect(DB)
    tables=["viral_hooks","short_form_scripts","ctas","before_after_patterns","product_demo_patterns","testimonial_patterns"]
    counts={t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    sources=conn.execute("""SELECT repo_owner||'/'||repo_name, usage_class, MAX(stars), COUNT(*)
                            FROM sources GROUP BY repo_owner,repo_name,usage_class ORDER BY MAX(stars) DESC""").fetchall()
    rows="".join(f"<tr><td>{html.escape(r)}</td><td>{u}</td><td>{s or 0}</td><td>{c}</td></tr>" for r,u,s,c in sources)
    cards="".join(f"<div class='card'><b>{t}</b><br><span>{n}</span></div>" for t,n in counts.items())
    doc=f"""<!doctype html><meta charset='utf-8'><title>Content Script Collector V1</title>
    <style>body{{font-family:Arial,sans-serif;margin:32px;max-width:1100px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
    .card{{border:1px solid #ddd;border-radius:12px;padding:18px}}.card span{{font-size:30px}}table{{border-collapse:collapse;width:100%;margin-top:24px}}
    td,th{{border-bottom:1px solid #ddd;padding:9px;text-align:left}}</style>
    <h1>Content / Script Collector V1</h1><div class='grid'>{cards}</div>
    <h2>Sources</h2><table><tr><th>Repository</th><th>Usage</th><th>Stars</th><th>Files</th></tr>{rows}</table>"""
    OUT.write_text(doc,encoding="utf-8")
    print(OUT)
if __name__=="__main__": main()
