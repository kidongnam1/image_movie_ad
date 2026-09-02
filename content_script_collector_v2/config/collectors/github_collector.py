from __future__ import annotations
import argparse, base64, fnmatch, hashlib, json, os, sqlite3, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "repositories.yaml"
SOURCES = ROOT / "sources"
LOGS = ROOT / "logs"
DB = ROOT / "database" / "content_script.sqlite"

sys.path.insert(0, str(ROOT))
from classifiers.license_classifier import classify_license

API = "https://api.github.com"
TEXT_EXT = {".md",".txt",".json",".jsonl",".yaml",".yml",".csv",".tsv",".py",".js",".ts"}

def log(msg: str):
    print(msg)
    LOGS.mkdir(exist_ok=True)
    with (LOGS/"collector.log").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")

def headers():
    h = {"Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token: h["Authorization"] = f"Bearer {token}"
    return h

def gh_get(url):
    r = requests.get(url, headers=headers(), timeout=30)
    r.raise_for_status()
    return r.json()

def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

def wanted(path: str, patterns: list[str]) -> bool:
    p = path.replace("\\","/")
    return any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(p, pat.replace("/**","/*")) for pat in patterns)

def init_db():
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript((ROOT/"database/schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    return conn

def collect_repo(item, conn):
    owner, repo = item["repo"].split("/",1)
    meta = gh_get(f"{API}/repos/{owner}/{repo}")
    branch = meta.get("default_branch","main")
    tree = gh_get(f"{API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    sha = tree.get("sha") or ""
    repo_dir = SOURCES / owner / repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    license_spdx = ((meta.get("license") or {}).get("spdx_id") or item.get("license_expected") or "UNKNOWN")
    decision = classify_license(license_spdx, item.get("usage_class"))
    retrieved_at = datetime.now(timezone.utc).isoformat()

    count = 0
    candidates = []
    for node in tree.get("tree",[]):
        path = node.get("path","")
        if node.get("type") != "blob":
            continue
        if Path(path).suffix.lower() not in TEXT_EXT and "LICENSE" not in Path(path).name.upper():
            continue
        if not wanted(path, item.get("collect", [])):
            continue
        candidates.append(node)

    log(f"START {item['repo']} candidate_files={len(candidates)} stars={meta.get('stargazers_count')} license={license_spdx} usage={decision.usage_class}")

    for idx, node in enumerate(candidates, 1):
        path = node.get("path","")
        print(f"  [{idx}/{len(candidates)}] {path}", flush=True)
        try:
            blob = gh_get(node["url"])
            raw = base64.b64decode(blob.get("content","")).decode("utf-8", errors="ignore")
        except Exception as e:
            log(f"WARN {item['repo']} {path}: {e}")
            continue
        dest = repo_dir / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(raw, encoding="utf-8")
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        conn.execute("""
        INSERT OR IGNORE INTO sources
        (repo_owner,repo_name,github_url,file_path,license_spdx,usage_class,
         attribution_required,share_alike,noncommercial_only,stars,last_commit,
         retrieved_at,source_commit_sha,sha256)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(owner,repo,item["url"],path,license_spdx,decision.usage_class,
             int(decision.attribution_required),int(decision.share_alike),
             int(decision.noncommercial_only),meta.get("stargazers_count"),
             meta.get("pushed_at"),retrieved_at,sha,digest))
        count += 1

    conn.commit()
    log(f"OK {item['repo']} files={count} stars={meta.get('stargazers_count')} license={license_spdx} usage={decision.usage_class}")
    return count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="Only one config id or owner/repo")
    args = ap.parse_args()
    cfg = load_config()
    conn = init_db()
    total = 0
    selected=[item for item in cfg["repositories"] if not args.repo or args.repo in {item["id"], item["repo"]}]
    for pos, item in enumerate(selected, 1):
        print(f"\n[{pos}/{len(selected)}] {item['repo']}", flush=True)
        try:
            total += collect_repo(item, conn)
        except Exception as e:
            log(f"ERROR {item['repo']}: {type(e).__name__}: {e}")
    log(f"DONE files={total} db={DB}")
    conn.close()

if __name__ == "__main__":
    main()
