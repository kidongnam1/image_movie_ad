from __future__ import annotations
import argparse, json, logging, re, sqlite3, traceback
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/content_script.sqlite'; LOG_DIR=ROOT/'logs'; MIN_CREATIVE_SCORE=80.0
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
'beauty':('뷰티/스킨케어','바꿔 써도 사용감이 계속 아쉬운 상황','제형·사용감·성분·사용법의 적합성','제품을 소량 사용해 제형과 실제 사용감을 가까이 보여준다','동일 조건에서 사용감과 루틴 적합성을 비교한다','clean vanity or bathroom setting','내 피부와 루틴에 맞는 제품을 고르는 것','또 안 맞는 제품을 사는 것'),
'golf':('골프','거리 판단이 흔들려 클럽 선택이 애매한 순간','측정 정확도·속도와 라운드 중 사용 편의성','티잉구역이나 페어웨이에서 실제 작동시키고 결과를 즉시 보여준다','같은 지점을 반복 측정해 결과와 속도를 보여준다','golf course or driving range','판단 시간을 줄이고 더 자신 있게 플레이하는 것','한 번의 거리 판단 실수로 샷 흐름을 놓치는 것'),
'automotive':('자동차용품','운전이나 차량 관리에서 같은 불편이 반복되는 상황','설치·사용 편의성과 실제 차량 환경에서의 체감 기능','차량 안팎에서 설치부터 작동까지 직접 보여준다','같은 차량 환경에서 기능 작동 여부와 편의성을 비교한다','real car interior, garage, or parking area','운전과 차량 관리를 더 간단하게 만드는 것','사소한 불편에 매번 시간 쓰는 것'),
'pet':('반려동물','외출할 때 돌봄을 놓칠까 계속 신경 쓰이는 상황','반려동물과 보호자가 실제로 편해지는 핵심 기능','실제 생활 공간에서 기능을 작동시키고 반려동물 반응을 보여준다','설정부터 실제 사용까지 흐름을 끊김 없이 보여준다','warm pet-friendly home','돌봄 부담을 줄이고 안심하는 것','외출할 때마다 돌봄 걱정을 반복하는 것'),
'travel':('여행','이동 중 짐 때문에 예상치 못한 불편이 생기는 상황','수납·내구성·휴대성과 이동 편의성','실제 짐을 넣고 끌고 열고 닫는 과정을 빠르게 보여준다','공항·숙소·차량 등 실제 이동 동선에서 사용성을 확인한다','airport, hotel room, or travel transit setting','짐 스트레스를 줄이고 이동을 편하게 만드는 것','여행 첫날부터 짐 때문에 진 빠지는 것'),
'kitchen':('주방용품','조리할 때 같은 번거로운 작업이 매번 반복되는 상황','조리 시간·세척·보관을 줄여주는 실제 사용성','실제 재료와 함께 핵심 동작을 바로 보여준다','사용 전후 작업 단계와 정리 과정을 같은 조건에서 비교한다','realistic modern kitchen','요리와 정리를 더 빠르게 만드는 것','요리보다 정리에 더 지치는 것'),
'fashion':('패션','사진과 실제 핏이 달라 사고도 손이 안 가는 상황','핏·소재·착용감과 활용도','실제 착용 후 앞·옆·움직임을 짧게 보여준다','여러 코디와 움직임에서 핏과 활용도를 확인한다','clean wardrobe, studio, or real street setting','자주 손이 가는 선택을 하는 것','사고도 옷장에만 걸어두는 것'),
'food':('식품/음료','한 번 먹고 다시 살 이유가 약한 제품을 고르는 상황','맛·구성·조리 또는 섭취 편의성','개봉부터 준비·섭취까지 실제 과정을 빠르게 보여준다','구성·용량·조리 과정을 사실적으로 보여준다','home dining table or kitchen','맛과 편의성을 동시에 만족시키는 것','돈 주고 샀는데 다시 손이 안 가는 것'),
'home_appliance':('생활가전','제품을 써도 시간과 손이 계속 많이 가는 상황','성능·사용 시간·관리 편의성을 체감할 수 있는 기능','실제 집 안에서 작동시키고 핵심 기능을 즉시 보여준다','같은 조건에서 작동 과정과 결과를 연속 촬영으로 보여준다','real lived-in home interior','집안일 시간을 줄이고 반복 작업을 덜어내는 것','기계를 샀는데 결국 사람이 다시 손대는 것'),
'electronics':('전자기기','연결·충전·조작 때문에 흐름이 계속 끊기는 상황','속도·호환성·배터리·조작 편의성','실제 기기와 연결해 핵심 기능이 작동하는 장면을 보여준다','연결 과정과 실제 작동 상태를 한 화면에서 보여준다','clean desk or everyday tech setup','매일 쓰는 환경을 더 빠르고 단순하게 만드는 것','작은 끊김 때문에 매일 시간을 버리는 것'),
'sports':('스포츠/운동','운동 흐름을 끊어 결국 안 쓰게 되는 상황','착용감·휴대성·운동 중 실제 사용 편의성','실제 운동 동작 속에서 제품이 어떻게 쓰이는지 보여준다','움직임 속 안정성과 사용성을 확인한다','gym, running track, or outdoor sports setting','운동 흐름을 유지하고 꾸준히 쓰기 쉬운 장비를 고르는 것','사놓고 결국 안 쓰게 되는 것'),
'office':('사무/오피스','작은 불편이 반복되어 집중이 끊기는 상황','업무 속도·정리·편안함을 개선하는 실사용 기능','실제 책상에서 업무 흐름 안에 제품을 사용한다','사용 전후 작업 단계를 비교해 불필요한 동작 감소를 보여준다','realistic office or desk setup','집중을 덜 끊고 업무를 단순하게 만드는 것','사소한 동작에 하루 집중력을 계속 빼앗기는 것'),
'household':('생활용품','매일 같은 집안일 불편이 반복되는 상황','사용·정리·세척을 줄여주는 실용성','실제 생활 공간에서 문제와 제품 사용을 연속으로 보여준다','같은 조건에서 사용 전후 작업 과정을 비교한다','realistic home utility setting','반복되는 생활 불편을 줄이는 것','작은 불편을 매일 참고 사는 것'),
'general':('일반 상품','비슷한 제품이 너무 많아 선택 기준이 흐려지는 상황','실사용에서 차이를 만드는 핵심 기능과 편의성','대표 기능을 실제 사용 환경에서 바로 보여준다','광고 문구 대신 실제 작동·사용 과정을 보여준다','realistic everyday product-use setting','돈을 두 번 쓰지 않고 맞는 제품을 고르는 것','기준 없이 샀다가 다시 사는 것')}
ANGLES={'problem_attack':('문제공격형','A · 문제공격'),'loss_aversion':('손실회피형','B · 손실회피'),'curiosity':('호기심형','C · 호기심'),'comparison':('비교형','D · 비교/전문가'),'contrarian':('반전형','E · 반전/UGC'),'discovery':('발견형','F · 발견'),'proof':('증거형','G · 실사용 증거')}
ANGLE_ORDER=tuple(ANGLES)
BANNED=('치료','완치','100%','즉시 효과','무조건','절대','주름 제거','여드름 치료','완전히 사라','기적','보장','무조건 환불')
GENERIC=('오늘 소개','제품을 소개','정말 좋은','강력 추천','가성비 최고','인생템','무조건 사세요')

def _logger():
    LOG_DIR.mkdir(parents=True,exist_ok=True); l=logging.getLogger('script_generator_v25')
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
        if x and x not in out:out.append(x)
    return out

def infer_category(product,description='',override=''):
    aliases={'뷰티':'beauty','화장품':'beauty','골프':'golf','자동차':'automotive','차량':'automotive','펫':'pet','반려동물':'pet','여행':'travel','주방':'kitchen','패션':'fashion','식품':'food','가전':'home_appliance','전자':'electronics','스포츠':'sports','사무':'office','생활':'household','일반':'general'}
    o=aliases.get((override or '').strip().lower(),(override or '').strip().lower())
    if o in P:return o
    hay=f'{product} {description}'.lower()
    for c,ks in RULES:
        if any(k.lower() in hay for k in ks):return c
    return 'general'

def product_profile(product,category='',features=None,must_emphasize=None,pain_point='',target='일반 소비자',description=''):
    c=infer_category(product,description,category); label,pain,feat,demo,proof,env,motive,stake=P[c]
    req=split_values(must_emphasize); opt=split_values(features); pts=[]
    for x in req+opt+[feat]:
        if x and x not in pts:pts.append(x)
    return {'product':product.strip(),'category':c,'category_label':label,'description':(description or '').strip(),'target':(target or '일반 소비자').strip(),'pain_point':(pain_point or pain).strip(),'must_emphasize':req,'features':opt,'selling_points':pts,'primary_selling_point':pts[0],'secondary_selling_points':pts[1:3],'default_feature':feat,'demo_action':demo,'proof_action':proof,'environment':env,'buyer_motive':motive,'stake':stake,'claim_verification_required':bool(req or opt),'emphasis_strategy':{'fixed':req,'ai_selected':[x for x in pts if x not in req][:2],'hook_primary':pts[0],'proof_points':pts[:3]}}

@dataclass
class Hook:
    rank:int;text:str;category:str;angle:str;score:float;hook_strength:float;scroll_stop:float;curiosity_gap:float;purchase_desire:float;clarity:float;credibility:float;risk:float;curiosity:float;relevance:float;differentiation:float;first_2s_power:float=0.0;specificity:float=0.0;generic_penalty:float=0.0;db_source_id:int|None=None;db_hook_id:int|None=None

def risk_score(t):
    n=sum(x.lower() in (t or '').lower() for x in BANNED);return 0.0 if not n else min(100.0,35+n*20)
def generic_penalty(t):return min(30.0,sum(x in (t or '') for x in GENERIC)*10.0)
def score_hook(text,angle,pc,intensity,bonus=0):
    hs=min(99,74+intensity*4.5+(7 if angle in {'problem_attack','loss_aversion','contrarian'} else 3));ss=min(99,70+intensity*5+(7 if angle in {'problem_attack','loss_aversion','curiosity'} else 3));cg=96 if angle in {'curiosity','contrarian','discovery'} else 89 if angle in {'comparison','problem_attack'} else 84
    primary=pc['primary_selling_point'] in text;pd=99 if primary else 96 if any(x in text for x in pc['selling_points'][:3]) else 82;cl=96 if len(text)<=42 else 92 if len(text)<=58 else 84;cr=95 if pd>=96 and risk_score(text)==0 else 88
    first=min(99,80+intensity*3+(5 if text[:12].count('?') or any(text.startswith(x) for x in ('아직도','잠깐','이거','광고는','가격부터','딱')) else 0));spec=99 if primary else 96 if any(ch.isdigit() for ch in text) else 88;r=risk_score(text);gp=generic_penalty(text)
    total=hs*.22+ss*.18+cg*.13+pd*.14+cl*.09+cr*.10+first*.08+spec*.06+min(3,bonus)+(2.5 if primary else 0)-r*.30-gp*.20
    return round(min(100,max(0,total)),1),{'hook_strength':hs,'scroll_stop':ss,'curiosity_gap':cg,'purchase_desire':pd,'clarity':cl,'credibility':cr,'risk':r,'first_2s_power':first,'specificity':spec,'generic_penalty':gp}

def db_context():
    if not DB.exists():return {'connected':False,'counts':{},'hook_signals':[]}
    con=sqlite3.connect(DB);con.row_factory=sqlite3.Row;counts={}
    for t in ('sources','viral_hooks','short_form_scripts','ctas','product_demo_patterns'):
        try:counts[t]=con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except Exception:counts[t]=0
    sig=[]
    try:
        rows=con.execute("SELECT h.hook_id,h.source_id,h.hook_category,h.hook_formula,h.formula_family,h.quality_score FROM viral_hooks h JOIN sources s ON s.source_id=h.source_id WHERE s.usage_class IN ('COMMERCIAL_OK','TRANSFORM_ONLY') AND COALESCE(h.claim_risk,'LOW') NOT IN ('HIGH','PROHIBITED') ORDER BY h.quality_score DESC LIMIT 80").fetchall()
        for r in rows:
            raw=' '.join(str(r[k] or '').lower() for k in ('hook_category','hook_formula','formula_family'));a='comparison' if any(x in raw for x in ('compare','versus','비교')) else 'problem_attack' if any(x in raw for x in ('problem','pain','mistake','warning','문제')) else 'loss_aversion' if any(x in raw for x in ('loss','cost','fear')) else 'contrarian' if any(x in raw for x in ('contrarian','myth','reversal')) else 'proof' if any(x in raw for x in ('proof','review','demo','후기')) else 'curiosity' if any(x in raw for x in ('curiosity','secret','question','mystery')) else 'discovery';sig.append({'hook_id':r['hook_id'],'source_id':r['source_id'],'angle':a,'quality':float(r['quality_score'] or 0)})
    except Exception:pass
    con.close();return {'connected':counts.get('viral_hooks',0)>0,'counts':counts,'hook_signals':sig}

def tone(i):return {1:'정보 중심',2:'관심 유도',3:'강한 후킹',4:'퍼포먼스 광고',5:'극강 후킹'}[i]
def _base_templates(a,p,pain,pt,target,stake):
    return {
    'problem_attack':[f'아직도 {pain}? {p}보다 먼저 {pt}부터 보세요.',f'{p} 바꿔도 같은 불편이 반복된다면, 놓친 건 {pt}일 수 있습니다.',f'{stake} 싫다면 {p}에서 {pt}부터 보세요.',f'계속 {pain}? 이번엔 {p} 이름보다 {pt}부터 보세요.',f'{p} 문제가 아니라 선택 기준 문제일 수 있습니다. {pt}부터 보세요.'],
    'loss_aversion':[f'이거 모르고 {p} 사면 또 바꿀 수 있습니다. 먼저 {pt}부터 보세요.',f'가격부터 보고 {p} 고르면 가장 중요한 {pt}를 놓칩니다.',f'{stake} 전에 딱 하나, {pt}부터 비교하세요.',f'{p} 싸게 사는 것보다 두 번 안 사는 게 중요합니다. 기준은 {pt}입니다.',f'돈 쓰기 전에 5초만. {p}에서 {pt}가 실제로 되는지 보세요.'],
    'curiosity':[f'왜 {p} 잘 고르는 사람은 {pt}부터 볼까요?',f'처음엔 평범해 보이는데, {p}는 {pt}에서 갈립니다.',f'{target}이 {p} 살 때 마지막에 후회하는 포인트, 의외로 {pt}입니다.',f'{p} 설명에서 제일 먼저 찾아볼 한 줄은 {pt}입니다.',f'딱 하나만 비교한다면? {p}에서는 {pt}입니다.'],
    'comparison':[f'{p} 10개 비교해도 {pt} 안 보면 핵심을 놓칩니다.',f'비싼 {p}와 싼 {p}, 먼저 나란히 볼 건 {pt}입니다.',f'스펙이 비슷해도 실제 차이는 {pt}에서 드러납니다.',f'{p} 가격표 말고 {pt}를 먼저 비교해보세요.',f'브랜드 빼고 비교하면 남는 기준은 {pt}입니다.'],
    'contrarian':[f'광고는 다 좋다고 합니다. 그래서 저는 {p}에서 {pt} 하나만 봅니다.',f'{p}, 기능 많다고 좋은 게 아닙니다. {pt}가 약하면 의미 없습니다.',f'비싸다고 좋은 {p}? 저는 {pt} 확인 전엔 믿지 않습니다.',f'후기 많다고 끝이 아닙니다. {p}는 {pt}를 직접 보세요.',f'{p} 고를 때 유명한 것보다 중요한 건 {pt}입니다.'],
    'discovery':[f'이 {p}를 다시 보게 만든 건 거창한 기능이 아니라 {pt}였습니다.',f'별거 아닌 줄 알았던 {pt}, 실제로는 {p} 만족도를 가릅니다.',f'{p}에서 제일 의외였던 포인트? 바로 {pt}.',f'사고 나서 알기 전에 보세요. {p}의 {pt}가 핵심입니다.',f'{p} 볼 때 기준이 바뀐 이유는 하나. {pt}.'],
    'proof':[f'말은 빼고 보겠습니다. {p}의 {pt}, 실제로 되는지만 확인해보죠.',f'{p} 광고 문구 말고 {pt} 작동 장면만 보세요.',f'후기보다 빠른 확인법: {p}의 {pt}를 직접 보여드리겠습니다.',f'좋다는 말 대신 증거 하나. {p}에서 {pt}가 어떻게 보이는지 확인하세요.',f'{p}는 설명보다 시연이 빠릅니다. {pt}부터 보여드리죠.']}[a]
def hook_text(a,pc,i,v):
    p=pc['product'];pain=pc['pain_point'];pts=pc['selling_points'];pt=pts[v%min(3,len(pts))];target=pc['target'];stake=pc['stake'];text=_base_templates(a,p,pain,pt,target,stake)[v%5];g=v//5
    if i<=2:text=text.replace('또 바꿀 수 있습니다','후회할 수 있습니다').replace('10개','여러 개')
    elif i==3 and g:text=('잠깐, ' if g%2 else '구매 전에, ')+text
    elif i==4:
        if g==1:text='딱 10초만 보세요. '+text
        elif g>=2:text='후기 보기 전에 이것부터. '+text
    elif i==5:
        if g==1:text='지금 스크롤 넘기기 전에, '+text
        elif g==2:text='사고 나서 후회하기 전에, '+text
        elif g>=3:text='광고 문구는 잠깐 빼고, '+text
    return text

def generate_hooks(pc,ctx,n=30,intensity=4,min_score=80):
    effective=max(float(min_score),84.0 if intensity>=4 else float(min_score));sb={}
    for s in ctx.get('hook_signals',[]):
        if s['angle'] not in sb:sb[s['angle']]=s
    cand=[]
    for v in range(25):
        for a in ANGLE_ORDER:
            sig=sb.get(a);text=hook_text(a,pc,intensity,v);sc,z=score_hook(text,a,pc,intensity,min(3,(sig or {}).get('quality',0)/100*3))
            if sc>=effective:cand.append(Hook(0,text,a,a,sc,z['hook_strength'],z['scroll_stop'],z['curiosity_gap'],z['purchase_desire'],z['clarity'],z['credibility'],z['risk'],z['curiosity_gap'],z['purchase_desire'],z['hook_strength'],z['first_2s_power'],z['specificity'],z['generic_penalty'],(sig or {}).get('source_id'),(sig or {}).get('hook_id')))
    pool=sorted({h.text:h for h in cand}.values(),key=lambda h:(h.score,h.first_2s_power,h.specificity,-len(h.text)),reverse=True);sel=[];used=set()
    for h in pool:
        if h.angle not in used:sel.append(h);used.add(h.angle)
    for h in pool:
        if h not in sel:sel.append(h)
        if len(sel)>=n:break
    if len(sel)<n:raise RuntimeError(f'{effective}점 이상 고유 Hook이 {len(sel)}개뿐입니다.')
    for j,h in enumerate(sel[:n],1):h.rank=j
    return sel[:n],effective

def cta(i,pc):
    pt=pc['primary_selling_point'];p=pc['product'];return {1:f'{p}의 {pt}와 사용 조건을 확인해보세요.',2:f'관심 있다면 {pt}와 가격을 상세 페이지에서 비교해보세요.',3:f'비슷한 불편이 있다면 {pt}부터 지금 쓰는 제품과 비교해보세요.',4:f'지금 쓰는 제품과 {pt}만 나란히 비교해보세요. 차이가 보이면 그때 선택하면 됩니다.',5:f'계속 같은 불편을 참고 있었다면 {pt}, 그리고 가격부터 바로 비교해보세요. 선택은 확인한 뒤 하세요.'}[i]
def times(d):
    w=[12,20,28,25,15];st=[0];c=0
    for x in w[:-1]:c+=x;st.append(round(d*c/sum(w)))
    return list(zip(st,st[1:]+[d]))
def _points_line(pc,d):return ' · '.join(pc['selling_points'][:(3 if d>=45 else 2 if d>=30 else 1)])
def build_script(pc,h,d,a,i):
    p=pc['product'];pt=pc['primary_selling_point'];pain=pc['pain_point'];points=_points_line(pc,d);pref='사용자가 지정한 특징 기준으로 ' if pc['claim_verification_required'] else '';strong=i>=4
    tension=(f'{pain}. 이걸 계속 참고 쓰면 같은 불편에 또 시간과 돈을 쓰게 됩니다. 문제는 제품 이름보다 선택 기준입니다.' if strong else f'{pain}. 그래서 선택 기준을 먼저 정하는 게 중요합니다.')
    reveal=(f'그래서 {p}에서는 {pt}부터 봐야 합니다. {points}. 이 특징들이 실제로 {pc["buyer_motive"]}에 연결되는지 보겠습니다.' if strong else f'{p}에서 먼저 볼 포인트는 {pt}입니다. 실제 사용에서 체감되는지 확인해보세요.')
    proof=(f'{pref}말로는 다 좋다고 할 수 있습니다. 실제로는 이렇게 확인합니다. {pc["demo_action"]} 그리고 {pc["proof_action"]}' if strong else f'{pref}광고 문구보다 실제 작동과 사용 과정을 확인하는 게 좋습니다. {pt}가 체감되는지 직접 보세요.')
    C=[('HOOK',h.text,h.text,f'{p}과 문제 상황을 첫 1초에 동시에 제시한다.'),('TENSION',tension,'왜 계속 같은 불편이 생길까?',f'{pain}이 드러나는 실제 상황을 빠른 컷으로 보여준다.'),('REVEAL',reveal,f'핵심: {points}',pc['demo_action']),('PROOF',proof,'말보다 실제 작동',pc['proof_action']),('CTA',cta(i,pc),f'{pt} · 가격 · 조건 비교',f'{p}과 {points}를 한 화면에 정리한 엔드카드.')]
    return [{'time':f'{s}-{e}s','role':r,'spoken':sp,'onscreen':on,'visual':vi,'angle':a} for (r,sp,on,vi),(s,e) in zip(C,times(d))]
def emphasis_coverage(pc,b):
    req=pc['must_emphasize'];text=' '.join(x['spoken']+' '+x['onscreen'] for x in b);return 100.0 if not req else round(sum(x in text for x in req)/len(req)*100,1)
def script_score(h,b,pc):
    text=' '.join(x['spoken'] for x in b);r=risk_score(text);cov=emphasis_coverage(pc,b);pd=97 if pc['primary_selling_point'] in text else 82;cl=95 if pc['product'] in text else 84;cr=95 if not r else 82;gp=generic_penalty(text);tot=h.hook_strength*.22+h.scroll_stop*.18+h.curiosity_gap*.13+pd*.13+cl*.08+cr*.09+h.first_2s_power*.07+h.specificity*.04+cov*.06-r*.30-gp*.15
    return {'hook_strength':h.hook_strength,'scroll_stop_power':h.scroll_stop,'curiosity_gap':h.curiosity_gap,'purchase_desire':pd,'clarity':cl,'credibility':cr,'first_2s_power':h.first_2s_power,'specificity':h.specificity,'must_emphasize_coverage':cov,'generic_penalty':gp,'risk':r,'total':round(min(100,max(0,tot)),1)}
def competition(pc,hooks,i,min_score):
    by={};[by.setdefault(h.angle,h) for h in hooks];out=[]
    for a in ('loss_aversion','curiosity','problem_attack','comparison','contrarian'):
        h=by.get(a,hooks[0]);b=build_script(pc,h,30,a,i);s=script_score(h,b,pc);out.append({'copywriter':ANGLES[a][1],'angle':a,'angle_label':ANGLES[a][0],'hook':asdict(h),'script_30s':b,'scores':s,'qualified':s['total']>=min_score})
    return sorted(out,key=lambda x:(x['qualified'],x['scores']['total'],x['scores']['first_2s_power']),reverse=True)
def prompt(model,pc,b):
    base=f"Vertical 9:16 Korean short-form performance ad for {pc['product']}. Product category: {pc['category_label']}. Target audience: {pc['target']}. Scene timing: {b['time']}. Purpose: {b['role']}. Visual action: {b['visual']} Environment: {pc['environment']}. On-screen text concept: {b['onscreen']}. Fast first two seconds, immediate problem tension, clear product reveal, authentic product-focused commercial, realistic use demonstration, consistent packaging, no unsupported superlatives, fabricated reviews, fake scarcity, or unverified medical claims."
    return base+({'kling':' Controlled handheld-to-close-up motion, punchy first cut, smooth social-ad pacing.','veo':' Cinematic close-up, coherent continuity, realistic ambience, fast problem-to-product reveal.','seedance':' Dynamic but stable camera movement, strong first frame, clear problem/benefit contrast.'}[model])

def generate(product,*,category='',features=None,must_emphasize=None,pain_point='',target='일반 소비자',description='',intensity=4,min_score=80.0):
    if not (product or '').strip():raise ValueError('product is required')
    if intensity not in range(1,6):raise ValueError('intensity must be 1..5')
    log_status(f'[1/7] 상품 분석: {product}');pc=product_profile(product,category,features,must_emphasize,pain_point,target,description);ctx=db_context();log_status(f"[2/7] 카테고리={pc['category_label']} / 강조={pc['primary_selling_point']}")
    hooks,effective=generate_hooks(pc,ctx,30,intensity,min_score);top3=hooks[:3];log_status(f'[3/7] Hook 30개 / V2.5 Gate={effective} / TOP1={top3[0].score}점');comp=competition(pc,hooks,intensity,effective);win=next((x for x in comp if x['qualified']),comp[0]);wh=Hook(**win['hook']);log_status(f"[4/7] Creative Competition 우승={win['angle_label']} / {win['scores']['total']}점")
    scripts={};prompts={};coverage={}
    for d in (15,30,45):
        k=f'{d}s';b=build_script(pc,wh,d,win['angle'],intensity);scripts[k]=b;coverage[k]=emphasis_coverage(pc,b);prompts[k]={m:[prompt(m,pc,x) for x in b] for m in ('kling','veo','seedance')}
    log_status(f"[5/7] 강조점 Coverage={coverage}")
    if pc['must_emphasize'] and coverage['45s']<100:raise RuntimeError(f"필수 강조점 누락: coverage={coverage['45s']}")
    audit={'hook_count':len(hooks),'minimum_hook_score':min(h.score for h in hooks),'generic_hook_hits':sum(any(g in h.text for g in GENERIC) for h in hooks),'banned_hook_hits':sum(risk_score(h.text)>0 for h in hooks),'must_emphasize_coverage':coverage,'category_neutral':pc['category']=='beauty' or not any(x in ' '.join(b['spoken'] for b in scripts['30s']) for x in ('피부','제형','바르기'))};log_status('[6/7] 품질 감사 완료')
    data={'version':'2.5','product':pc['product'],'product_analysis':pc,'ad_settings':{'intensity':intensity,'intensity_label':tone(intensity),'minimum_score':effective,'requested_minimum_score':min_score,'discard_below_score':True,'v25_strong_gate':intensity>=4},'quality_audit':audit,'db_integration':{'connected':ctx.get('connected',False),'database':str(DB),'counts':ctx.get('counts',{}),'commercial_policy':'COMMERCIAL_OK + TRANSFORM_ONLY only; RESEARCH_ONLY/BLOCKED/UNKNOWN excluded from direct generation','selected_references':{},'hook_reference_ids':[{'hook_id':h.db_hook_id,'source_id':h.db_source_id,'category':h.category} for h in top3],'top3_diversity':{'unique_hook_ids':len({h.db_hook_id for h in top3 if h.db_hook_id is not None}),'unique_categories':len({h.category for h in top3})}},'hooks':[asdict(h) for h in hooks],'top3':[asdict(h) for h in top3],'creative_competition':comp,'winner':{'copywriter':win['copywriter'],'angle':win['angle'],'angle_label':win['angle_label'],'scores':win['scores']},'scripts_by_duration':scripts,'script_15s':scripts['15s'],'script_30s':scripts['30s'],'script_45s':scripts['45s'],'cta':cta(intensity,pc),'video_prompts_by_duration':prompts,'video_prompts':prompts['30s'],'claim_note':'사용자가 제공한 수치·성능·효능 특징은 광고 집행 전에 상품 상세페이지/공식 자료로 사실 확인이 필요합니다.'};log_status('[7/7] 생성 완료');return data

def render_md(d):
    pc=d['product_analysis'];s=d['ad_settings'];q=d['quality_audit'];out=[f"# Script Generator V2.5 — {d['product']}",'','## 상품 분석',f"- 카테고리: **{pc['category_label']}** (`{pc['category']}`)",f"- 타깃: {pc['target']}",f"- Pain Point: {pc['pain_point']}",f"- 반드시 강조: {pc['must_emphasize'] or '미입력 → AI 기본값 사용'}",f"- Selling Points: {pc['selling_points']}",f"- 광고 강도: {s['intensity']} / 5 · {s['intensity_label']}",f"- 품질 Gate: **{s['minimum_score']}점**",'','## 품질 감사',f"- Hook 30개: {q['hook_count']==30}",f"- 최저 Hook 점수: {q['minimum_hook_score']}",f"- Generic Hook hit: {q['generic_hook_hits']}",f"- 금지표현 Hook hit: {q['banned_hook_hits']}",f"- 강조점 Coverage: {q['must_emphasize_coverage']}",'','## TOP 3 Hooks']
    out += [f"{h['rank']}. **{h['text']}** — {h['score']}점 · {ANGLES[h['angle']][0]} · 첫2초 {h['first_2s_power']}" for h in d['top3']];out+=['','## Creative Competition']
    for j,x in enumerate(d['creative_competition'],1):out.append(f"{'🏆' if x['angle']==d['winner']['angle'] else '-'} {j}. {x['copywriter']} / {x['angle_label']} — **{x['scores']['total']}점** · 강조 {x['scores']['must_emphasize_coverage']}%")
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
        out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);safe=re.sub(r'[^0-9A-Za-z가-힣_-]+','_',a.product);(out/f'{safe}_script_v2.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');md=out/f'{safe}_script_v2.md';md.write_text(render_md(d),encoding='utf-8');print('DB connected:',d['db_integration']['connected']);print('Category:',d['product_analysis']['category_label']);print('Winner:',d['winner']);print('Quality audit:',d['quality_audit']);print('Generated:',md);return 0
    except Exception as e:
        tb=traceback.format_exc();print('ERROR:',e);print(tb);LOGGER.error('Script Generator V2.5 failed: %s\n%s',e,tb);return 1
if __name__=='__main__':raise SystemExit(main())