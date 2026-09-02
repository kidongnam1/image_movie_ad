from __future__ import annotations
import csv, sqlite3, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from parsers.markdown_parser import extract_candidates
from classifiers.claim_classifier import claim_risk
from dedupe.semantic_dedupe import exact_key, formula_family

DB = ROOT/"database/content_script.sqlite"
INDEX = ROOT/"indexes"

def quality(text: str) -> float:
    score = 50
    n = len(text)
    if 80 <= n <= 2500: score += 15
    if any(x in text.lower() for x in ("hook","cta","shot","spoken","before","after","demo","testimonial")): score += 20
    if "[" in text or "{" in text: score += 5
    if n > 8000: score -= 15
    return max(0,min(100,score))

def source_map(conn):
    rows = conn.execute("SELECT source_id,repo_owner,repo_name,file_path,usage_class FROM sources").fetchall()
    return {(r[1],r[2],r[3]): r for r in rows}

def insert_candidate(conn, source_id, cat, text):
    q = quality(text)
    risk = claim_risk(text)
    if cat == "viral_hook":
        conn.execute("""INSERT INTO viral_hooks
          (hook_category,hook_formula,example_normalized,commercial_safe,claim_risk,formula_family,quality_score,source_id)
          VALUES (?,?,?,?,?,?,?,?)""",
          ("auto",text[:2000],text[:2000],int(risk in ("LOW","MEDIUM")),risk,formula_family(text),q,source_id))
    elif cat == "short_form_script":
        conn.execute("""INSERT INTO short_form_scripts
          (framework_name,spoken_template,quality_score,source_id) VALUES (?,?,?,?)""",
          ("auto_extracted",text[:6000],q,source_id))
    elif cat == "cta":
        conn.execute("""INSERT INTO ctas
          (cta_type,goal,cta_template,quality_score,source_id) VALUES (?,?,?,?,?)""",
          ("auto","conversion",text[:2000],q,source_id))
    elif cat == "before_after":
        conn.execute("""INSERT INTO before_after_patterns
          (spoken_template,claim_risk,quality_score,source_id) VALUES (?,?,?,?)""",
          (text[:4000],risk,q,source_id))
    elif cat == "product_demo":
        conn.execute("""INSERT INTO product_demo_patterns
          (demo_type,spoken_template,quality_score,source_id) VALUES (?,?,?,?)""",
          ("auto",text[:4000],q,source_id))
    elif cat == "testimonial":
        conn.execute("""INSERT INTO testimonial_patterns
          (testimonial_type,spoken_template,claim_risk,quality_score,source_id) VALUES (?,?,?,?,?)""",
          ("auto",text[:4000],risk,q,source_id))

def export_table(conn, table):
    INDEX.mkdir(exist_ok=True)
    cur = conn.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    with (INDEX/f"{table}.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(cols); w.writerows(cur.fetchall())

def main():
    conn=sqlite3.connect(DB)
    src = source_map(conn)
    seen=set()
    for p in (ROOT/"sources").rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md",".txt"}: continue
        rel=p.relative_to(ROOT/"sources")
        if len(rel.parts)<3: continue
        owner, repo = rel.parts[0], rel.parts[1]
        file_path="/".join(rel.parts[2:])
        srow=src.get((owner,repo,file_path))
        if not srow: continue
        source_id,_,_,_,usage=srow
        if usage in {"BLOCKED","UNKNOWN"}: continue
        for cand in extract_candidates(p):
            for cat in cand["categories"]:
                text=cand["text"]
                key=(cat,exact_key(text))
                if key in seen: continue
                seen.add(key)
                insert_candidate(conn,source_id,cat,text)
    conn.commit()
    for t in ["viral_hooks","short_form_scripts","ctas","before_after_patterns","product_demo_patterns","testimonial_patterns","sources"]:
        export_table(conn,t)
    conn.close()
    print(f"Built indexes in {INDEX}")

if __name__=="__main__":
    main()
