import csv, sqlite3, re
from pathlib import Path
base=Path(__file__).parent
rows=list(csv.DictReader(open(base/'repos_manifest.csv',encoding='utf-8-sig')))
db=base/'repo_catalog.sqlite'
if db.exists(): db.unlink()
con=sqlite3.connect(db); cur=con.cursor()
cols=list(rows[0].keys()) if rows else []
def sql_name(c):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',c): raise ValueError(c)
    return c
cur.execute('CREATE TABLE repos(id INTEGER PRIMARY KEY,'+','.join(sql_name(c)+' TEXT' for c in cols)+')')
cur.executemany('INSERT INTO repos('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',[tuple(r.get(c,'') for c in cols) for r in rows])
fts_cols=[c for c in ['repo','model_family','specialization','use_case','notes','verification_note','license_spdx'] if c in cols]
try:
    cur.execute("CREATE VIRTUAL TABLE repos_fts USING fts5("+','.join(fts_cols)+",content='repos',content_rowid='id')")
    cur.execute("INSERT INTO repos_fts(rowid,"+','.join(fts_cols)+") SELECT id,"+','.join(fts_cols)+" FROM repos")
except sqlite3.OperationalError: pass
for c in ['media_type','model_family','origin_status','source_kind','license_spdx']:
    if c in cols: cur.execute(f'CREATE INDEX ix_repos_{c} ON repos({c})')
con.commit(); con.close(); print(db)
