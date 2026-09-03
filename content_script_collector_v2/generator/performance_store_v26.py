from __future__ import annotations

import argparse, csv, hashlib, json, math, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB=Path(__file__).resolve().parents[1]/"database/ad_performance.sqlite"
ANGLE_NAMES=("problem_attack","loss_aversion","curiosity","comparison","contrarian","discovery","proof")
NUMERIC_FIELDS=("impressions","video_starts","views_2s","views_3s","clicks","detail_views","purchases","revenue","spend")
TEMPLATE_FIELDS=("observed_at","campaign_id","creative_id","product","category","platform","angle","hook_text","selling_point","impressions","video_starts","views_2s","views_3s","clicks","detail_views","purchases","revenue","spend")
IDENTITY_FIELDS=("observed_at","campaign_id","creative_id","product","category","platform","angle","hook_text","selling_point")

SCHEMA="""
CREATE TABLE IF NOT EXISTS performance_events (
 performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
 row_fingerprint TEXT NOT NULL UNIQUE,
 observed_at TEXT,campaign_id TEXT,creative_id TEXT,product TEXT NOT NULL,category TEXT,platform TEXT,
 angle TEXT,hook_text TEXT,selling_point TEXT,
 impressions INTEGER NOT NULL DEFAULT 0,video_starts INTEGER NOT NULL DEFAULT 0,views_2s INTEGER NOT NULL DEFAULT 0,
 views_3s INTEGER NOT NULL DEFAULT 0,clicks INTEGER NOT NULL DEFAULT 0,detail_views INTEGER NOT NULL DEFAULT 0,
 purchases INTEGER NOT NULL DEFAULT 0,revenue REAL NOT NULL DEFAULT 0,spend REAL NOT NULL DEFAULT 0,
 source_file TEXT,imported_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_perf_category_angle ON performance_events(category,angle);
CREATE INDEX IF NOT EXISTS idx_perf_creative ON performance_events(creative_id);
CREATE INDEX IF NOT EXISTS idx_perf_product ON performance_events(product);
"""

def connect(db_path: str|Path|None=None)->sqlite3.Connection:
 p=Path(db_path or DEFAULT_DB);p.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(p);c.row_factory=sqlite3.Row;c.executescript(SCHEMA);return c

def _int(v): return 0 if v in (None,"") else int(float(str(v).replace(",","").strip()))
def _float(v): return 0.0 if v in (None,"") else float(str(v).replace(",","").strip())

def normalize_row(row:dict[str,Any])->dict[str,Any]:
 out={k:str(row.get(k,"") or "").strip() for k in TEMPLATE_FIELDS}
 if not out["product"]: raise ValueError("product is required")
 a=out["angle"].lower()
 if a and a not in ANGLE_NAMES: raise ValueError(f"unsupported angle: {a}")
 out["angle"]=a
 for k in NUMERIC_FIELDS:
  out[k]=_float(row.get(k)) if k in {"revenue","spend"} else _int(row.get(k))
  if out[k]<0: raise ValueError(f"{k} must be >= 0")
 imp=out["impressions"]
 for k in ("video_starts","views_2s","views_3s","clicks","detail_views","purchases"):
  if imp and out[k]>imp: raise ValueError(f"{k} cannot exceed impressions")
 if out["views_3s"]>out["views_2s"] and out["views_2s"]>0: raise ValueError("views_3s cannot exceed views_2s")
 return out

def row_fingerprint(row:dict[str,Any])->str:
 # Identity excludes metrics. Re-importing a refreshed cumulative snapshot updates the existing row instead of double-counting it.
 payload="|".join(str(row.get(k,"")) for k in IDENTITY_FIELDS)
 return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _csv_rows(p:Path):
 with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def _json_rows(p:Path):
 d=json.loads(p.read_text(encoding="utf-8-sig"));d=d.get("rows",d.get("performance",[d])) if isinstance(d,dict) else d
 if not isinstance(d,list):raise ValueError("JSON must contain a list of performance rows")
 return [dict(x) for x in d]
def _xlsx_rows(p:Path):
 try:from openpyxl import load_workbook
 except ImportError as e:raise RuntimeError("XLSX import requires openpyxl. Run: pip install openpyxl") from e
 wb=load_workbook(p,read_only=True,data_only=True);ws=wb[wb.sheetnames[0]];it=ws.iter_rows(values_only=True)
 try:headers=[str(x or "").strip() for x in next(it)]
 except StopIteration:return []
 return [{headers[i]:v for i,v in enumerate(r) if i<len(headers)} for r in it]
def read_rows(path:str|Path):
 p=Path(path);e=p.suffix.lower()
 if e==".csv":return _csv_rows(p)
 if e==".json":return _json_rows(p)
 if e in {".xlsx",".xlsm"}:return _xlsx_rows(p)
 raise ValueError("supported performance files: .csv, .json, .xlsx, .xlsm")

def _same_metrics(old:sqlite3.Row,row:dict[str,Any])->bool:
 return all(float(old[k] or 0)==float(row[k] or 0) for k in NUMERIC_FIELDS)

def import_file(path:str|Path,db_path:str|Path|None=None)->dict[str,Any]:
 p=Path(path);rows=read_rows(p);c=connect(db_path);inserted=updated=skipped=errors=0;bad=[];now=datetime.now(timezone.utc).isoformat(timespec="seconds")
 insert_sql="""INSERT INTO performance_events(row_fingerprint,observed_at,campaign_id,creative_id,product,category,platform,angle,hook_text,selling_point,impressions,video_starts,views_2s,views_3s,clicks,detail_views,purchases,revenue,spend,source_file,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
 update_sql="""UPDATE performance_events SET impressions=?,video_starts=?,views_2s=?,views_3s=?,clicks=?,detail_views=?,purchases=?,revenue=?,spend=?,source_file=?,imported_at=? WHERE row_fingerprint=?"""
 for idx,raw in enumerate(rows,start=2):
  try:
   r=normalize_row(raw);fp=row_fingerprint(r);old=c.execute("SELECT * FROM performance_events WHERE row_fingerprint=?",(fp,)).fetchone()
   if old and _same_metrics(old,r): skipped+=1;continue
   if old:
    c.execute(update_sql,(r["impressions"],r["video_starts"],r["views_2s"],r["views_3s"],r["clicks"],r["detail_views"],r["purchases"],r["revenue"],r["spend"],p.name,now,fp));updated+=1
   else:
    c.execute(insert_sql,(fp,r["observed_at"],r["campaign_id"],r["creative_id"],r["product"],r["category"],r["platform"],r["angle"],r["hook_text"],r["selling_point"],r["impressions"],r["video_starts"],r["views_2s"],r["views_3s"],r["clicks"],r["detail_views"],r["purchases"],r["revenue"],r["spend"],p.name,now));inserted+=1
  except Exception as e:errors+=1;bad.append({"row":idx,"error":str(e)})
 c.commit();total=c.execute("SELECT COUNT(*) FROM performance_events").fetchone()[0];c.close()
 return {"source":str(p),"inserted":inserted,"updated":updated,"duplicates_skipped":skipped,"errors":errors,"error_rows":bad[:20],"database_rows":total}

def create_template(path:str|Path)->Path:
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("w",encoding="utf-8-sig",newline="") as f:csv.writer(f).writerow(TEMPLATE_FIELDS)
 return p

def _aggregate(rows:Iterable[sqlite3.Row|dict[str,Any]]):
 s={k:0.0 for k in NUMERIC_FIELDS};n=0
 for r in rows:
  n+=1
  for k in NUMERIC_FIELDS:s[k]+=float(r[k] or 0)
 s["rows"]=float(n);return s
def _rate(n,d):return n/d if d>0 else 0.0
def _metrics(a):
 imp=a["impressions"];clk=a["clicks"];sp=a["spend"]
 return {"impressions":imp,"rows":a.get("rows",0.0),"retention_2s":_rate(a["views_2s"],imp),"retention_3s":_rate(a["views_3s"],imp),"ctr":_rate(clk,imp),"detail_view_rate":_rate(a["detail_views"],imp),"purchase_cvr":_rate(a["purchases"],clk),"purchase_rate":_rate(a["purchases"],imp),"roas":_rate(a["revenue"],sp)}
def _smooth(s,d,prior,strength):return prior if d<=0 else (s+prior*strength)/(d+strength)
def _lift(v,b,clip=.60):return 0.0 if b<=0 else max(-clip,min(clip,v/b-1.0))
def _adjust(a,base):
 imp=a["impressions"];clk=a["clicks"];r2=_smooth(a["views_2s"],imp,base["retention_2s"],600);r3=_smooth(a["views_3s"],imp,base["retention_3s"],600);ctr=_smooth(clk,imp,base["ctr"],800);detail=_smooth(a["detail_views"],imp,base["detail_view_rate"],800);cvr=_smooth(a["purchases"],clk,base["purchase_cvr"],80);roas=_metrics(a)["roas"] if a["spend"]>0 else base["roas"]
 lift=_lift(r2,base["retention_2s"])*.20+_lift(r3,base["retention_3s"])*.10+_lift(ctr,base["ctr"])*.25+_lift(detail,base["detail_view_rate"])*.10+_lift(cvr,base["purchase_cvr"])*.25+_lift(roas,base["roas"])*.10
 conf=1.0-math.exp(-imp/2000.0)
 if imp<200:conf*=imp/200.0
 adj=max(-6.0,min(6.0,lift*12.0*conf))
 return round(adj,2),{"retention_2s":round(r2,6),"retention_3s":round(r3,6),"ctr":round(ctr,6),"detail_view_rate":round(detail,6),"purchase_cvr":round(cvr,6),"roas":round(roas,4),"confidence":round(conf,4),"impressions":int(imp)}

def build_learning_profile(category:str="",db_path:str|Path|None=None)->dict[str,Any]:
 c=connect(db_path);rows=c.execute("SELECT * FROM performance_events").fetchall()
 if not rows:c.close();return {"active":False,"reason":"no performance data","total_rows":0,"total_impressions":0,"category":category,"baselines":{},"angle_adjustments":{a:0.0 for a in ANGLE_NAMES},"angle_details":{},"hook_adjustments":{},"creative_adjustments":{}}
 allagg=_aggregate(rows);base=_metrics(allagg);adj={};details={}
 for angle in ANGLE_NAMES:
  gr=[r for r in rows if (r["angle"] or "")==angle];cr=[r for r in gr if category and (r["category"] or "")==category];ga=_aggregate(gr);gadj,gdet=_adjust(ga,base) if gr else (0.0,{})
  if cr:
   ca=_aggregate(cr);cadj,cdet=_adjust(ca,base);cc=1.0-math.exp(-ca["impressions"]/1500.0);x=cadj*cc+gadj*(1.0-cc)*.5;details[angle]={"category":cdet,"global":gdet,"category_blend":round(cc,4)}
  else:x=gadj*.5;details[angle]={"category":None,"global":gdet,"category_blend":0.0}
  adj[angle]=round(max(-6,min(6,x)),2)
 def directs(field,max_bonus):
  groups={}
  for r in rows:
   k=str(r[field] or "").strip()
   if k:groups.setdefault(k,[]).append(r)
  out={}
  for k,rs in groups.items():
   a=_aggregate(rs)
   if a["impressions"]<200:out[k]=0.0;continue
   x,_=_adjust(a,base);out[k]=round(max(-max_bonus,min(max_bonus,x*(max_bonus/6.0))),2)
  return out
 hooks=directs("hook_text",3.0);creatives=directs("creative_id",2.0);c.close()
 return {"active":True,"reason":"performance data available","category":category,"total_rows":int(allagg["rows"]),"total_impressions":int(allagg["impressions"]),"baselines":{k:round(v,6) if isinstance(v,float) else v for k,v in base.items()},"angle_adjustments":adj,"angle_details":details,"hook_adjustments":hooks,"creative_adjustments":creatives,"weights":{"retention_2s":.20,"retention_3s":.10,"ctr":.25,"detail_view_rate":.10,"purchase_cvr":.25,"roas":.10},"max_adjustment":6.0,"max_hook_adjustment":3.0,"max_creative_adjustment":2.0}

def creative_id(product:str,category:str,angle:str,hook_text:str)->str:
 return "CR-"+hashlib.sha1(f"v26|{product}|{category}|{angle}|{hook_text}".encode("utf-8")).hexdigest()[:12].upper()
def report(db_path:str|Path|None=None,category:str=""):return build_learning_profile(category,db_path)
def parse_args():
 ap=argparse.ArgumentParser(description="V2.6 ad performance learning store");sub=ap.add_subparsers(dest="cmd",required=True)
 p=sub.add_parser("init-db");p.add_argument("--db",default=str(DEFAULT_DB));p=sub.add_parser("template");p.add_argument("--out",default="ad_performance_template.csv");p=sub.add_parser("import");p.add_argument("file");p.add_argument("--db",default=str(DEFAULT_DB));p=sub.add_parser("report");p.add_argument("--db",default=str(DEFAULT_DB));p.add_argument("--category",default="");return ap.parse_args()
def main():
 a=parse_args()
 if a.cmd=="init-db":c=connect(a.db);c.close();print("DB_READY=",a.db);return 0
 if a.cmd=="template":print("TEMPLATE=",create_template(a.out));return 0
 if a.cmd=="import":print(json.dumps(import_file(a.file,a.db),ensure_ascii=False,indent=2));return 0
 if a.cmd=="report":print(json.dumps(report(a.db,a.category),ensure_ascii=False,indent=2));return 0
 return 1
if __name__=="__main__":raise SystemExit(main())
