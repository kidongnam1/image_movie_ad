from __future__ import annotations
import argparse, json, re, sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"database/content_script.sqlite"

HOOK_PATTERNS = {
"problem":"{product}을 써도 원하는 느낌이 안 나는 이유, 혹시 이것 때문일까요?",
"mistake":"{product}, 아직도 이렇게 사용하고 계신가요?",
"curiosity":"많은 분이 놓치는 {product} 사용 포인트가 하나 있습니다.",
"comparison":"비싼 {product}보다 먼저 확인해야 할 건 따로 있습니다.",
"pattern_interrupt":"잠깐, {product} 바르기 전에 이것부터 확인해보세요.",
"question":"왜 어떤 날은 {product}를 발라도 사용감이 다르게 느껴질까요?",
"specificity":"{product} 사용할 때 가장 먼저 볼 3가지를 알려드릴게요.",
"routine":"아침 {product} 루틴, 순서 하나만 바꿔도 사용감이 달라질 수 있습니다.",
"texture":"{product} 고를 때 성분표만큼 중요한 게 바로 이 사용감입니다.",
"soft_contrarian":"{product}는 많이 바른다고 꼭 더 좋은 건 아닙니다.",
"demo":"이 {product} 제형, 손등에서 먼저 보여드릴게요.",
"before_after_safe":"메이크업 전에 {product}를 쓰는 방식, 이렇게 비교해보세요.",
"authority_safe":"{product}를 고를 때 광고 문구보다 먼저 확인할 기준이 있습니다.",
"fear_safe":"{product}를 아무 생각 없이 고르면 내 피부에 안 맞을 수 있습니다.",
"social_proof":"요즘 {product} 후기에서 반복해서 나오는 포인트가 있습니다.",
}
FALLBACK_ORDER=list(HOOK_PATTERNS)

CTA_PATTERNS = {
"save":"비슷한 고민이 있다면 저장해두고 다음 루틴 때 비교해보세요.",
"learn_more":"더 자세한 사용법은 제품 페이지에서 확인해보세요.",
"comment":"어떤 사용감이 좋은지 댓글로 남겨보세요.",
"safety":"사용 전 제품 설명과 주의사항을 먼저 확인해보세요.",
"check":"내 피부에 맞는 사용법인지 제품 정보를 확인해보세요.",
}

@dataclass
class Hook:
    rank:int
    text:str
    category:str
    score:float
    scroll_stop:float
    curiosity:float
    relevance:float
    clarity:float
    differentiation:float
    risk:float
    db_source_id:int|None=None
    db_hook_id:int|None=None

def risk_score(text):
    t=text.lower()
    bad=["치료","완치","없애","사라","100%","즉시 효과","주름 제거","여드름 치료"]
    return 0 if not any(x in t for x in bad) else 60

def score_hook(text,cat,product,quality_bonus=0):
    n=len(text)
    scroll=92 if cat in {"mistake","pattern_interrupt","question","problem"} else 82
    curiosity=94 if cat in {"curiosity","problem","question","comparison"} else 78
    relevance=98 if product in text else 80
    clarity=94 if n<=45 else 86 if n<=60 else 74
    diff=90 if cat in {"soft_contrarian","specificity","texture","comparison"} else 80
    risk=risk_score(text)
    total=scroll*.25+curiosity*.20+relevance*.20+clarity*.15+diff*.10+(100-risk)*.10
    total=min(100,total+quality_bonus)
    return round(total,1),(scroll,curiosity,relevance,clarity,diff,risk)

def open_db():
    if not DB.exists():
        return None
    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    return conn

def table_counts(conn):
    out={}
    for t in ["sources","viral_hooks","short_form_scripts","ctas","before_after_patterns","product_demo_patterns","testimonial_patterns"]:
        try: out[t]=conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception: out[t]=0
    return out

def allowed_clause(alias="s"):
    # RESEARCH_ONLY/BLOCKED/UNKNOWN must not directly drive commercial copy.
    return f"{alias}.usage_class IN ('COMMERCIAL_OK','TRANSFORM_ONLY')"

def infer_hook_category(text):
    t=(text or "").lower()
    rules=[
      ("before_after_safe",["before","after","transformation","비포","애프터"]),
      ("comparison",["compare","comparison","versus","vs ","비교"]),
      ("question",["question","why ","what if","왜 ","?"]),
      ("problem",["problem","pain","frustrat","문제","고민"]),
      ("social_proof",["social proof","testimonial","review","후기"]),
      ("mistake",["mistake","wrong","실수","잘못"]),
      ("curiosity",["curiosity","secret","mystery","unknown","궁금","비밀"]),
      ("pattern_interrupt",["stop","wait","잠깐"]),
      ("specificity",["numbered","list","3 ","5 ","가지"]),
      ("soft_contrarian",["contrarian","myth","reframe","반대","오해"]),
      ("demo",["demo","show","product","시연"]),
      ("routine",["routine","루틴"]),
      ("texture",["texture","제형"]),
    ]
    for cat,words in rules:
        if any(w in t for w in words): return cat
    return "curiosity"

def db_hook_signals(conn, limit=60):
    rows=conn.execute(f"""
      SELECT h.hook_id,h.source_id,h.hook_category,h.hook_formula,h.formula_family,h.quality_score,
             h.claim_risk,s.usage_class
      FROM viral_hooks h JOIN sources s ON s.source_id=h.source_id
      WHERE {allowed_clause('s')} AND COALESCE(h.claim_risk,'LOW') NOT IN ('HIGH','PROHIBITED')
      ORDER BY h.quality_score DESC,h.hook_id ASC LIMIT ?
    """,(limit,)).fetchall()
    signals=[]
    for r in rows:
        raw=" ".join(str(r[k] or "") for k in ("hook_category","hook_formula","formula_family"))
        signals.append({
          "hook_id":r["hook_id"],"source_id":r["source_id"],
          "category":infer_hook_category(raw),
          "quality":float(r["quality_score"] or 0),
          "usage_class":r["usage_class"]
        })
    return signals

def db_best(conn, table, fields, risk_field=None, limit=5):
    risk_cond=""
    if risk_field:
        risk_cond=f" AND COALESCE(t.{risk_field},'LOW') NOT IN ('HIGH','PROHIBITED')"
    cols=",".join("t."+f for f in fields)
    rows=conn.execute(f"""
      SELECT t.rowid as row_id,t.source_id,t.quality_score,{cols},s.usage_class
      FROM {table} t JOIN sources s ON s.source_id=t.source_id
      WHERE {allowed_clause('s')} {risk_cond}
      ORDER BY t.quality_score DESC,t.rowid ASC LIMIT ?
    """,(limit,)).fetchall()
    return [dict(r) for r in rows]

def db_context():
    conn=open_db()
    if not conn:
        return {"connected":False,"reason":"DB file not found","counts":{},"hook_signals":[]}
    counts=table_counts(conn)
    connected=counts.get("viral_hooks",0)>0
    ctx={"connected":connected,"counts":counts}
    if connected:
        ctx["hook_signals"]=db_hook_signals(conn)
        ctx["scripts"]=db_best(conn,"short_form_scripts",["framework_name"],limit=3)
        ctx["ctas"]=db_best(conn,"ctas",["cta_type","goal"],limit=5)
        ctx["before_after"]=db_best(conn,"before_after_patterns",["transition_pattern"],risk_field="claim_risk",limit=3)
        ctx["product_demo"]=db_best(conn,"product_demo_patterns",["demo_type","camera_pattern"],limit=3)
        ctx["testimonial"]=db_best(conn,"testimonial_patterns",["testimonial_type","proof_level"],risk_field="claim_risk",limit=3)
    conn.close()
    return ctx

def generate_hooks(product, ctx, n=30):
    signals=ctx.get("hook_signals",[]) if ctx.get("connected") else []
    if signals:
        cats=[]
        seen=set()
        for s in signals:
            c=s["category"]
            if c not in seen:
                cats.append((c,s));seen.add(c)
        for c in FALLBACK_ORDER:
            if c not in seen: cats.append((c,None))
    else:
        cats=[(c,None) for c in FALLBACK_ORDER]

    prefixes=["","잠깐, ","의외로 ","생각보다 ","많은 분이 ","오늘부터 ","딱 10초만, ","혹시 ","먼저 ","제품 사기 전에 "]
    suffixes=[""," 한번 확인해보세요."," 이 부분부터 보세요."," 비교해보세요."," 루틴에서 체크해보세요."," 사용 전에 확인해보세요."]
    variants=[]
    i=0
    while len(variants)<n*5:
        cat,sig=cats[i%len(cats)]
        base=HOOK_PATTERNS.get(cat,HOOK_PATTERNS["curiosity"]).format(product=product)
        pre=prefixes[(i//len(cats))%len(prefixes)]
        suf=suffixes[(i//(len(cats)*len(prefixes)))%len(suffixes)]
        text=(pre+base+suf).strip().replace("??","?").replace("..",".")
        bonus=min(3.0,(sig["quality"]/100)*3) if sig else 0
        sc,parts=score_hook(text,cat,product,bonus)
        variants.append(Hook(0,text,cat,sc,*parts,
            db_source_id=(sig["source_id"] if sig else None),
            db_hook_id=(sig["hook_id"] if sig else None)))
        i+=1
    uniq={}
    for h in variants:
        if h.text not in uniq or h.score>uniq[h.text].score: uniq[h.text]=h
    pool=sorted(uniq.values(),key=lambda x:(x.score,-len(x.text)),reverse=True)

    # Diversity-aware ranking:
    # - TOP3 should prefer distinct DB hook_id
    # - TOP3 should also prefer distinct hook categories
    # - remaining hooks are filled by score
    selected=[]
    used_hook_ids=set()
    used_categories=set()

    # Pass 1: strongest diversity for TOP3
    for h in pool:
        if len(selected) >= min(3,n):
            break
        hook_ok = (h.db_hook_id is None or h.db_hook_id not in used_hook_ids)
        cat_ok = h.category not in used_categories
        if hook_ok and cat_ok:
            selected.append(h)
            if h.db_hook_id is not None:
                used_hook_ids.add(h.db_hook_id)
            used_categories.add(h.category)

    # Pass 2: keep DB refs distinct even if category must repeat
    if len(selected) < min(3,n):
        for h in pool:
            if h in selected:
                continue
            if h.db_hook_id is None or h.db_hook_id not in used_hook_ids:
                selected.append(h)
                if h.db_hook_id is not None:
                    used_hook_ids.add(h.db_hook_id)
                used_categories.add(h.category)
                if len(selected) >= min(3,n):
                    break

    # Pass 3: score fallback if source data is too sparse
    if len(selected) < min(3,n):
        for h in pool:
            if h not in selected:
                selected.append(h)
                if len(selected) >= min(3,n):
                    break

    # Fill remaining ranking by score while preserving uniqueness of text
    for h in pool:
        if h not in selected:
            selected.append(h)
        if len(selected) >= n:
            break

    ranked=selected[:n]
    for i,h in enumerate(ranked,1):
        h.rank=i
    return ranked

def choose_cta(ctx):
    if ctx.get("connected") and ctx.get("ctas"):
        raw=" ".join(str(x or "") for x in ctx["ctas"] for x in (x.get("cta_type"),x.get("goal"))).lower()
        if "save" in raw: return CTA_PATTERNS["save"],ctx["ctas"][0]
        if "comment" in raw or "engage" in raw: return CTA_PATTERNS["comment"],ctx["ctas"][0]
        if "learn" in raw or "click" in raw or "conversion" in raw: return CTA_PATTERNS["learn_more"],ctx["ctas"][0]
        return CTA_PATTERNS["check"],ctx["ctas"][0]
    return CTA_PATTERNS["check"],None

def choose_demo(ctx):
    default="제형 확인 → 소량 도포 → 사용감 체크"
    if ctx.get("connected") and ctx.get("product_demo"):
        d=ctx["product_demo"][0]
        typ=(d.get("demo_type") or "").lower()
        if "unbox" in typ: return "패키지 공개 → 제형 확인 → 소량 도포",d
        if "comparison" in typ: return "두 사용 방식을 나란히 비교 → 제형/밀림 체크",d
        return default,d
    return default,None

def build_script(product, hook, ctx):
    cta,cta_ref=choose_cta(ctx)
    demo_style,demo_ref=choose_demo(ctx)
    framework_ref=(ctx.get("scripts") or [None])[0] if ctx.get("connected") else None
    ba_ref=(ctx.get("before_after") or [None])[0] if ctx.get("connected") else None
    test_ref=(ctx.get("testimonial") or [None])[0] if ctx.get("connected") else None

    beats=[
      {"time":"0-3s","role":"HOOK","spoken":hook.text,
       "onscreen":hook.text,"visual":f"{product} 제품을 빠르게 클로즈업. 손에 들고 카메라 쪽으로 보여준다."},
      {"time":"3-8s","role":"PROBLEM","spoken":f"{product}는 제품 자체만큼 내 피부 상태와 바르는 순서, 사용량을 같이 보는 게 중요합니다.",
       "onscreen":"제품 + 피부상태 + 사용순서","visual":"세안 후 피부와 제품을 번갈아 보여주는 짧은 컷."},
      {"time":"8-17s","role":"DEMO","spoken":f"{demo_style}. {product}는 손등에서 먼저 제형을 확인하고 얼굴에는 소량씩 나눠 발라보세요.",
       "onscreen":demo_style,"visual":f"드로퍼/펌프에서 {product} 한 방울. 매크로 제형 촬영 후 볼에 소량 도포."},
      {"time":"17-25s","role":"PROOF_SAFE","spoken":"바른 직후에는 끈적임, 밀림, 당김 같은 사용감을 확인하고 내 루틴과 맞는지 비교해보세요.",
       "onscreen":"끈적임 · 밀림 · 당김 체크","visual":"피부 표면을 가볍게 터치하고 사용 전후의 느낌을 과장 없이 비교."},
      {"time":"25-30s","role":"CTA","spoken":cta,"onscreen":"제품 정보·사용법 확인","visual":f"{product} 패키지와 제품 페이지를 연상시키는 깔끔한 엔드카드."},
    ]
    refs={
      "framework":framework_ref,
      "cta":cta_ref,
      "product_demo":demo_ref,
      "before_after":ba_ref,
      "testimonial":test_ref,
    }
    return beats,cta,refs

def model_prompt(model, product, beat):
    base=f"""Vertical 9:16 premium Korean beauty short-form ad for a skincare {product}.
Scene timing: {beat['time']}. Purpose: {beat['role']}.
Visual action: {beat['visual']}
On-screen text concept: {beat['onscreen']}
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition."""
    if model=="kling":
        return base+"\nCamera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion."
    if model=="veo":
        return base+"\nCamera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts."
    return base+"\nMotion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing."

def generate(product):
    ctx=db_context()
    hooks=generate_hooks(product,ctx,30)
    top3=hooks[:3]
    beats,cta,refs=build_script(product,top3[0],ctx)
    prompts={m:[model_prompt(m,product,b) for b in beats] for m in ["kling","veo","seedance"]}
    return {
      "product":product,
      "db_integration":{
        "connected":ctx.get("connected",False),
        "database":str(DB),
        "counts":ctx.get("counts",{}),
        "commercial_policy":"COMMERCIAL_OK + TRANSFORM_ONLY only; RESEARCH_ONLY/BLOCKED/UNKNOWN excluded from direct generation",
        "selected_references":refs,
        "hook_reference_ids":[{"hook_id":h.db_hook_id,"source_id":h.db_source_id,"category":h.category} for h in top3],
        "top3_diversity":{
          "unique_hook_ids":len({h.db_hook_id for h in top3 if h.db_hook_id is not None}),
          "unique_categories":len({h.category for h in top3})
        },
      },
      "hooks":[asdict(h) for h in hooks],
      "top3":[asdict(h) for h in top3],
      "script_30s":beats,
      "cta":cta,
      "video_prompts":prompts
    }

def render_md(data):
    db=data["db_integration"]
    out=[f"# Script Generator V2.2 — {data['product']}","",
         "## DB 연동 검증",
         f"- DB 연결: **{'YES' if db['connected'] else 'NO'}**",
         f"- Database: `{db['database']}`",
         f"- DB counts: `{json.dumps(db['counts'],ensure_ascii=False)}`",
         f"- 정책: {db['commercial_policy']}",
         f"- TOP3 Hook reference IDs: `{db['hook_reference_ids']}`",f"- TOP3 다양성: `{db.get('top3_diversity',{})}`","",
         "## TOP 3 Hooks"]
    for h in data["top3"]:
        out.append(f"{h['rank']}. **{h['text']}** — {h['score']}점 ({h['category']}) · DB hook={h['db_hook_id']} source={h['db_source_id']}")
    out+=["","## 30초 대본",""]
    for b in data["script_30s"]:
        out += [f"### {b['time']} · {b['role']}",f"- 대사: {b['spoken']}",f"- 자막: {b['onscreen']}",f"- 화면: {b['visual']}",""]
    out+=["## CTA",data["cta"],""]
    for model in ["kling","veo","seedance"]:
        out += [f"## {model.upper()} 장면별 Prompt",""]
        for i,p in enumerate(data["video_prompts"][model],1):
            out += [f"### Shot {i}","```text",p,"```",""]
    return "\n".join(out)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("--outdir",default="outputs")
    ap.add_argument("--require-db",action="store_true",help="fail if Content DB is empty/unavailable")
    a=ap.parse_args()
    data=generate(a.product)
    if a.require_db and not data["db_integration"]["connected"]:
        raise SystemExit("ERROR: Content DB is not connected or empty. Run collector/build_indexes first.")
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r'[^0-9A-Za-z가-힣_-]+','_',a.product)
    (out/f"{safe}_script_v2.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/f"{safe}_script_v2.md").write_text(render_md(data),encoding="utf-8")
    print("DB connected:",data["db_integration"]["connected"])
    print("DB counts:",data["db_integration"]["counts"])
    print("Generated:",out/f"{safe}_script_v2.md")
