from __future__ import annotations
import argparse, json, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CR_RE = re.compile(r"CR-[A-Z0-9]{8,20}", re.I)
REGISTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS creative_registry (
  creative_id TEXT PRIMARY KEY,
  product TEXT NOT NULL,
  category TEXT,
  angle TEXT,
  angle_label TEXT,
  hook_text TEXT,
  selling_point TEXT,
  script_version TEXT,
  experiment_slot TEXT,
  source_project TEXT,
  registered_at TEXT NOT NULL,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_registry_product ON creative_registry(product);
CREATE INDEX IF NOT EXISTS idx_registry_category_angle ON creative_registry(category, angle);
"""

def ensure_registry(conn: sqlite3.Connection) -> None:
    conn.executescript(REGISTRY_SCHEMA)

def extract_creative_id(*values: Any) -> str:
    for value in values:
        m = CR_RE.search(str(value or ""))
        if m:
            return m.group(0).upper()
    return ""

def register_candidates(conn: sqlite3.Connection, data: dict[str, Any], source_project: str = "") -> int:
    ensure_registry(conn)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    candidates = data.get("experiment_plan", {}).get("candidates", [])
    product = data.get("product", "")
    category = data.get("product_analysis", {}).get("category", "")
    version = str(data.get("version", "2.7"))
    n = 0
    for c in candidates:
        cid = str(c.get("creative_id", "")).upper().strip()
        if not cid:
            continue
        payload = json.dumps(c, ensure_ascii=False)
        conn.execute(
            """INSERT INTO creative_registry(creative_id,product,category,angle,angle_label,hook_text,selling_point,script_version,experiment_slot,source_project,registered_at,metadata_json)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(creative_id) DO UPDATE SET product=excluded.product,category=excluded.category,angle=excluded.angle,
               angle_label=excluded.angle_label,hook_text=excluded.hook_text,selling_point=excluded.selling_point,
               script_version=excluded.script_version,experiment_slot=excluded.experiment_slot,source_project=excluded.source_project,
               registered_at=excluded.registered_at,metadata_json=excluded.metadata_json""",
            (cid, product, category, c.get("angle", ""), c.get("angle_label", ""), c.get("hook", ""),
             c.get("selling_point", ""), version, c.get("slot", ""), source_project, now, payload),
        )
        n += 1
    conn.commit()
    return n

def lookup(conn: sqlite3.Connection, creative_id: str) -> dict[str, Any] | None:
    ensure_registry(conn)
    row = conn.execute("SELECT * FROM creative_registry WHERE creative_id=?", (creative_id.upper(),)).fetchone()
    return dict(row) if row else None

def list_registry(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_registry(conn)
    return [dict(r) for r in conn.execute("SELECT * FROM creative_registry ORDER BY registered_at DESC, creative_id")]

def register_file(plan_path: str | Path, db_path: str | Path) -> dict[str, Any]:
    path=Path(plan_path); data=json.loads(path.read_text(encoding="utf-8-sig"))
    if "experiment_plan" not in data:
        data={"version":data.get("version","2.7"),"product":data.get("product",data.get("product_name","")),"product_analysis":data.get("product_analysis",{}),"experiment_plan":data}
    conn=sqlite3.connect(db_path);conn.row_factory=sqlite3.Row;count=register_candidates(conn,data,source_project=str(path));total=conn.execute("SELECT COUNT(*) FROM creative_registry").fetchone()[0];conn.close()
    return {"source":str(path),"registered":count,"registry_rows":total}

def parse_args():
    p=argparse.ArgumentParser(description="V2.7 creative registry");p.add_argument("plan");p.add_argument("--db",required=True);return p.parse_args()
def main():
    a=parse_args();print(json.dumps(register_file(a.plan,a.db),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
