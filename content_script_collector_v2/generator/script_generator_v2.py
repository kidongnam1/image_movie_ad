from __future__ import annotations
import argparse, json, logging, re, sqlite3, traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'database/content_script.sqlite'; LOG_DIR=ROOT/'logs'; MIN_CREATIVE_SCORE=80.0
RULES=[
('beauty',('세럼','로션','크림','토너','앰플','화장품','마스크팩','선크림','클렌저','립','스킨케어')),
('golf',('골프','거리측정기','퍼터','드라이버','아이언','웨지','골프공','골프백')),
('automotive',('자동차','차량용','세차','거치대','발수','블랙박스','타이어','카매트')),
('pet',('강아지','고양이','반려','펫','급식기','배변','캣')),
('travel',('캐리어','여행','트래블','여권','수하물','기내용')),
('kitchen',('주방','프라이팬','냄비','도마','에어프라이어','믹서기')),
('fashion',('의류','셔츠','바지','자켓','재킷','신발','운동화','가방','모자','패션')),
('food',('식품','간식','커피','음료','소스','라면','건강식','과자')),
('home_appliance',('청소기','가습기','제습기','선풍기','에어컨','공기청정기','건조기','가전')),
('electronics',('이어폰','헤드폰','충전기','보조배터리','키보드','마우스','스피커','모니터','전자')),
('sports',('러닝','운동','헬스','요가','자전거','스포츠','등산')),
('office',('사무','의자','책상','문구','노트','프린터')),
('household',('세제','수납','정리','생활용품','휴지','타월','욕실','청소'))]
P={
'beauty':('뷰티/스킨케어','내 피부와 맞지 않는 사용감 때문에 제품을 바꿔도 만족하기 어려운 상황','제형과 사용감, 성분·사용법의 적합성','제품을 소량 사용해 제형과 실제 사용감을 가까이 보여준다','동일한 조건에서 사용감과 루틴 적합성을 과장 없이 비교한다','clean vanity or bathroom setting','내 피부와 루틴에 잘 맞는 제품을 고르는 것'),
'golf':('골프','거리와 상황 판단이 흔들려 클럽 선택이 애매해지는 순간','측정 정확도·속도와 라운드 중 사용 편의성','티잉구역이나 페어웨이에서 제품을 실제로 작동시키고 결과를 즉시 보여준다','같은 지점을 반복 측정하거나 실제 라운드 상황에서 사용 과정을 보여준다','golf course or driving range','판단 시간을 줄이고 더 자신 있게 플레이하는 것'),
'automotive':('자동차용품','운전이나 차량 관리 중 반복되는 작지만 짜증나는 불편','설치·사용 편의성과 실제 차량 환경에서의 체감 기능','차량 내부 또는 외부에서 설치 전후의 사용 과정을 직접 보여준다','같은 차량 환경에서 기능 작동 여부와 사용 편의성을 비교한다','real car interior, garage, or parking area','운전과 차량 관리를 더 간단하고 편하게 만드는 것'),
'pet':('반려동물','외출하거나 바쁠 때 반려동물 돌봄을 놓칠까 신경 쓰이는 상황','반려동물과 보호자가 실제로 편해지는 핵심 기능','반려동물이 있는 실제 생활 공간에서 기능을 작동시키는 모습을 보여준다','설정부터 실제 사용까지의 흐름을 끊김 없이 보여준다','warm pet-friendly home','돌봄 부담을 줄이고 안심하는 것'),
'travel':('여행','이동 중 짐 때문에 생기는 번거로움과 예상치 못한 불편','수납·내구성·휴대성과 이동 중 사용 편의성','실제 짐을 넣고 이동하거나 펼치고 접는 과정을 빠르게 보여준다','공항·숙소·차량 등 실제 이동 동선에서 사용성을 확인한다','airport, hotel room, or travel transit setting','짐 스트레스를 줄이고 이동을 편하게 만드는 것'),
'kitchen':('주방용품','조리할 때 매번 반복되는 번거로운 작업과 정리 스트레스','조리 시간·세척·보관을 줄여주는 실제 사용성','실제 재료와 함께 제품을 사용해 핵심 동작을 한 번에 보여준다','사용 전후의 작업 단계와 정리 시간을 같은 조건에서 비교한다','realistic modern kitchen','요리와 정리를 더 빠르고 간단하게 만드는 것'),
'fashion':('패션','사진과 실제 착용감·핏이 달라 구매 후 손이 잘 안 가는 문제','핏·소재·착용감과 활용도','실제 착용 후 앞·옆·움직임을 짧게 보여준다','여러 코디나 움직임에서 핏과 활용도를 확인한다','clean wardrobe, studio, or real street setting','자주 손이 가고 활용하기 쉬운 선택을 하는 것'),
'food':('식품/음료','맛이나 편의성을 기대했지만 재구매할 이유가 약한 제품을 고르는 문제','맛·구성·조리 또는 섭취 편의성','개봉부터 준비·섭취까지 실제 과정을 빠르게 보여준다','구성·용량·조리 과정을 사실적으로 보여주고 과장된 건강 효능은 피한다','home dining table or kitchen','맛과 편의성을 동시에 만족시키는 것'),
'home_appliance':('생활가전','기존 제품을 써도 시간과 손이 계속 많이 가는 불편','성능과 사용 시간, 관리 편의성을 체감할 수 있는 기능','실제 집 안에서 제품을 작동시키고 핵심 기능을 바로 보여준다','같은 조건에서 작동 과정과 결과를 연속 촬영으로 보여준다','real lived-in home interior','집안일 시간을 줄이고 반복 작업을 덜어내는 것'),
'electronics':('전자기기','매일 쓰는 기기에서 연결·충전·조작 때문에 흐름이 끊기는 불편','속도·호환성·배터리·조작 편의성 같은 핵심 스펙','실제 기기와 연결해 핵심 기능이 작동하는 장면을 보여준다','연결 과정과 실제 작동 상태를 한 화면에서 확인시킨다','clean desk or everyday tech setup','매일 쓰는 환경을 더 빠르고 단순하게 만드는 것'),
'sports':('스포츠/운동','운동 흐름을 끊거나 반복 사용이 불편해 결국 안 쓰게 되는 문제','착용감·휴대성·운동 중 실제 사용 편의성','실제 운동 동작 속에서 제품이 어떻게 쓰이는지 보여준다','정지 화면보다 실제 움직임 속 안정성과 사용성을 확인한다','gym, running track, or outdoor sports setting','운동 흐름을 유지하고 꾸준히 쓰기 쉬운 장비를 고르는 것'),
'office':('사무/오피스','작업 중 작은 불편이 반복되어 집중이 끊기는 문제','업무 속도·정리·편안함을 개선하는 실사용 기능','실제 책상에서 업무 흐름 안에 제품을 사용해 보여준다','사용 전후 작업 단계를 비교해 불필요한 동작이 줄어드는지 보여준다','realistic office or desk setup','집중을 덜 끊고 업무를 더 단순하게 만드는 것'),
'household':('생활용품','매일 반복되는 집안일에서 사소한 불편이 계속 쌓이는 문제','사용·정리·세척을 줄여주는 실용성','실제 생활 공간에서 문제 상황과 제품 사용을 연속으로 보여준다','같은 조건에서 사용 전후 작업 과정을 비교한다','realistic home utility setting','반복되는 생활 불편을 줄이는 것'),
'general':('일반 상품','비슷한 제품이 많아 무엇을 기준으로 골라야 할지 애매한 상황','실제 사용에서 차이를 만드는 핵심 기능과 편의성','제품의 대표 기능을 실제 사용 환경에서 바로 보여준다','광고 문구 대신 실제 작동·사용 과정을 한 화면에서 확인시킨다','realistic everyday product-use setting','돈을 두 번 쓰지 않고 나에게 맞는 제품을 고르는 것')}
ANGLES={'problem_attack':('문제공격형','A · 문제/손실회피'),'loss_aversion':('손실회피형','B · 손실회피'),'curiosity':('호기심형','C · 호기심'),'comparison':('비교형','D · 비교/전문가'),'contrarian':('반전형','E · 반전/UGC'),'discovery':('발견형','F · 발견/직설'),'proof':('증거형','G · 증거/실사용')}
ANGLE_ORDER=tuple(ANGLES); BANNED=('치료','완치','100%','즉시 효과','무조건','절대','주름 제거','여드름 치료','완전히 사라')

def _logger():
    LOG_DIR.mkdir(parents=True,exist_ok=True); l=logging.getLogger('script_generator_v2')
    if not l.handlers:
        l.setLevel(logging.INFO); h=logging.FileHandler(LOG_DIR/'app.log',encoding='utf-8'); h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s')); l.addHandler(h)
    return l
LOGGER=_logger()
def log_status(m): print(m); LOGGER.info(m)
def split_values(v):
    if not v:return []
    raw=[str(x) for x in v] if isinstance(v,(list,tuple)) else re.split(r'(?<!\d),(?!\d)|[;|\n]+',str(v)); out=[]
    for x in raw:
        x=re.sub(r'\s+',' ',x).strip(' -\t')
        if x and x not in out: out.append(x)
    return out

def infer_category(product,description='',override=''):
    aliases={'뷰티':'beauty','화장품':'beauty','골프':'golf','자동차':'automotive','차량':'automotive','펫':'pet','반려동물':'pet','여행':'travel','주방':'kitchen','패션':'fashion','식품':'food','가전':'home_appliance','전자':'electronics','스포츠':'sports','사무':'office','생활':'household','일반':'general'}
    o=aliases.get((override or '').strip().lower(),(override or '').strip().lower())
    if o in P:return o
    h=f'{product} {description}'.lower()
    for c,ks in RULES:
        if any(k.lower() in h for k in ks):return c
    return 'general'

def product_profile(product,category='',features=None,must_emphasize=None,pain_point='',target='일반 소비자',description=''):
    c=infer_category(product,description,category); label,pain,feat,demo,proof,env,motive=P[c]; req=split_values(must_emphasize); opt=split_values(features); pts=[]
    for x in req+opt+[feat]:
        if x and x not in pts:pts.append(x)
    return {'product':product.strip(),'category':c,'category_label':label,'description':(description or '').strip(),'target':(target or '일반 소비자').strip(),'pain_point':(pain_point or pain).strip(),'must_emphasize':req,'features':opt,'selling_points':pts,'primary_selling_point':pts[0],'default_feature':feat,'demo_action':demo,'proof_action':proof,'environment':env,'buyer_motive':motive,'claim_verification_required':bool(req or opt)}

@dataclass
class Hook:
    rank:int;text:str;category:str;angle:str;score:float;hook_strength:float;scroll_stop:float;curiosity_gap:float;purchase_desire:float;clarity:float;credibility:float;risk:float;curiosity:float;relevance:float;differentiation:float;db_source_id:int|None=None;db_hook_id:int|None=None

def risk_score(t):
    n=sum(x.lower() in (t or '').lower() for x in BANNED);return 0.0 if not n else min(100.0,35+n*20)
def score_hook(text,angle,pc,intensity,bonus=0):
    hs=min(98,76+intensity*4+(5 if angle in {'problem_attack','loss_aversion','contrarian'} else 2)); ss=min(98,72+intensity*4.5+(6 if angle in {'problem_attack','loss_aversion','curiosity'} else 2)); cg=94 if angle in {'curiosity','contrarian','discovery'} else 86 if angle in {'comparison','problem_attack'} else 82; pd=94 if any(x in text for x in pc['selling_points'][:3]) else 84; cl=95 if len(text)<=48 else 90 if len(text)<=64 else 82; cr=94 if pd==94 else 88; r=risk_score(text); total=hs*.30+ss*.20+cg*.15+pd*.15+cl*.10+cr*.10+min(3,bonus)-r*.30
    return round(min(100,max(0,total)),1),{'hook_strength':hs,'scroll_stop':ss,'curiosity_gap':cg,'purchase_desire':pd,'clarity':cl,'credibility':cr,'risk':r}

def db_context():
    if not DB.exists():return {'connected':False,'counts':{},'hook_signals':[]}
    con=sqlite3.connect(DB);con.row_factory=sqlite3.Row; counts={}
    for t in ('sources','viral_hooks','short_form_scripts','ctas','product_demo_patterns'):
        try:counts[t]=con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except Exception:counts[t]=0
    sig=[]
    try:
        rows=con.execute("SELECT h.hook_id,h.source_id,h.hook_category,h.hook_formula,h.formula_family,h.quality_score FROM viral_hooks h JOIN sources s ON s.source_id=h.source_id WHERE s.usage_class IN ('COMMERCIAL_OK','TRANSFORM_ONLY') AND COALESCE(h.claim_risk,'LOW') NOT IN ('HIGH','PROHIBITED') ORDER BY h.quality_score DESC LIMIT 80").fetchall()
        for r in rows:
            raw=' '.join(str(r[k] or '').lower() for k in ('hook_category','hook_formula','formula_family')); a='comparison' if any(x in raw for x in ('compare','versus','비교')) else 'problem_attack' if any(x in raw for x in ('problem','pain','mistake','warning','문제')) else 'loss_aversion' if any(x in raw for x in ('loss','cost','fear')) else 'contrarian' if any(x in raw for x in ('contrarian','myth','reversal')) else 'proof' if any(x in raw for x in ('proof','review','demo','후기')) else 'curiosity' if any(x in raw for x in ('curiosity','secret','question','mystery')) else 'discovery'; sig.append({'hook_id':r['hook_id'],'source_id':r['source_id'],'angle':a,'quality':float(r['quality_score'] or 0)})
    except Exception:pass
    con.close();return {'connected':counts.get('viral_hooks',0)>0,'counts':counts,'hook_signals':sig}

def tone(i):return {1:'정보 중심',2:'관심 유도',3:'강한 후킹',4:'퍼포먼스 광고',5:'극강 후킹'}[i]
def hook_text(a,pc,i,v):
    p=pc['product'];pain=pc['pain_point'];pt=pc['selling_points'][v%min(3,len(pc['selling_points']))];target=pc['target']
    T={
    'problem_attack':[f'{pain} 때문에 {p} 찾고 계시다면, {pt}부터 보세요.',f'{p} 써도 같은 불편이 반복된다면 핵심 포인트 {pt}를 먼저 확인하세요.',f'{pain} 때문에 제품을 또 바꾸기 전에 {p}의 {pt}부터 보세요.'],
    'loss_aversion':[f'이 기준 모르고 {p} 사면 돈 두 번 쓸 수 있습니다. 핵심은 {pt}입니다.',f'{p} 가격만 보고 고르면 놓치기 쉽습니다. 핵심 포인트는 {pt}입니다.',f'{pain} 때문에 다시 사기 전에 {p}의 {pt}부터 확인하세요.'],
    'curiosity':[f'왜 요즘 {p} 고를 때 {pt}를 먼저 보는지 10초면 이해됩니다.',f'처음 보면 평범한 {p}인데, {pt}에서 차이가 납니다.',f'{target}이 {p}에서 먼저 볼 한 가지, {pt}입니다.'],
    'comparison':[f'비싼 {p}보다 먼저 비교할 것, {pt}입니다.',f'{p}끼리 비교할 때 스펙표보다 먼저 볼 건 {pt}입니다.',f'비슷해 보이는 {p}, 결국 차이는 {pt}에서 드러납니다.'],
    'contrarian':[f'{p}, 기능이 많다고 답은 아닙니다. 핵심 포인트는 {pt}입니다.',f'{p}는 비싸다고 답이 아닙니다. 실제 핵심은 {pt}입니다.',f'다들 {p}의 겉모습부터 보지만, 저는 핵심 포인트 {pt}부터 봅니다.'],
    'discovery':[f'처음엔 별거 아닌 줄 알았는데, {pt} 때문에 {p} 보는 기준이 바뀝니다.',f'{p}에서 의외로 만족도를 가르는 건 {pt}였습니다.',f'이 {p}를 다시 보게 만든 포인트는 딱 하나, {pt}입니다.'],
    'proof':[f'{p} 광고 문구 말고 실제로 확인할 건 {pt}입니다.',f'말로만 좋은 {p} 말고, {pt}가 실제로 어떻게 작동하는지 보세요.',f'{p} 살 때 후기보다 먼저 직접 확인할 수 있는 건 {pt}입니다.']}
    text=T[a][v%3]
    if i==1:text=text.replace('돈 두 번 쓸 수 있습니다','후회할 수 있습니다')
    if i==5 and a in {'problem_attack','loss_aversion'}:text='딱 10초만 보세요. '+text
    g=v//3
    if g==1:text='구매 전에 확인하세요. '+text
    elif g==2:text='실사용 기준으로 보면, '+text
    elif g>=3:text='후기보다 먼저 볼 건 이겁니다. '+text
    return text

def generate_hooks(pc,ctx,n=30,intensity=4,min_score=80):
    sb={}
    for s in ctx.get('hook_signals',[]):
        if s['angle'] not in sb:sb[s['angle']]=s
    cand=[]
    for v in range(12):
        for a in ANGLE_ORDER:
            sig=sb.get(a); text=hook_text(a,pc,intensity,v);sc,z=score_hook(text,a,pc,intensity,min(3,(sig or {}).get('quality',0)/100*3))
            if sc>=min_score:cand.append(Hook(0,text,a,a,sc,z['hook_strength'],z['scroll_stop'],z['curiosity_gap'],z['purchase_desire'],z['clarity'],z['credibility'],z['risk'],z['curiosity_gap'],z['purchase_desire'],z['hook_strength'],(sig or {}).get('source_id'),(sig or {}).get('hook_id')))
    pool=sorted({h.text:h for h in cand}.values(),key=lambda h:(h.score,h.credibility,-len(h.text)),reverse=True); sel=[]; used=set()
    for h in pool:
        if h.angle not in used:sel.append(h);used.add(h.angle)
    for h in pool:
        if h not in sel:sel.append(h)
        if len(sel)>=n:break
    if len(sel)<n:raise RuntimeError(f'{min_score}점 이상 고유 Hook이 {len(sel)}개뿐입니다.')
    for j,h in enumerate(sel[:n],1):h.rank=j
    return sel[:n]
def cta(i):return {1:'제품 정보와 사용 조건을 확인해보세요.',2:'관심 있다면 상세 페이지에서 핵심 기능을 비교해보세요.',3:'비슷한 불편이 있다면 가격과 상세 조건을 한번 확인해보세요.',4:'지금 쓰는 제품과 비교해보고, 조건이 맞는지 상세 페이지에서 확인해보세요.',5:'계속 같은 불편을 겪고 있다면, 지금 핵심 기능과 가격부터 비교해보세요.'}[i]
def times(d):
    w=[12,18,30,24,16];st=[0];c=0
    for x in w[:-1]:c+=x;st.append(round(d*c/sum(w)))
    return list(zip(st,st[1:]+[d]))
def build_script(pc,h,d,a,i):
    p=pc['product'];pt=pc['primary_selling_point'];pain=pc['pain_point'];pref='사용자가 제공한 특징을 기준으로 ' if pc['claim_verification_required'] else ''
    C=[('HOOK',h.text,h.text,f'{p}을 첫 프레임에서 크게 보여주고 문제 상황을 1초 안에 제시한다.'),('PROBLEM',f'{pain}. 그래서 {p}를 고를 때는 겉모습보다 실제 불편을 줄이는 기준이 중요합니다.','문제부터 정확히',f'{pain}이 드러나는 실제 사용 상황을 짧게 보여준다.'),('SOLUTION',f'이 제품에서 가장 먼저 볼 포인트는 {pt}입니다. {pc["buyer_motive"]}에 직접 연결되는지 확인해보세요.',f'핵심: {pt}',pc['demo_action']),('PROOF',f'{pref}광고 문구보다 실제 작동과 사용 과정을 확인하는 게 좋습니다. {pt}가 체감되는지 직접 보세요.','말보다 실제 사용',pc['proof_action']),('CTA',cta(i),'가격 · 조건 · 핵심 기능 확인',f'{p}과 핵심 특징 {pt}를 한 화면에 정리한 엔드카드.')]
    return [{'time':f'{s}-{e}s','role':r,'spoken':sp,'onscreen':on,'visual':vi,'angle':a} for (r,sp,on,vi),(s,e) in zip(C,times(d))]
def script_score(h,b,pc):
    text=' '.join(x['spoken'] for x in b);r=risk_score(text);pd=95 if pc['primary_selling_point'] in text else 82;cl=94 if pc['product'] in text else 84;cr=94 if not r else 82;tot=h.hook_strength*.30+h.scroll_stop*.20+h.curiosity_gap*.15+pd*.15+cl*.10+cr*.10-r*.30
    return {'hook_strength':h.hook_strength,'scroll_stop_power':h.scroll_stop,'curiosity_gap':h.curiosity_gap,'purchase_desire':pd,'clarity':cl,'credibility':cr,'risk':r,'total':round(min(100,max(0,tot)),1)}
def competition(pc,hooks,i,min_score):
    by={};[by.setdefault(h.angle,h) for h in hooks];out=[]
    for a in ('loss_aversion','curiosity','problem_attack','comparison','contrarian'):
        h=by.get(a,hooks[0]);b=build_script(pc,h,30,a,i);s=script_score(h,b,pc);out.append({'copywriter':ANGLES[a][1],'angle':a,'angle_label':ANGLES[a][0],'hook':asdict(h),'script_30s':b,'scores':s,'qualified':s['total']>=min_score})
    return sorted(out,key=lambda x:x['scores']['total'],reverse=True)
def prompt(model,pc,b):
    base=f"Vertical 9:16 Korean short-form performance ad for {pc['product']}. Product category: {pc['category_label']}. Target audience: {pc['target']}. Scene timing: {b['time']}. Purpose: {b['role']}. Visual action: {b['visual']} Environment: {pc['environment']}. On-screen text concept: {b['onscreen']}. Authentic product-focused commercial, strong first frame, realistic use demonstration, consistent packaging, no unsupported superlatives, fabricated reviews, fake scarcity, or unverified medical claims."
    return base+({'kling':' Controlled handheld-to-close-up motion and smooth social-ad pacing.','veo':' Cinematic close-up, coherent continuity and realistic ambience.','seedance':' Dynamic but stable camera movement and clear problem/benefit contrast.'}[model])

def generate(product,*,category='',features=None,must_emphasize=None,pain_point='',target='일반 소비자',description='',intensity=4,min_score=80.0):
    if not (product or '').strip():raise ValueError('product is required')
    if intensity not in range(1,6):raise ValueError('intensity must be 1..5')
    log_status(f'[1/6] 상품 분석: {product}');pc=product_profile(product,category,features,must_emphasize,pain_point,target,description);ctx=db_context();log_status(f"[2/6] 카테고리={pc['category_label']} / 강조={pc['primary_selling_point']}");hooks=generate_hooks(pc,ctx,30,intensity,min_score);top3=hooks[:3];log_status(f'[3/6] Hook 30개 생성 완료 / TOP1={top3[0].score}점');comp=competition(pc,hooks,intensity,min_score);win=next((x for x in comp if x['qualified']),comp[0]);wh=Hook(**win['hook']);log_status(f"[4/6] Creative Competition 우승={win['angle_label']} / {win['scores']['total']}점")
    scripts={};prompts={}
    for d in (15,30,45):
        k=f'{d}s';b=build_script(pc,wh,d,win['angle'],intensity);scripts[k]=b;prompts[k]={m:[prompt(m,pc,x) for x in b] for m in ('kling','veo','seedance')}
    log_status('[5/6] 15초 / 30초 / 45초 대본 생성 완료');data={'version':'2.4','product':pc['product'],'product_analysis':pc,'ad_settings':{'intensity':intensity,'intensity_label':tone(intensity),'minimum_score':min_score,'discard_below_score':True},'db_integration':{'connected':ctx.get('connected',False),'database':str(DB),'counts':ctx.get('counts',{}),'commercial_policy':'COMMERCIAL_OK + TRANSFORM_ONLY only; RESEARCH_ONLY/BLOCKED/UNKNOWN excluded from direct generation','selected_references':{},'hook_reference_ids':[{'hook_id':h.db_hook_id,'source_id':h.db_source_id,'category':h.category} for h in top3],'top3_diversity':{'unique_hook_ids':len({h.db_hook_id for h in top3 if h.db_hook_id is not None}),'unique_categories':len({h.category for h in top3})}},'hooks':[asdict(h) for h in hooks],'top3':[asdict(h) for h in top3],'creative_competition':comp,'winner':{'copywriter':win['copywriter'],'angle':win['angle'],'angle_label':win['angle_label'],'scores':win['scores']},'scripts_by_duration':scripts,'script_15s':scripts['15s'],'script_30s':scripts['30s'],'script_45s':scripts['45s'],'cta':cta(intensity),'video_prompts_by_duration':prompts,'video_prompts':prompts['30s'],'claim_note':'사용자가 제공한 수치·성능·효능 특징은 광고 집행 전에 상품 상세페이지/공식 자료로 사실 확인이 필요합니다.'};log_status('[6/6] 생성 완료');return data

def render_md(d):
    pc=d['product_analysis'];s=d['ad_settings'];out=[f"# Script Generator V2.4 — {d['product']}",'','## 상품 분석',f"- 카테고리: **{pc['category_label']}** (`{pc['category']}`)",f"- 타깃: {pc['target']}",f"- 핵심 Pain Point: {pc['pain_point']}",f"- 반드시 강조: {pc['must_emphasize'] or '미입력 → AI 기본값 사용'}",f"- Selling Points: {pc['selling_points']}",f"- 광고 강도: {s['intensity']} / 5 · {s['intensity_label']}",f"- 품질 Gate: **{s['minimum_score']}점 미만 폐기**",'','## TOP 3 Hooks']
    out += [f"{h['rank']}. **{h['text']}** — {h['score']}점 · {ANGLES[h['angle']][0]}" for h in d['top3']];out+=['','## Creative Competition']
    for j,x in enumerate(d['creative_competition'],1):out.append(f"{'🏆' if x['angle']==d['winner']['angle'] else '-'} {j}. {x['copywriter']} / {x['angle_label']} — **{x['scores']['total']}점**")
    for dur in (15,30,45):
        out += ['',f'## {dur}초 대본','']
        for b in d[f'script_{dur}s']:out += [f"### {b['time']} · {b['role']}",f"- 대사: {b['spoken']}",f"- 자막: {b['onscreen']}",f"- 화면: {b['visual']}",'']
    out += ['## CTA',d['cta'],'','## 광고 집행 전 확인',d['claim_note'],'']
    for m in ('kling','veo','seedance'):
        out += [f'## {m.upper()} · 30초 장면별 Prompt','']
        for j,p in enumerate(d['video_prompts'][m],1):out += [f'### Shot {j}','```text',p,'```','']
    return '\n'.join(out)
def parse_args():
    a=argparse.ArgumentParser();a.add_argument('product');a.add_argument('--category',default='');a.add_argument('--features',default='');a.add_argument('--must-emphasize',default='');a.add_argument('--pain-point',default='');a.add_argument('--target',default='일반 소비자');a.add_argument('--description',default='');a.add_argument('--intensity',type=int,choices=(1,2,3,4,5),default=4);a.add_argument('--min-score',type=float,default=80);a.add_argument('--outdir',default='outputs');a.add_argument('--require-db',action='store_true');return a.parse_args()
def main():
    a=parse_args()
    try:
        d=generate(a.product,category=a.category,features=a.features,must_emphasize=a.must_emphasize,pain_point=a.pain_point,target=a.target,description=a.description,intensity=a.intensity,min_score=a.min_score)
        if a.require_db and not d['db_integration']['connected']:raise RuntimeError('Content DB is not connected or empty.')
        out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);safe=re.sub(r'[^0-9A-Za-z가-힣_-]+','_',a.product);(out/f'{safe}_script_v2.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');md=out/f'{safe}_script_v2.md';md.write_text(render_md(d),encoding='utf-8');print('DB connected:',d['db_integration']['connected']);print('Category:',d['product_analysis']['category_label']);print('Winner:',d['winner']);print('Generated:',md);return 0
    except Exception as e:tb=traceback.format_exc();print('ERROR:',e);print(tb);LOGGER.error('Script Generator V2.4 failed: %s\n%s',e,tb);return 1
if __name__=='__main__':raise SystemExit(main())
