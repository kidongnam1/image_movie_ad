from __future__ import annotations
import argparse, csv, math
from pathlib import Path
import pandas as pd

def norm_repo(s):
    return str(s).strip().removesuffix(".git")

def read_overlap(path: Path):
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    # tolerate many column names
    cands = {c.lower(): c for c in df.columns}
    a_col = next((cands[k] for k in cands if k in {"repo_a","repo1","repo_1","left_repo"}), None)
    b_col = next((cands[k] for k in cands if k in {"repo_b","repo2","repo_2","right_repo"}), None)
    o_col = next((cands[k] for k in cands if "overlap" in k or "jaccard" in k or "similarity" in k), None)
    if not (a_col and b_col and o_col):
        return {}
    out = {}
    for _,r in df.iterrows():
        try: ov=float(r[o_col])
        except: continue
        if ov > 1: ov /= 100.0
        a,b=norm_repo(r[a_col]),norm_repo(r[b_col])
        out[(a,b)] = ov
        out[(b,a)] = ov
    return out

def classify(manifest_path: Path, overlap_path: Path|None, outdir: Path, core_target=25):
    df=pd.read_csv(manifest_path)
    df=df[df["active"]==True].copy()
    overlap=read_overlap(overlap_path) if overlap_path else {}

    def b(v):
        if pd.isna(v): return 0
        return int(str(v).lower() in {"true","1","yes"} or v is True)
    def txt(r):
        return (str(r.get("specialization",""))+"|"+str(r.get("use_case",""))).lower()

    def score(r):
        s=float(r.get("repo_quality_score",0) or 0)*0.55
        s+=float(r.get("origin_confidence",0) or 0)*10
        s+=5*b(r.get("verified_fork_false"))
        lic=str(r.get("license_spdx","")).upper()
        s+=5 if lic in {"MIT","APACHE-2.0","BSD-3-CLAUSE","BSD-2-CLAUSE","ISC","CC0-1.0"} else 0
        role=str(r.get("source_role","")).lower()
        s+=4 if role=="primary" else 2 if role in {"specialized","supplemental"} else 0
        u=txt(r)
        s+=7 if any(k in u for k in ("product","advert","commercial","ugc","creator","ecommerce","cinematic","camera","storyboard")) else 0
        p=int(r.get("priority",3) or 3)
        s+=4 if p==1 else 2 if p==2 else 0
        return s
    df["audit_score"]=df.apply(score,axis=1)

    # Greedy diversity selection. Penalize high overlap with already selected repos.
    selected=[]
    family_counts={}
    media_counts={"image":0,"video":0}
    candidates=df.sort_values("audit_score",ascending=False).to_dict("records")
    while candidates and len(selected)<core_target:
        best_i=None; best_eff=-999
        for i,r in enumerate(candidates):
            repo=norm_repo(r["repo"])
            fam=str(r.get("model_family",""))
            media=str(r.get("media_type",""))
            eff=float(r["audit_score"])
            # diversity bonus for new model family and balance image/video
            if family_counts.get(fam,0)==0: eff+=8
            elif family_counts.get(fam,0)>=2: eff-=6
            if media=="image" and media_counts["image"]>=13: eff-=8
            if media=="video" and media_counts["video"]>=12: eff-=8
            # exact corpus-overlap penalty if report exists
            maxov=0
            for s in selected:
                maxov=max(maxov, overlap.get((repo,norm_repo(s["repo"])),0))
            if maxov>=0.85: eff-=30
            elif maxov>=0.70: eff-=15
            elif maxov>=0.50: eff-=6
            # business fit bonus
            u=txt(r)
            if any(k in u for k in ("product","advert","commercial","ugc","creator","ecommerce")): eff+=5
            if eff>best_eff:
                best_eff=eff; best_i=i
        r=candidates.pop(best_i)
        r["effective_score"]=best_eff
        selected.append(r)
        family_counts[str(r.get("model_family",""))]=family_counts.get(str(r.get("model_family","")),0)+1
        media_counts[str(r.get("media_type",""))]=media_counts.get(str(r.get("media_type","")),0)+1

    core=set(norm_repo(x["repo"]) for x in selected)
    df["class_v2"]=df["repo"].map(lambda x:"CORE" if norm_repo(x) in core else "")
    rem=df[df["class_v2"]==""].sort_values("audit_score",ascending=False)
    ext=set(rem.head(max(0,min(23,len(rem))))["repo"].map(norm_repo))
    df.loc[df["repo"].map(norm_repo).isin(ext),"class_v2"]="EXTENDED"
    df.loc[df["class_v2"]=="","class_v2"]="ARCHIVE"

    outdir.mkdir(parents=True,exist_ok=True)
    df.to_csv(outdir/"prompt_repo_reclassification_FINAL.csv",index=False,encoding="utf-8-sig")
    for label,name in [("CORE","CORE_25_FINAL.csv"),("EXTENDED","EXTENDED_FINAL.csv"),("ARCHIVE","ARCHIVE_FINAL.csv")]:
        df[df["class_v2"]==label].sort_values("audit_score",ascending=False).to_csv(outdir/name,index=False,encoding="utf-8-sig")
    print("FINAL:", df["class_v2"].value_counts().to_dict())
    print("Overlap report:", overlap_path if overlap else "not available - metadata/diversity mode")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--overlap")
    ap.add_argument("--outdir",default="prompt_core/final")
    a=ap.parse_args()
    classify(Path(a.manifest),Path(a.overlap) if a.overlap else None,Path(a.outdir))
