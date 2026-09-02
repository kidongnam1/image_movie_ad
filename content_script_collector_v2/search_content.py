import argparse, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DB=ROOT/"database/content_script.sqlite"

TABLES = {
  "hook": ("viral_hooks","hook_formula"),
  "script": ("short_form_scripts","spoken_template"),
  "cta": ("ctas","cta_template"),
  "before_after": ("before_after_patterns","spoken_template"),
  "demo": ("product_demo_patterns","spoken_template"),
  "testimonial": ("testimonial_patterns","spoken_template"),
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--type", choices=["all",*TABLES], default="all")
    ap.add_argument("--limit", type=int, default=20)
    a=ap.parse_args()
    conn=sqlite3.connect(DB)
    targets=TABLES.items() if a.type=="all" else [(a.type,TABLES[a.type])]
    out=[]
    for label,(table,col) in targets:
        rows=conn.execute(f"""SELECT {col}, quality_score FROM {table}
                             WHERE {col} LIKE ? ORDER BY quality_score DESC LIMIT ?""",
                          (f"%{a.query}%",a.limit)).fetchall()
        out.extend((label,*r) for r in rows)
    for label,text,score in sorted(out,key=lambda x:x[2] or 0, reverse=True)[:a.limit]:
        print(f"[{label}] score={score}\n{text[:500]}\n")
    conn.close()
if __name__=="__main__": main()
