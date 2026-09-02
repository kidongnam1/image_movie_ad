from __future__ import annotations
import argparse, csv, hashlib, json, os, re, shutil, sqlite3, subprocess, sys
from pathlib import Path
from typing import Any, Iterable
from collections import defaultdict, Counter

TEXT_EXTS={'.json','.jsonl','.ndjson','.csv','.tsv','.md','.markdown','.txt','.yaml','.yml','.js','.ts','.jsx','.tsx','.py','.html','.htm','.toml','.ini','.xml','.vue','.svelte'}
SKIP_DIRS={'.git','node_modules','.next','dist','build','coverage','.venv','venv','__pycache__','.idea','.vscode'}
PROMPT_KEYS={'prompt','prompts','text','content','description','instruction','template','positive_prompt','negative_prompt','caption','query','system_prompt','user_prompt'}
TITLE_KEYS={'title','name','id','slug','category','type','style','tasktype'}
MODEL_KEYWORDS={
 'gpt_image_2':['gpt image 2','gpt-image-2','gpt_image_2','gptimage2'],
 'gpt4o_gpt_image_1':['gpt-4o','gpt4o','gpt-image-1','gpt image 1'],
 'midjourney':['midjourney','--ar','--stylize','--sref','--chaos'],
 'flux':['flux'],
 'nano_banana':['nano banana','nanobanana','gemini image'],
 'seedream':['seedream'],
 'stable_diffusion':['stable diffusion','sdxl','negative prompt','sampler'],
 'ideogram':['ideogram'],
 'seedance':['seedance'],
 'veo':['veo 3','veo3','veo 3.1','veo3.1'],
 'kling':['kling'],
 'runway':['runway','gen-4','gen4'],
 'sora':['sora'],
 'hailuo':['hailuo','minimax'],
 'wan':['wan 2','wan2','wan 3','wan3'],
 'luma':['luma','dream machine'],
 'pika':['pika'],
 'recraft':['recraft'],
 'qwen_image_3':['qwen image 3','qwen-image-3','qwen_image_3','qwen image 3.0'],
 'z_image':['z-image','z image turbo','z-image-turbo'],
 'ltx_video':['ltx video','ltx-2','ltx2','ltx video 2'],
 'cogvideox':['cogvideox','cogvideo x'],
 'hunyuan_video':['hunyuan video','hunyuanvideo','huanyuanvideo'],
 'higgsfield':['higgsfield','cinema studio','soul id','mcsla'],
 'mochi_video':['mochi video','genmo mochi'],
 'comfyui':['comfyui']
}
VISUAL_TERMS=['lighting','light','shadow','camera','lens','composition','texture','material','color','palette','depth of field','bokeh','studio','cinematic','photorealistic','product','portrait','editorial','typography','layout','angle','macro','wide shot','close-up','rim light','softbox','reflection','background']
VIDEO_TERMS=['motion','move','moving','dolly','pan','tilt','orbit','zoom','tracking','handheld','crane','drone','transition','cut','shot','sequence','slow motion','timelapse','camera movement','subject motion','physics','dialogue','audio','rack focus','push in','pull out']
NOISE_TERMS=['installation','npm install','pip install','license','contributing','pull request','github actions','table of contents','clone this repository']
AUTO_TAG_RULES={
 'product':['product','packshot','ecommerce','e-commerce','bottle','packaging','catalog'],
 'advertising':['advertising','advertisement','campaign','ad creative','commercial','brand visual'],
 'portrait':['portrait','headshot','face','beauty shot'],
 'fashion':['fashion','editorial','runway','streetwear','outfit','garment'],
 'food':['food','dish','restaurant','beverage','drink','dessert','coffee'],
 'architecture':['architecture','building','facade','real estate','property','house','villa'],
 'interior':['interior','room','living room','bedroom','kitchen','furniture'],
 'typography':['typography','poster text','lettering','font','wordmark','headline'],
 'poster':['poster','key visual','billboard','flyer'],
 'infographic':['infographic','diagram','chart','explainer','information design'],
 'ui_ux':['ui','ux','interface','dashboard','app screen','website mockup'],
 'social_media':['instagram','tiktok','reels','social media','xiaohongshu','thumbnail'],
 'ugc':['ugc','creator-style','influencer','testimonial','selfie review'],
 'cinematic':['cinematic','film','movie','anamorphic','cinematography'],
 'storyboard':['storyboard','shot list','sequence','scene 1','scene 2'],
 'anime':['anime','manga'],
 '3d':['3d render','cgi','octane','blender','unreal engine'],
 'photorealistic':['photorealistic','photo-realistic','realistic photography','hyper-realistic'],
 'camera_motion':['dolly','pan','tilt','orbit','tracking shot','handheld','crane','drone','rack focus','push in','pull out'],
 'dialogue_audio':['dialogue','voiceover','voice-over','audio','sound design','lip sync','speaking'],
 'image_to_video':['image to video','image-to-video','i2v','input image','reference image'],
 'editing':['edit the image','image editing','change only','preserve the','inpaint','replace only'],
 'logo_brand':['logo','wordmark','brand identity','brand system'],
 'science_technical':['scientific','technical diagram','cutaway','engineering','schematic'],
}

MODEL_PROFILES={
 'gpt_image_2':{'media':'image','structure':'natural language + layout/text constraints + materials/lighting','strong_at':'instruction following, editing, text/layout, product/design','hint':'State subject, composition, exact text/layout, materials, lighting, camera, and what must remain unchanged.'},
 'gpt4o_gpt_image_1':{'media':'image','structure':'descriptive natural language + visual intent','strong_at':'conceptual image generation, styles, visual examples','hint':'Describe the full scene and desired visual intent; preserve source attribution when adapting examples.'},
 'midjourney':{'media':'image','structure':'concise visual phrase + style + composition + parameters','strong_at':'aesthetics, fashion, editorial, concept art','hint':'Use concise visual descriptors; add aspect ratio and stylization parameters only when relevant.'},
 'flux':{'media':'image','structure':'subject + composition + photographic/art detail + light/material','strong_at':'photorealism, texture, structured visual detail','hint':'Prioritize clear subject, spatial relationships, materials, lighting and camera language.'},
 'nano_banana':{'media':'image','structure':'scene + subject + environment + light + camera/lens + edit constraints','strong_at':'natural-language editing, product/realistic imagery','hint':'Be explicit about what changes and what stays fixed; specify angle, lens and lighting.'},
 'seedream':{'media':'image','structure':'subject + style + layout + commercial design/text','strong_at':'commercial visuals, posters, design-heavy images','hint':'Specify layout hierarchy, key text, brand mood, subject and visual style.'},
 'stable_diffusion':{'media':'image','structure':'positive prompt + optional negative prompt + model/sampler context','strong_at':'custom workflows, reproducibility, local control','hint':'Keep positive and negative concepts separable and preserve model-specific parameters outside the semantic prompt.'},
 'ideogram':{'media':'image','structure':'subject + composition + explicit typography/text + design style','strong_at':'typography, posters, logos, UI/product mockups','hint':'Quote exact text, state placement/hierarchy, then describe design style, subject and composition.'},
 'seedance':{'media':'video','structure':'shot sequence + subject action + camera movement + timing/transitions','strong_at':'cinematic sequence, ads, UGC, multi-shot motion','hint':'Write the temporal sequence explicitly and separate subject motion from camera motion.'},
 'veo':{'media':'video','structure':'shot + camera + action + environment + cinematic treatment + audio if needed','strong_at':'cinematic scene direction and audiovisual prompting','hint':'Define shot type, camera behavior, action, environment and optional dialogue/audio.'},
 'kling':{'media':'video','structure':'start state + action/physics + camera + end state','strong_at':'motion realism, physical transitions','hint':'Describe motion mechanics and end state clearly; avoid conflicting movement instructions.'},
 'runway':{'media':'video','structure':'subject motion + camera motion + scene motion','strong_at':'image-to-video motion direction','hint':'If an input image already defines appearance, spend text budget on motion and camera behavior.'},
 'sora':{'media':'video','structure':'scene progression + action + camera + cinematic detail','strong_at':'coherent scene development and cinematic direction','hint':'Describe how the scene evolves over time, not just a static frame.'},
 'hailuo':{'media':'video','structure':'subject/action + camera + motion intensity + scene','strong_at':'dynamic short video','hint':'Use explicit action verbs, camera movement and motion intensity.'},
 'wan':{'media':'video','structure':'subject + action + camera + scene + temporal transition','strong_at':'general text/image-to-video workflows','hint':'Keep motion, scene and camera instructions distinct.'},
 'luma':{'media':'video','structure':'scene + subject motion + camera path','strong_at':'dreamlike/cinematic motion','hint':'Describe the camera path and one dominant subject motion.'},
 'pika':{'media':'video','structure':'subject transformation/motion + camera + effect','strong_at':'short transformations and effects','hint':'Keep the central transformation/effect explicit and concise.'},
 'qwen_image_3':{'media':'image','structure':'deliverable/use-case + goal + scene/subject + style + composition + exact text/data + constraints','strong_at':'text-heavy layouts, multilingual typography, e-commerce, infographics, consistent series','hint':'Define the deliverable first, quote exact on-image copy, state hierarchy and constraints, and separate facts from visual style.'},
 'z_image':{'media':'image','structure':'subject + visual style + composition + lighting + material/camera','strong_at':'fast image generation and editing workflows','hint':'Keep subject and composition explicit; use precise material, lighting and edit-preservation language.'},
 'ltx_video':{'media':'video','structure':'shot/scene + subject action + camera movement + temporal beats + dialogue/audio + settings','strong_at':'reproducible video prompts, camera movement, product video, dialogue and synchronized audio','hint':'Describe one temporal sequence at a time, keep camera motion separate from subject motion, and preserve generation settings/provenance.'},
 'cogvideox':{'media':'video','structure':'scene + action + temporal progression + camera + style','strong_at':'open video workflows and prompt-engineered text-to-video','hint':'Use concrete action verbs, temporal ordering and camera direction; avoid static image-only wording.'},
 'hunyuan_video':{'media':'video','structure':'scene + subject motion + camera + style + temporal consistency','strong_at':'open video generation and stylized motion workflows','hint':'Specify continuous motion, camera behavior and visual style without contradictory actions.'},
 'higgsfield':{'media':'video','structure':'creative intent + shot design + camera/motion control + character consistency + temporal beat + edit/extend constraints','strong_at':'cinematic ads, camera moves, character consistency, Seedance/Kling workflows','hint':'State the cinematic objective first, then camera/motion behavior, identity consistency, timing, and edit/extend constraints. Avoid mixing incompatible camera moves.'},
 'mochi_video':{'media':'video','structure':'scene + action + camera + visual mood + duration-aware progression','strong_at':'open text-to-video experiments','hint':'Favor a coherent single scene with explicit action and camera movement.'},
}

def run(cmd:list[str], cwd:Path|None=None, timeout:int|None=None)->tuple[int,str]:
    try:
        env=dict(os.environ); env.setdefault('GIT_LFS_SKIP_SMUDGE','1'); env.setdefault('GIT_TERMINAL_PROMPT','0'); p=subprocess.run(cmd,cwd=str(cwd) if cwd else None,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace',timeout=timeout,env=env)
        return p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:
        out=(e.stdout or '') + '\nTIMEOUT'
        return 124,out
    except Exception as e:
        return 125,f'{type(e).__name__}: {e}'

def slug(s:str)->str: return re.sub(r'[^A-Za-z0-9._-]+','_',s).strip('_')

def clone_or_update(repo:dict, root:Path, full:bool=True, retries:int=3, retry_delay:int=4, clone_timeout:int=900, no_pull:bool=False, text_only:bool=False)->dict:
    import time
    dest=root/'repos'/repo['media_type']/repo['model_family']/slug(repo['repo']); dest.parent.mkdir(parents=True,exist_ok=True)
    status={'repo':repo['repo'],'dest':str(dest),'status':'','message':'','attempts':0,'commit':''}
    if (dest/'.git').exists():
        if no_pull:
            code,out=0,'skipped pull (--no-pull)'
        else:
            code,out=run(['git','-c','core.longpaths=true','-C',str(dest),'pull','--ff-only'],timeout=clone_timeout)
        status['status']='updated' if code==0 and not no_pull else 'existing' if no_pull else 'update_failed'
        status['message']=out[-2000:]
        c,sha=run(['git','-C',str(dest),'rev-parse','HEAD'],timeout=60)
        if c==0: status['commit']=sha.strip()
        return status
    if dest.exists() and any(dest.iterdir()):
        status['status']='exists_non_git'; return status
    cmd=['git','-c','core.longpaths=true','clone','--depth','1','--no-tags','--single-branch']
    if text_only: cmd += ['--filter=blob:none','--no-checkout']
    elif not full: cmd += ['--filter=blob:none']
    cmd += [repo['url'],str(dest)]
    last=''
    for attempt in range(1,max(1,retries)+1):
        status['attempts']=attempt
        if dest.exists() and not (dest/'.git').exists():
            shutil.rmtree(dest,ignore_errors=True)
        code,out=run(cmd,timeout=clone_timeout); last=out
        if code==0:
            if text_only:
                patterns=['*.json','*.jsonl','*.ndjson','*.csv','*.tsv','*.md','*.markdown','*.txt','*.yaml','*.yml','*.js','*.ts','*.jsx','*.tsx','*.py','*.html','*.htm','*.toml','*.ini','*.xml','*.vue','*.svelte','LICENSE*','COPYING*']
                c1,o1=run(['git','-C',str(dest),'sparse-checkout','init','--no-cone'],timeout=120)
                c2,o2=run(['git','-C',str(dest),'sparse-checkout','set','--no-cone',*patterns],timeout=180) if c1==0 else (c1,o1)
                c3,o3=run(['git','-C',str(dest),'checkout'],timeout=clone_timeout) if c2==0 else (c2,o2)
                if c3!=0:
                    status['status']='sparse_checkout_failed'; status['message']=(o1+'\n'+o2+'\n'+o3)[-2500:]; return status
            status['status']='cloned'; status['message']=out[-2000:]
            c,sha=run(['git','-C',str(dest),'rev-parse','HEAD'],timeout=60)
            if c==0: status['commit']=sha.strip()
            return status
        if attempt < retries: time.sleep(max(1,retry_delay)*attempt)
    status['status']='clone_failed'; status['message']=last[-2000:]; return status

def likely_prompt_file(path:Path)->bool:
    if path.suffix.lower() not in TEXT_EXTS: return False
    n=path.name.lower(); good=any(x in n for x in ('prompt','readme','example','template','gallery','case','data','skill','workflow'))
    if good: return True
    try:
        if path.stat().st_size>8_000_000: return False
        sample=path.read_text(encoding='utf-8',errors='ignore')[:12000].lower()
        return 'prompt' in sample or '提示词' in sample or '提示語' in sample
    except Exception: return False

def iter_files(repo_dir:Path)->Iterable[Path]:
    for dp,dns,fns in os.walk(repo_dir):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            p=Path(dp)/fn
            try:
                if p.stat().st_size>50_000_000: continue
            except OSError: continue
            if likely_prompt_file(p): yield p

def clean_text(s:Any)->str:
    if s is None: return ''
    if not isinstance(s,str): s=json.dumps(s,ensure_ascii=False) if isinstance(s,(dict,list)) else str(s)
    return re.sub(r'\s+',' ',s).strip()

def model_guess(text:str, fallback:str)->str:
    low=text.lower(); hits=[]
    for m,keys in MODEL_KEYWORDS.items():
        if any(k in low for k in keys): hits.append(m)
    return '+'.join(hits[:4]) if hits else fallback

def rec_hash(prompt:str)->str:
    norm=re.sub(r'\s+',' ',prompt.lower()).strip(); return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def _term_in_text(term:str, low:str)->bool:
    term=term.lower()
    if len(term)<=3 and re.fullmatch(r'[a-z0-9]+',term):
        return re.search(r'(?<![a-z0-9_])'+re.escape(term)+r'(?![a-z0-9_])',low) is not None
    return term in low

def infer_tags(text:str)->list[str]:
    low=text.lower(); return [tag for tag,terms in AUTO_TAG_RULES.items() if any(_term_in_text(t,low) for t in terms)]

def model_fit_score(repo:dict,prompt:str,title:str='')->int:
    text=(title+' '+prompt).lower(); fam=repo.get('model_family','')
    score=50
    if fam=='midjourney':
        score += 12 if any(x in text for x in ['--ar','--stylize','--sref','--chaos']) else 0
        score += min(18,sum(3 for t in VISUAL_TERMS if t in text))
    elif fam in {'gpt_image_2','gpt4o_gpt_image_1','nano_banana','seedream','ideogram','flux','stable_diffusion','qwen_image_3','z_image'} or repo.get('media_type')=='image':
        score += min(24,sum(3 for t in VISUAL_TERMS if t in text))
        if fam=='ideogram' and any(t in text for t in ['typography','text','headline','logo','poster']): score += 12
        if fam=='stable_diffusion' and any(t in text for t in ['negative prompt','sampler','cfg','steps']): score += 10
        if fam=='qwen_image_3' and any(t in text for t in ['text (verbatim)','constraints','deliverable','hierarchy','multilingual','exact copy']): score += 12
    if repo.get('media_type')=='video':
        score += min(30,sum(3 for t in VIDEO_TERMS if t in text))
        if any(t in text for t in ['camera','shot','dolly','pan','orbit','tracking']): score += 8
        if any(t in text for t in ['sequence','transition','scene 1','scene 2']): score += 6
    return max(0,min(100,score))

def prompt_quality(repo:dict,prompt:str,title:str='')->int:
    text=(title+' '+prompt).lower(); score=20 + int(float(repo.get('repo_quality_score',70))*0.35); L=len(prompt)
    if 80 <= L <= 4000: score += 12
    elif 40 <= L <= 12000: score += 7
    elif L < 40: score -= 15
    terms=VISUAL_TERMS + (VIDEO_TERMS if repo.get('media_type')=='video' else [])
    score += min(18, sum(2 for t in terms if t in text))
    for keys in MODEL_KEYWORDS.values():
        if any(k in text for k in keys): score += 3
    if any(x in prompt for x in [':',',',';','\n','{','}','[',']']): score += 5
    if repo.get('media_type')=='video' and any(t in text for t in VIDEO_TERMS): score += 8
    if repo.get('media_type')=='image' and any(t in text for t in VISUAL_TERMS): score += 6
    score -= min(30, sum(10 for t in NOISE_TERMS if t in text))
    return max(0,min(100,score))

def quality_tier(score:int)->str: return 'S' if score>=90 else 'A' if score>=80 else 'B' if score>=65 else 'C' if score>=50 else 'D'

def language_guess(text:str)->str:
    ko=len(re.findall(r'[가-힣]',text)); zh=len(re.findall(r'[一-龥]',text)); ja=len(re.findall(r'[ぁ-ゟ゠-ヿ]',text)); latin=len(re.findall(r'[A-Za-z]',text))
    total=max(1,ko+zh+ja+latin)
    shares={'ko':ko/total,'zh':zh/total,'ja':ja/total,'en':latin/total}
    top=max(shares,key=shares.get)
    if shares[top]>=0.75: return top
    if sum(v>0.12 for v in shares.values())>=2: return 'mixed'
    return top if shares[top]>0 else 'other'

def input_mode_guess(repo:dict,text:str)->str:
    low=text.lower(); media=repo.get('media_type')
    if media=='video':
        if any(x in low for x in ['image to video','image-to-video','i2v','input image','reference image','first frame']): return 'image_to_video'
        return 'text_to_video'
    if any(x in low for x in ['edit the image','image editing','change only','preserve the','inpaint','replace only','input image','reference image']): return 'image_edit'
    return 'text_to_image'

def record(repo:dict,path:Path,title:str,prompt:str,meta:dict|None=None)->dict|None:
    prompt=clean_text(prompt)
    if len(prompt)<20: return None
    if len(prompt)>50000: prompt=prompt[:50000]
    txt=(title+' '+prompt+' '+str(path)).lower(); q=prompt_quality(repo,prompt,title); fit=model_fit_score(repo,prompt,title); combined=round(q*0.65+fit*0.35)
    return {
      'media_type':repo['media_type'],'model_family':repo['model_family'],'model_guess':model_guess(txt,repo['model_family']),'language_guess':language_guess(prompt),'input_mode_guess':input_mode_guess(repo,txt),'prompt_chars':len(prompt),
      'repo':repo['repo'],'source_file':str(path),'title':clean_text(title)[:500],'prompt':prompt,'prompt_hash':rec_hash(prompt),
      'duplicate_source_count':1,'repo_quality_score':int(float(repo.get('repo_quality_score',70))),'prompt_quality_score':q,'model_fit_score':fit,'combined_score':combined,'quality_tier':quality_tier(combined),
      'source_kind':repo.get('source_kind','corpus'),'source_role':repo.get('source_role',''),'specialization':repo.get('specialization',''),'use_case':repo.get('use_case',''),'auto_tags':'|'.join(infer_tags(txt)),
      'origin_status':repo.get('origin_status',''),'origin_confidence':float(repo.get('origin_confidence',0) or 0),
      'source_url':repo.get('url','').removesuffix('.git'),'license_spdx':repo.get('license_spdx','UNKNOWN'),'license_verified':repo.get('license_verified',False),
      'verified_at':repo.get('verified_at',''),'repo_commit':repo.get('_local_commit',''),'attribution':repo.get('repo',''),
      'metadata_json':json.dumps(meta or {},ensure_ascii=False)[:20000]
    }

def parse_json_obj(obj:Any, repo:dict, path:Path, parent_title:str='')->list[dict]:
    out=[]
    if isinstance(obj,list):
        for i,x in enumerate(obj): out += parse_json_obj(x,repo,path,parent_title or f'item_{i}')
    elif isinstance(obj,dict):
        title=' | '.join(clean_text(obj.get(k)) for k in TITLE_KEYS if obj.get(k) is not None)[:500] or parent_title; emitted=False
        for k,v in obj.items():
            kl=str(k).lower()
            if kl in PROMPT_KEYS:
                if isinstance(v,str):
                    r=record(repo,path,title or kl,v,{kk:obj.get(kk) for kk in TITLE_KEYS if kk in obj});
                    if r: out.append(r); emitted=True
                elif isinstance(v,list):
                    for j,item in enumerate(v):
                        if isinstance(item,str):
                            r=record(repo,path,title or f'{kl}_{j}',item); out.append(r) if r else None; emitted=True
                        elif isinstance(item,(dict,list)): out += parse_json_obj(item,repo,path,title); emitted=True
                elif isinstance(v,dict): out += parse_json_obj(v,repo,path,title); emitted=True
        if not emitted:
            for v in obj.values():
                if isinstance(v,(dict,list)): out += parse_json_obj(v,repo,path,title)
    return out

def parse_file(repo:dict,path:Path)->list[dict]:
    ext=path.suffix.lower(); out=[]
    try:
        if ext=='.json':
            with open(path,encoding='utf-8',errors='replace') as f: return parse_json_obj(json.load(f),repo,path)
        if ext in {'.jsonl','.ndjson'}:
            with open(path,encoding='utf-8',errors='replace') as f:
                for i,line in enumerate(f):
                    try: out += parse_json_obj(json.loads(line),repo,path,f'line_{i+1}')
                    except Exception: pass
            return out
        if ext in {'.csv','.tsv'}:
            delim='\t' if ext=='.tsv' else ','
            with open(path,encoding='utf-8-sig',errors='replace',newline='') as f:
                for i,row in enumerate(csv.DictReader(f,delimiter=delim)):
                    title=' | '.join(clean_text(row.get(k)) for k in row if k.lower() in TITLE_KEYS and row.get(k))[:500]
                    for k,v in row.items():
                        if k and k.lower() in PROMPT_KEYS and v:
                            r=record(repo,path,title or f'row_{i+2}',v,row); out.append(r) if r else None
            return out
        text=path.read_text(encoding='utf-8',errors='replace')
        for i,m in enumerate(re.finditer(r'```(?:json|text|prompt|markdown|md)?\s*\n(.*?)```',text,re.S|re.I)):
            s=m.group(1).strip()
            if len(s)>=40 and ('prompt' in s.lower() or len(s)<12000):
                r=record(repo,path,f'code_block_{i+1}',s); out.append(r) if r else None
        for i,ch in enumerate(re.split(r'\n\s*\n',text)):
            s=ch.strip()
            if len(s)<60 or len(s)>12000: continue
            low=s.lower()
            if ('prompt' in low or '提示词' in low or '提示語' in low or 'negative prompt' in low or re.search(r'--(?:ar|stylize|sref|chaos)\b',low)):
                r=record(repo,path,s.splitlines()[0][:300],s); out.append(r) if r else None
    except Exception: pass
    return out

def build_sqlite(records:list[dict], db:Path):
    if db.exists(): db.unlink()
    con=sqlite3.connect(db); cur=con.cursor()
    cur.execute('CREATE TABLE prompts(id INTEGER PRIMARY KEY, media_type TEXT, model_family TEXT, model_guess TEXT, language_guess TEXT, input_mode_guess TEXT, prompt_chars INTEGER, repo TEXT, source_file TEXT, title TEXT, prompt TEXT, prompt_hash TEXT, duplicate_source_count INTEGER, repo_quality_score INTEGER, prompt_quality_score INTEGER, model_fit_score INTEGER, combined_score INTEGER, quality_tier TEXT, source_kind TEXT, source_role TEXT, specialization TEXT, use_case TEXT, auto_tags TEXT, origin_status TEXT, origin_confidence REAL, source_url TEXT, license_spdx TEXT, license_verified TEXT, verified_at TEXT, repo_commit TEXT, attribution TEXT, metadata_json TEXT)')
    cols=['media_type','model_family','model_guess','language_guess','input_mode_guess','prompt_chars','repo','source_file','title','prompt','prompt_hash','duplicate_source_count','repo_quality_score','prompt_quality_score','model_fit_score','combined_score','quality_tier','source_kind','source_role','specialization','use_case','auto_tags','origin_status','origin_confidence','source_url','license_spdx','license_verified','verified_at','repo_commit','attribution','metadata_json']
    cur.executemany('INSERT INTO prompts('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',[tuple(r.get(k) for k in cols) for r in records])
    try:
        cur.execute("CREATE VIRTUAL TABLE prompts_fts USING fts5(title,prompt,repo,model_family,auto_tags,content='prompts',content_rowid='id')")
        cur.execute("INSERT INTO prompts_fts(rowid,title,prompt,repo,model_family,auto_tags) SELECT id,title,prompt,repo,model_family,auto_tags FROM prompts")
    except sqlite3.OperationalError: pass
    for col in ['prompt_hash','model_family','media_type','language_guess','input_mode_guess','combined_score','source_kind']: cur.execute(f'CREATE INDEX ix_prompts_{col} ON prompts({col})')
    con.commit(); con.close()

def _prompt_tokens(text:str)->set[str]:
    stop={'the','a','an','and','of','to','in','on','with','for','from','is','are','be','as','at','by','or','this','that','into','using','use','prompt','prompts','image','images','video','videos'}
    return {t for t in re.findall(r'[a-z0-9가-힣一-龥ぁ-ゟ゠-ヿ]+',text.lower()) if t not in stop and len(t)>1}

def _simhash64(text:str)->int:
    tokens=re.findall(r'[a-z0-9가-힣一-龥ぁ-ゟ゠-ヿ]+',text.lower())
    if not tokens: return 0
    feats=tokens + [tokens[i]+'_'+tokens[i+1] for i in range(len(tokens)-1)]
    vec=[0]*64
    for feat in feats[:4000]:
        h=int(hashlib.sha1(feat.encode('utf-8')).hexdigest()[:16],16)
        for b in range(64): vec[b] += 1 if (h>>b)&1 else -1
    out=0
    for b,v in enumerate(vec):
        if v>=0: out |= (1<<b)
    return out

def near_duplicate_report(records:list[dict], min_jaccard:float=0.82, max_pairs:int=50000)->list[dict]:
    """Approximate duplicate candidates via token MinHash buckets + Jaccard. Review only; never auto-delete."""
    items=[]
    for r in records:
        text=r.get('prompt','')
        if len(text)<60: continue
        toks=_prompt_tokens(text)
        if len(toks)<8: continue
        hashes=sorted((int(hashlib.sha1(t.encode('utf-8')).hexdigest()[:16],16) for t in toks))[:6]
        items.append((toks,_simhash64(text),hashes,r))
    buckets=defaultdict(list)
    for idx,(toks,sh,mins,r) in enumerate(items):
        for h in mins: buckets[h].append(idx)
    candidates=set()
    for ids in buckets.values():
        if len(ids)>500: ids=ids[:500]
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                a,b=ids[i],ids[j]
                if a!=b: candidates.add((min(a,b),max(a,b)))
    out=[]
    for a,b in candidates:
        ta,sha,_,r1=items[a]; tb,shb,_,r2=items[b]
        if r1.get('prompt_hash')==r2.get('prompt_hash'): continue
        jac=len(ta&tb)/max(1,len(ta|tb))
        ratio=min(len(ta),len(tb))/max(len(ta),len(tb))
        if jac>=min_jaccard and ratio>=0.70:
            out.append({'repo_a':r1.get('repo',''),'repo_b':r2.get('repo',''),'title_a':r1.get('title','')[:300],'title_b':r2.get('title','')[:300],'prompt_hash_a':r1.get('prompt_hash',''),'prompt_hash_b':r2.get('prompt_hash',''),'token_jaccard':round(jac,4),'token_length_ratio':round(ratio,4),'simhash_hamming':(sha^shb).bit_count(),'preview_a':r1.get('prompt','')[:700],'preview_b':r2.get('prompt','')[:700],'classification':'near_duplicate_review'})
            if len(out)>=max_pairs: break
    return sorted(out,key=lambda x:(x['token_jaccard'],-x['simhash_hamming']),reverse=True)

def repo_overlap_report(records:list[dict], min_prompts:int=8, threshold:float=0.85)->list[dict]:
    sets=defaultdict(set)
    for r in records: sets[r['repo']].add(r['prompt_hash'])
    repos=sorted(sets); out=[]
    for i,a in enumerate(repos):
        A=sets[a]
        if len(A)<min_prompts: continue
        for b in repos[i+1:]:
            B=sets[b]
            if len(B)<min_prompts: continue
            inter=len(A&B)
            if not inter: continue
            overlap=inter/min(len(A),len(B)); jacc=inter/len(A|B)
            if overlap>=threshold:
                out.append({'repo_a':a,'repo_b':b,'prompts_a':len(A),'prompts_b':len(B),'shared':inter,'overlap_coefficient':round(overlap,4),'jaccard':round(jacc,4),'classification':'probable_mirror_or_heavy_overlap' if overlap>=0.95 else 'heavy_overlap'})
    return sorted(out,key=lambda x:(x['overlap_coefficient'],x['shared']),reverse=True)

def write_csv(path:Path,rows:list[dict],fields:list[str]|None=None):
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        if not fields: return
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description='Download original AI prompt repos, extract/index prompts, score model fit, and detect cross-repo overlap.')
    ap.add_argument('--root',default='AI_PROMPT_LIBRARY')
    ap.add_argument('--manifest',default=str(Path(__file__).with_name('repos_manifest.json')))
    ap.add_argument('--priority',type=int,default=2,choices=[1,2,3])
    ap.add_argument('--index-only',action='store_true')
    ap.add_argument('--partial-clone',action='store_true')
    ap.add_argument('--include-candidates',action='store_true')
    ap.add_argument('--include-tooling',action='store_true',help='Also download/index prompt generators, enhancers and skills. Default corpus only.')
    ap.add_argument('--overlap-threshold',type=float,default=0.85)
    ap.add_argument('--verified-only',action='store_true',help='Only repositories explicitly verified as fork=false originals.')
    ap.add_argument('--media',choices=['image','video'],help='Download/index only one media type.')
    ap.add_argument('--model',help='Substring filter for model_family, e.g. qwen, ltx, seedance.')
    ap.add_argument('--min-repo-quality',type=int,default=0,help='Minimum repository quality score 0-100.')
    ap.add_argument('--retries',type=int,default=3,help='Clone retry count per repository.')
    ap.add_argument('--retry-delay',type=int,default=4,help='Base retry delay in seconds; multiplied by attempt.')
    ap.add_argument('--clone-timeout',type=int,default=900,help='Timeout in seconds for each git clone/pull.')
    ap.add_argument('--no-pull',action='store_true',help='Reuse already-downloaded repositories without git pull.')
    ap.add_argument('--text-only-clone',action='store_true',help='Sparse-checkout only prompt-friendly text files; skips heavy image/video assets.')
    args=ap.parse_args()
    root=Path(args.root).resolve(); root.mkdir(parents=True,exist_ok=True); (root/'indexes').mkdir(exist_ok=True); (root/'logs').mkdir(exist_ok=True)
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    repos=[]
    for r in manifest['repos']:
        if int(r.get('priority',2))>args.priority: continue
        is_candidate=(r.get('origin_status') in {'candidate','duplicate_excluded'} or not bool(r.get('active',True)))
        if is_candidate and not args.include_candidates: continue
        if r.get('source_kind')=='tooling' and not args.include_tooling: continue
        if r.get('source_kind')=='watchlist' and not args.include_candidates: continue
        if args.verified_only and r.get('origin_status')!='verified_original': continue
        if args.media and r.get('media_type')!=args.media: continue
        if args.model and args.model.lower() not in str(r.get('model_family','')).lower(): continue
        if int(float(r.get('repo_quality_score',0) or 0)) < args.min_repo_quality: continue
        repos.append(r)
    statuses=[]
    if not args.index_only:
        if not shutil.which('git'): print('ERROR: Git is not installed or not on PATH.',file=sys.stderr); sys.exit(2)
        status_path=root/'logs'/'clone_status.json'
        for n,r in enumerate(repos,1):
            print(f'[{n}/{len(repos)}] {r["repo"]} [{r.get("source_kind","corpus")}]')
            st=clone_or_update(r,root,full=not args.partial_clone,retries=args.retries,retry_delay=args.retry_delay,clone_timeout=args.clone_timeout,no_pull=args.no_pull,text_only=args.text_only_clone)
            statuses.append(st); print(' ',st['status'],'attempts=',st.get('attempts',0))
            status_path.write_text(json.dumps(statuses,ensure_ascii=False,indent=2),encoding='utf-8')
    records=[]; file_rows=[]; repo_rows=[]
    for r in repos:
        repo_dir=root/'repos'/r['media_type']/r['model_family']/slug(r['repo'])
        if not repo_dir.exists(): repo_rows.append({**r,'local_path':str(repo_dir),'downloaded':'N','prompt_files':0,'records':0}); continue
        c,sha=run(['git','-C',str(repo_dir),'rev-parse','HEAD'],timeout=30)
        r=dict(r); r['_local_commit']=sha.strip() if c==0 else ''
        files=list(iter_files(repo_dir)); before=len(records)
        for p in files:
            rs=parse_file(r,p); records.extend(rs); file_rows.append({'media_type':r['media_type'],'model_family':r['model_family'],'repo':r['repo'],'source_kind':r.get('source_kind','corpus'),'file':str(p),'size':p.stat().st_size,'records_extracted':len(rs)})
        repo_rows.append({**r,'local_path':str(repo_dir),'downloaded':'Y','prompt_files':len(files),'records':len(records)-before})
    groups=defaultdict(list)
    for r in records: groups[r['prompt_hash']].append(r)
    dedup=[]; dup_rows=[]
    for h,grp in groups.items():
        first=dict(sorted(grp,key=lambda x:(x['combined_score'],x['repo_quality_score']),reverse=True)[0]); first['duplicate_source_count']=len(grp); dedup.append(first)
        if len(grp)>1: dup_rows.append({'prompt_hash':h,'count':len(grp),'sources':' || '.join(f"{x['repo']}::{x['source_file']}" for x in grp)[:30000]})
    idx=root/'indexes'
    write_csv(idx/'repo_index.csv',repo_rows); write_csv(idx/'prompt_file_index.csv',file_rows); write_csv(idx/'duplicate_prompt_groups.csv',dup_rows)
    fields=['media_type','model_family','model_guess','language_guess','input_mode_guess','prompt_chars','repo','source_file','title','prompt','prompt_hash','duplicate_source_count','repo_quality_score','prompt_quality_score','model_fit_score','combined_score','quality_tier','source_kind','source_role','specialization','use_case','auto_tags','origin_status','origin_confidence','source_url','license_spdx','license_verified','verified_at','repo_commit','attribution','metadata_json']
    dedup=sorted(dedup,key=lambda x:(x['combined_score'],x['prompt_quality_score'],x['repo_quality_score']),reverse=True)
    write_csv(idx/'prompt_records.csv',dedup,fields)
    with open(idx/'prompt_records.jsonl','w',encoding='utf-8') as f:
        for r in dedup: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    by_model=idx/'by_model'; by_model.mkdir(exist_ok=True); model_groups=defaultdict(list)
    for r in dedup: model_groups[r['model_family']].append(r)
    model_summary=[]; top_all=[]
    for model,grp in sorted(model_groups.items()):
        ranked=sorted(grp,key=lambda x:(x['combined_score'],x['model_fit_score']),reverse=True); safe=slug(model); write_csv(by_model/f'{safe}.csv',ranked,fields); top_all.extend(ranked[:200])
        model_summary.append({'model_family':model,'media_type':grp[0].get('media_type',''),'unique_prompts':len(grp),'avg_combined_score':round(sum(x['combined_score'] for x in grp)/len(grp),1),'avg_model_fit':round(sum(x['model_fit_score'] for x in grp)/len(grp),1),'top_combined_score':max(x['combined_score'] for x in grp)})
    write_csv(idx/'model_summary.csv',model_summary); write_csv(idx/'top_prompts_by_model.csv',top_all,fields)
    by_tag=idx/'by_tag'; by_tag.mkdir(exist_ok=True); tag_groups=defaultdict(list)
    for r in dedup:
        for tag in (r.get('auto_tags') or '').split('|'):
            if tag: tag_groups[tag].append(r)
    for tag,grp in sorted(tag_groups.items()): write_csv(by_tag/f'{slug(tag)}.csv',sorted(grp,key=lambda x:x['combined_score'],reverse=True),fields)
    by_media=idx/'by_media'; by_media.mkdir(exist_ok=True)
    for media in ('image','video'): write_csv(by_media/f'{media}.csv',[r for r in dedup if r.get('media_type')==media],fields)
    overlap=repo_overlap_report(records,threshold=args.overlap_threshold); write_csv(idx/'repo_overlap_report.csv',overlap)
    near_dups=near_duplicate_report(dedup); write_csv(idx/'near_duplicate_report.csv',near_dups)
    profile_rows=[{'model':k,**v} for k,v in MODEL_PROFILES.items()]; write_csv(idx/'model_prompting_profiles.csv',profile_rows)
    (idx/'model_prompting_profiles.json').write_text(json.dumps(MODEL_PROFILES,ensure_ascii=False,indent=2),encoding='utf-8')
    build_sqlite(dedup,idx/'prompt_library.sqlite')
    summary={'version':'6.0','repos_selected':len(repos),'manifest_total':len(manifest.get('repos',[])),'include_candidates':bool(args.include_candidates),'include_tooling':bool(args.include_tooling),'verified_only':bool(args.verified_only),'media_filter':args.media,'model_filter':args.model,'min_repo_quality':args.min_repo_quality,'text_only_clone':bool(args.text_only_clone),'repos_downloaded':sum(x.get('downloaded')=='Y' for x in repo_rows),'prompt_files':len(file_rows),'raw_records':len(records),'unique_prompts':len(dedup),'duplicate_prompt_groups':len(dup_rows),'heavy_repo_overlap_pairs':len(overlap),'near_duplicate_review_pairs':len(near_dups),'source_kind_counts':dict(Counter(r.get('source_kind','corpus') for r in repos)),'media_counts':dict(Counter(r.get('media_type') for r in repos))}
    (idx/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
