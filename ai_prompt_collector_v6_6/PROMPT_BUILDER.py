from __future__ import annotations
import argparse, importlib.util, json, re, sqlite3, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / 'AI_PROMPT_LIBRARY' / 'indexes' / 'prompt_library.sqlite'
DEFAULT_OUT = HERE / 'AI_PROMPT_LIBRARY' / 'prompt_outputs'

spec = importlib.util.spec_from_file_location('collector', HERE / 'collect_and_index.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
MODEL_PROFILES = collector.MODEL_PROFILES

MODEL_ALIAS = {
    'gpt image':'gpt_image_2','gpt-image':'gpt_image_2','gpt image 2':'gpt_image_2','gptimage2':'gpt_image_2','gpt':'gpt_image_2','gpt-4o':'gpt_image_2',
    'midjourney':'midjourney','mj':'midjourney',
    'nano banana':'nano_banana','nano banana pro':'nano_banana','banana':'nano_banana',
    'flux':'flux','flux 3':'flux',
    'seedream':'seedream','seedream 5':'seedream','seedream 4.5':'seedream',
    'qwen':'qwen_image_3','qwen image':'qwen_image_3','qwen image 3':'qwen_image_3',
    'stable diffusion':'stable_diffusion','sd':'stable_diffusion',
    'recraft':'recraft','ideogram':'ideogram',
    'seedance':'seedance','seedance 2':'seedance','seedance 2.5':'seedance',
    'veo':'veo','veo 3':'veo',
    'kling':'kling','ltx':'ltx_video','ltx video':'ltx_video',
    'sora':'sora','higgsfield':'higgsfield','runway':'runway','pika':'pika','luma':'luma',
    'minimax':'minimax_hailuo','hailuo':'minimax_hailuo','wan':'wan','vidu':'vidu',
    'gemini':'veo','openai':'gpt_image_2',
}

COMMON_MODELS = [
    ('1', 'gpt_image_2', '이미지/편집/상세페이지'),
    ('2', 'midjourney', '감성/아트/패션 이미지'),
    ('3', 'flux', '범용 이미지'),
    ('4', 'nano_banana', '실사/카메라형 이미지'),
    ('5', 'seedream', '상업용 이미지/디자인'),
    ('6', 'qwen_image_3', '이미지'),
    ('7', 'seedance', '영상/광고/UGC'),
    ('8', 'veo', '영상/시네마틱'),
    ('9', 'kling', '영상/모션'),
    ('10', 'ltx_video', '영상/씬 구조'),
    ('11', 'higgsfield', '영상/광고'),
    ('12', 'runway', '영상'),
]

COMMON_USE_CASES = [
    ('1', 'advertising'),
    ('2', 'product'),
    ('3', 'detail page'),
    ('4', 'poster'),
    ('5', 'social media'),
    ('6', 'cinematic'),
    ('7', 'ugc'),
    ('8', 'portrait'),
    ('9', 'architecture'),
    ('10', 'infographic'),
]

IMAGE_HINTS = {'image', '사진', 'photo', '포스터', 'poster', '상세페이지', 'detail', '배너', '썸네일', 'thumbnail'}
VIDEO_HINTS = {'video', '영상', '모션', 'motion', '릴스', 'reels', '숏츠', 'shorts', '광고영상', 'commercial', 'ugc', 'shot', '씬', 'scene'}
VIDEO_FIRST_MODELS = {'higgsfield', 'veo', 'seedance', 'kling', 'ltx_video', 'runway', 'sora', 'pika', 'luma', 'wan', 'vidu', 'minimax_hailuo'}
IMAGE_FIRST_MODELS = {'gpt_image_2', 'midjourney', 'flux', 'nano_banana', 'seedream', 'qwen_image_3', 'stable_diffusion', 'ideogram', 'recraft'}


def canonical_model(name: str) -> str:
    key = re.sub(r'\s+', ' ', (name or '').strip().lower())
    key = MODEL_ALIAS.get(key, key.replace(' ', '_').replace('-', '_'))
    if key not in MODEL_PROFILES:
        matches = sorted([m for m in MODEL_PROFILES if key and key in m])
        if len(matches) == 1:
            return matches[0]
    return key


def guess_media(model_key: str, explicit_media: str | None) -> str:
    if explicit_media and explicit_media != 'auto':
        return explicit_media
    p = MODEL_PROFILES.get(model_key)
    if p and p.get('media') in {'image', 'video'}:
        return p['media']
    return 'image'


def infer_media_from_text(text: str, fallback: str = 'image') -> str:
    t = (text or '').lower()
    if any(k in t for k in VIDEO_HINTS):
        return 'video'
    if any(k in t for k in IMAGE_HINTS):
        return 'image'
    return fallback


def recommend_use_case(idea: str, requested: str | None = None) -> str:
    if requested and requested not in {'', 'auto'}:
        return requested
    t = (idea or '').lower()
    rules = [
        ('detail page', ['상세페이지', 'detail page', '상세']),
        ('ugc', ['ugc', '리뷰', 'review', 'unboxing', '사용후기']),
        ('social media', ['reels', 'shorts', 'instagram', '인스타', 'tiktok', '틱톡', 'sns']),
        ('poster', ['poster', '포스터']),
        ('cinematic', ['cinematic', '영화', '트레일러', 'trailer']),
        ('architecture', ['architecture', '건축', '인테리어', 'exterior', 'interior']),
        ('portrait', ['portrait', '인물', '모델']),
        ('product', ['product', '제품', '상품', '패키지']),
        ('advertising', ['advertising', '광고', 'campaign', '브랜딩', '홍보']),
    ]
    for label, keys in rules:
        if any(k.lower() in t for k in keys):
            return label
    return 'advertising'


def recommend_aspect_ratio(media: str, use_case: str, explicit: str | None = None) -> str:
    if explicit and explicit not in {'', 'auto'}:
        return explicit
    if media == 'video':
        if use_case in {'ugc', 'social media', 'advertising'}:
            return '9:16'
        return '16:9'
    if use_case in {'detail page'}:
        return '4:5'
    if use_case in {'poster', 'portrait', 'advertising'}:
        return '4:5'
    return '1:1'


def recommend_model(idea: str, providers: list[str] | None = None, media: str | None = None, use_case: str | None = None) -> tuple[str, str]:
    providers = [p.lower() for p in (providers or [])]
    media = media or infer_media_from_text(idea, 'image')
    use_case = recommend_use_case(idea, use_case)
    reason = []
    if media == 'video':
        if 'higgsfield' in providers and use_case in {'advertising', 'ugc', 'social media', 'product'}:
            reason.append('광고/UGC 영상에는 Higgsfield가 강점이 큽니다.')
            return 'higgsfield', ' '.join(reason)
        if 'gemini' in providers:
            reason.append('영상 생성은 Gemini 계열에서는 Veo 프로필로 매칭하는 것이 적합합니다.')
            return 'veo', ' '.join(reason)
        if 'openai' in providers:
            reason.append('OpenAI는 현재 이 라이브러리에서는 이미지 우선이므로, 영상은 Seedance/Veo 계열이 더 적합합니다.')
        return ('seedance' if use_case in {'advertising', 'ugc', 'social media'} else 'veo', '영상 목적과 용도에 맞춘 기본 추천입니다.')
    # image
    if 'openai' in providers:
        return 'gpt_image_2', 'OpenAI 구독을 활용한 이미지 생성에는 GPT Image 2가 가장 직접적입니다.'
    if 'gemini' in providers:
        return 'seedream', 'Gemini 구독은 있지만 현재 프롬프트 프로필 기준 이미지 목적에는 Seedream/범용 이미지 구조가 더 안정적입니다.'
    return 'gpt_image_2', '기본 이미지 추천 모델입니다.'


def auto_recommend_setup(idea: str, providers: list[str] | None = None, requested_media: str | None = None,
                         requested_use_case: str | None = None, requested_aspect_ratio: str | None = None) -> dict:
    media = requested_media if requested_media and requested_media != 'auto' else infer_media_from_text(idea, 'image')
    use_case = recommend_use_case(idea, requested_use_case)
    aspect_ratio = recommend_aspect_ratio(media, use_case, requested_aspect_ratio)
    model, reason = recommend_model(idea, providers=providers, media=media, use_case=use_case)
    return {
        'media': media,
        'use_case': use_case,
        'aspect_ratio': aspect_ratio,
        'model': model,
        'reason': reason,
    }


def slugify(text: str) -> str:
    s = re.sub(r'[^\w\-]+', '_', text.strip().lower())
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:60] or 'prompt'


def query_terms(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r'[\w-]+', text or '') if len(t) > 1]


def ask(prompt: str, default: str = '') -> str:
    suffix = f' [{default}]' if default else ''
    try:
        value = input(f'{prompt}{suffix}: ').strip()
    except EOFError:
        value = ''
    return value or default


def choose_from_list(title: str, items: list[tuple[str, str, str]] | list[tuple[str, str]], default: str = '') -> str:
    print('\n' + title)
    print('-' * len(title))
    for item in items:
        if len(item) == 3:
            k, value, desc = item
            print(f'  {k}. {value:<16}  {desc}')
        else:
            k, value = item
            print(f'  {k}. {value}')
    raw = ask('번호를 입력하거나 직접 이름을 입력하세요', default)
    for item in items:
        k, value = item[0], item[1]
        if raw == k:
            return value
    return raw


def search_examples(db_path: Path, query: str, media: str | None, model: str | None, use_case: str | None, limit: int = 5) -> list[dict]:
    if not db_path.exists():
        return []
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    terms = query_terms(query)
    where = ['p.combined_score>=?']
    params: list = [40]
    if media:
        where.append('p.media_type=?')
        params.append(media)
    if model:
        where.append('(p.model_family LIKE ? OR p.model_guess LIKE ?)')
        params += [f'%{model}%', f'%{model}%']
    if use_case:
        where.append('(p.use_case LIKE ? OR p.auto_tags LIKE ?)')
        params += [f'%{use_case}%', f'%{use_case}%']
    base = ' AND '.join(where)
    rows = []
    if terms:
        fts = ' AND '.join('"' + t.replace('"', '') + '"' for t in terms)
        try:
            rows = cur.execute(
                'SELECT p.* FROM prompts_fts f JOIN prompts p ON p.id=f.rowid WHERE prompts_fts MATCH ? AND ' + base + ' LIMIT 50',
                [fts] + params
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        if terms:
            term_sql = []
            term_params = []
            for t in terms:
                term_sql.append('(p.title LIKE ? OR p.prompt LIKE ? OR p.auto_tags LIKE ?)')
                q = f'%{t}%'
                term_params += [q, q, q]
            sql = 'SELECT p.* FROM prompts p WHERE ' + ' AND '.join(term_sql) + ' AND ' + base + ' LIMIT 50'
            rows = cur.execute(sql, term_params + params).fetchall()
        else:
            rows = cur.execute('SELECT p.* FROM prompts p WHERE ' + base + ' LIMIT 50', params).fetchall()

    def score(r):
        text = ((r['title'] or '') + ' ' + (r['prompt'] or '') + ' ' + (r['auto_tags'] or '')).lower()
        lexical = min(20, sum(4 for t in terms if t in text))
        trust = 8 if r['origin_status'] == 'verified_original' else 4 if r['origin_status'] == 'probable_original' else 0
        model_fit = int(r['model_fit_score'] or 0)
        combined = int(r['combined_score'] or 0)
        return lexical + trust + combined + model_fit

    out = [dict(r) for r in rows]
    out.sort(key=score, reverse=True)
    con.close()
    return out[:limit]


def build_dynamic_notes(media: str, options: dict | None = None) -> str:
    options = options or {}
    lines = []
    if media == 'image':
        mapping = [
            ('composition', 'Composition'), ('background', 'Background'), ('lighting', 'Lighting'),
            ('lens', 'Lens / camera'), ('text_layout', 'Text placement'), ('quality_focus', 'Quality focus')
        ]
    else:
        mapping = [
            ('duration', 'Duration'), ('scene_count', 'Scene count'), ('opening_shot', 'Opening shot'),
            ('camera_motion', 'Camera motion'), ('subject_motion', 'Subject motion'), ('ending_shot', 'Ending shot'),
            ('audio', 'Audio / dialogue')
        ]
    for key, label in mapping:
        val = (options.get(key) or '').strip()
        if val:
            lines.append(f'- {label}: {val}')
    return '\n'.join(lines)


def build_prompt(idea: str, model_key: str, media: str, use_case: str, style: str, aspect_ratio: str,
                 must_include: str, avoid: str, on_image_text: str, examples: list[dict], dynamic_options: dict | None = None) -> dict:
    p = MODEL_PROFILES.get(model_key, {})
    style_text = style.strip() or 'clean, high-quality, visually appealing'
    use_case = use_case.strip() or 'general'
    aspect_ratio = aspect_ratio.strip() or ('16:9' if media == 'video' else '1:1')
    must_text = must_include.strip() or 'Preserve the main idea faithfully.'
    avoid_text = avoid.strip() or 'Avoid incorrect text, duplicate objects, warped anatomy, fake claims, and irrelevant background clutter.'
    on_image_text = on_image_text.strip()
    dynamic_block = build_dynamic_notes(media, dynamic_options)
    example_lines = []
    for i, ex in enumerate(examples[:3], 1):
        title = (ex.get('title') or ex.get('repo') or 'Untitled').strip()
        tags = (ex.get('auto_tags') or '').strip()
        usec = (ex.get('use_case') or '').strip()
        example_lines.append(f'- Example {i}: {title} | repo={ex.get("repo","-")} | use_case={usec or "-"} | tags={tags or "-"}')
    examples_block = '\n'.join(example_lines) if example_lines else '- No local indexed examples found. Build from model profile only.'
    hint = p.get('hint', '')
    strong_at = p.get('strong_at', '')
    structure = p.get('structure', '')

    shared_constraints = f"""
Constraints:
- {avoid_text}
- Do not invent unsupported certifications, scientific claims, review counts, labels, brand facts, or numbers.
- Keep the result production-ready and aligned with the stated use case.
"""

    if media == 'image':
        final_prompt = f"""Create an {use_case} image based on this core idea: {idea}

Style and mood:
- {style_text}

Visual direction:
- Use a composition that clearly supports the {use_case} goal.
- Ensure the subject is easy to understand at first glance.
- Match the output to a polished, production-ready image.
- Preferred aspect ratio: {aspect_ratio}

Must include:
- {must_text}

Model-specific guidance:
- Target model: {model_key}
- Best structure: {structure}
- Strong at: {strong_at}
- Guidance: {hint}

Construction checklist:
- subject / hero element
- environment or background
- composition and framing
- lighting and color mood
- camera angle or rendering medium
- materials and surface detail
- text or layout treatment if relevant
- realism/stylization balance
"""
        if dynamic_block:
            final_prompt += f"""
Image-specific directions:
{dynamic_block}
"""
        if on_image_text:
            final_prompt += f"""
Required on-image text:
- Render this text clearly and accurately: \"{on_image_text}\"
"""
        final_prompt += shared_constraints + '\n- Keep typography clean and legible if text is included.\n'
        short_prompt = f"{idea}. {style_text}. {use_case} image. Aspect ratio {aspect_ratio}. Must include: {must_text}. Avoid: {avoid_text}"
    else:
        final_prompt = f"""Create a {use_case} video based on this core idea: {idea}

Style and mood:
- {style_text}

Video direction:
- Preferred aspect ratio: {aspect_ratio}
- Build a clear beginning, motion phase, and ending frame.
- Emphasize physically believable movement and camera behavior.

Must include:
- {must_text}

Model-specific guidance:
- Target model: {model_key}
- Best structure: {structure}
- Strong at: {strong_at}
- Guidance: {hint}

Construction checklist:
- opening shot / initial state
- subject action and timing
- camera movement
- scene motion and environmental effects
- lighting and mood
- transition or end state
- audio/dialogue only if truly needed
"""
        if dynamic_block:
            final_prompt += f"""
Video-specific directions:
{dynamic_block}
"""
        if on_image_text:
            final_prompt += f"""
Required visible text in frame (only if appropriate):
- \"{on_image_text}\"
"""
        final_prompt += shared_constraints + f'- Keep the motion elegant, coherent, and useful for the intended {use_case}.\n'
        short_prompt = f"{idea}. {style_text}. {use_case} video. Aspect ratio {aspect_ratio}. Must include: {must_text}. Avoid: {avoid_text}"

    markdown = f"""# Prompt Builder Output

- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Target model: {model_key}
- Media: {media}
- Use case: {use_case}
- Aspect ratio: {aspect_ratio}

## Input Summary
- Idea: {idea}
- Style: {style_text}
- Must include: {must_text}
- Avoid: {avoid_text}
- On-image text: {on_image_text or '-'}

## Dynamic Options
{dynamic_block or '- none -'}

## Referenced Local Examples
{examples_block}

## Final Prompt
{final_prompt}

## Short Prompt
{short_prompt}
"""
    return {
        'model': model_key,
        'media': media,
        'use_case': use_case,
        'aspect_ratio': aspect_ratio,
        'examples': examples,
        'dynamic_options': dynamic_options or {},
        'final_prompt': final_prompt.strip(),
        'short_prompt': short_prompt.strip(),
        'markdown': markdown,
    }


def interactive_args(args):
    print('=' * 72)
    print('AI PROMPT BUILDER')
    print('=' * 72)
    print('원하는 결과를 설명하면, 보유한 프롬프트 라이브러리와 AI별 규칙을 참고해')
    print('최종 프롬프트를 생성합니다.\n')

    if not args.idea:
        args.idea = ask('무엇을 만들까요? 예: 고급 향수 광고 이미지')
    if not args.model:
        raw_model = choose_from_list('자주 쓰는 AI 모델', COMMON_MODELS, 'gpt_image_2')
        args.model = raw_model
    if not args.media:
        args.media = ask('미디어 유형은 무엇인가요? image 또는 video', '')
    if not args.use_case:
        args.use_case = choose_from_list('용도를 선택하세요', COMMON_USE_CASES, 'advertising')
    if not args.style:
        args.style = ask('원하는 스타일/분위기는 무엇인가요?', 'clean, polished, high quality')
    if not args.aspect_ratio:
        default_ar = '16:9' if guess_media(canonical_model(args.model), args.media) == 'video' else '1:1'
        args.aspect_ratio = ask('화면비는 무엇인가요? 예: 1:1 / 4:5 / 9:16 / 16:9', default_ar)
    if args.must_include is None:
        args.must_include = ask('반드시 포함할 요소는 무엇인가요?', '')
    if args.avoid is None:
        args.avoid = ask('피하고 싶은 요소는 무엇인가요?', 'bad text, distortion, clutter')
    if args.on_image_text is None:
        args.on_image_text = ask('이미지/영상 안에 꼭 들어가야 할 텍스트가 있나요?', '')
    return args


def print_examples(examples: list[dict]) -> None:
    if not examples:
        print('\n참고 예제: 로컬 인덱스 예제가 없어 모델 프로필만 사용합니다.')
        return
    print('\n참고된 로컬 예제 TOP 결과')
    print('-' * 72)
    for i, ex in enumerate(examples, 1):
        print(f'[{i}] {(ex.get("title") or "Untitled")[:80]}')
        print(f'    repo={ex.get("repo") or "-"} | model={ex.get("model_family") or ex.get("model_guess") or "-"} | score={ex.get("combined_score") or "-"}')
        tags = (ex.get('auto_tags') or '')[:120]
        if tags:
            print(f'    tags={tags}')


def main() -> int:
    ap = argparse.ArgumentParser(description='Build a new prompt from your idea + local prompt library + model-specific optimization.')
    ap.add_argument('--idea')
    ap.add_argument('--model')
    ap.add_argument('--media', choices=['image', 'video'])
    ap.add_argument('--use-case', dest='use_case')
    ap.add_argument('--style')
    ap.add_argument('--aspect-ratio', dest='aspect_ratio')
    ap.add_argument('--must-include', dest='must_include', nargs='?', const='')
    ap.add_argument('--avoid', nargs='?', const='')
    ap.add_argument('--on-image-text', dest='on_image_text', nargs='?', const='')
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--output-dir', default=str(DEFAULT_OUT))
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--non-interactive', action='store_true')
    a = ap.parse_args()

    if not a.non_interactive:
        a = interactive_args(a)
    missing = [name for name in ['idea', 'model'] if not getattr(a, name)]
    if missing:
        print('ERROR: missing required inputs:', ', '.join(missing))
        return 2

    model_key = canonical_model(a.model)
    if model_key not in MODEL_PROFILES:
        print('Unknown model. Available models:')
        print(', '.join(sorted(MODEL_PROFILES)))
        return 2

    media = guess_media(model_key, a.media)
    query = ' '.join(x for x in [a.idea, a.style, a.use_case] if x)
    examples = search_examples(Path(a.db), query=query, media=media, model=model_key, use_case=a.use_case, limit=a.limit)
    result = build_prompt(
        idea=a.idea,
        model_key=model_key,
        media=media,
        use_case=a.use_case or 'general',
        style=a.style or '',
        aspect_ratio=a.aspect_ratio or '',
        must_include=a.must_include or '',
        avoid=a.avoid or '',
        on_image_text=a.on_image_text or '',
        examples=examples,
        dynamic_options={},
    )

    out_dir = Path(a.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = f'{ts}_{slugify(a.idea)}_{result["model"]}'
    txt_path = out_dir / f'{base}.txt'
    md_path = out_dir / f'{base}.md'
    json_path = out_dir / f'{base}.json'

    txt_path.write_text(result['final_prompt'] + '\n', encoding='utf-8')
    md_path.write_text(result['markdown'], encoding='utf-8')
    json_path.write_text(json.dumps({
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'input': {
            'idea': a.idea,
            'model': result['model'],
            'media': result['media'],
            'use_case': result['use_case'],
            'style': a.style or '',
            'aspect_ratio': result['aspect_ratio'],
            'must_include': a.must_include or '',
            'avoid': a.avoid or '',
            'on_image_text': a.on_image_text or '',
        },
        'examples': [
            {
                'title': ex.get('title'),
                'repo': ex.get('repo'),
                'model_family': ex.get('model_family'),
                'use_case': ex.get('use_case'),
                'specialization': ex.get('specialization'),
                'auto_tags': ex.get('auto_tags'),
                'combined_score': ex.get('combined_score'),
            } for ex in examples
        ],
        'final_prompt': result['final_prompt'],
        'short_prompt': result['short_prompt'],
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print_examples(examples)
    print('\n' + '=' * 72)
    print('PROMPT BUILDER COMPLETE')
    print('=' * 72)
    print('Target model :', result['model'])
    print('Media        :', result['media'])
    print('Use case     :', result['use_case'])
    print('Aspect ratio :', result['aspect_ratio'])
    print('Examples used:', len(examples))
    print('\nFINAL PROMPT\n')
    print(result['final_prompt'])
    print('\nSaved files:')
    print('-', txt_path)
    print('-', md_path)
    print('-', json_path)
    return 0


def extract_scene_count(dynamic_options: dict | None = None, default: int = 3) -> int:
    dynamic_options = dynamic_options or {}
    preferred = str(dynamic_options.get('scene_count') or '').strip()
    if preferred:
        m = re.search(r'(\d+)', preferred)
        if m:
            n = int(m.group(1))
            return max(2, min(n, 8))
    text = ' '.join(str(v) for k, v in dynamic_options.items() if v and k != 'duration')
    m = re.search(r'(\d+)', text)
    if not m:
        return default
    n = int(m.group(1))
    return max(2, min(n, 8))


def build_storyboard(idea: str, media: str, use_case: str, style: str, aspect_ratio: str,
                     must_include: str = '', on_image_text: str = '', dynamic_options: dict | None = None,
                     target_model: str = '') -> str:
    dynamic_options = dynamic_options or {}
    use_case = use_case or 'general'
    style = style or 'clean, high-quality, visually appealing'
    aspect_ratio = aspect_ratio or ('16:9' if media == 'video' else '1:1')
    must_include = must_include or 'main subject and key selling elements'
    on_image_text = on_image_text or ''

    if media == 'image':
        lines = [
            '# Storyboard / Shot Plan',
            '',
            f'- Idea: {idea}',
            f'- Target model: {target_model or "-"}',
            f'- Media: image',
            f'- Use case: {use_case}',
            f'- Aspect ratio: {aspect_ratio}',
            '',
            '## Image Layout Plan',
            f'1. Hero frame: {idea}',
            f'   - Style: {style}',
            f'   - Must include: {must_include}',
            f'   - Composition: {dynamic_options.get("composition") or "clear hero composition"}',
            f'   - Background: {dynamic_options.get("background") or "clean supporting background"}',
            f'   - Lighting: {dynamic_options.get("lighting") or "polished commercial lighting"}',
            f'   - Lens / camera: {dynamic_options.get("lens") or "commercial product photography"}',
            f'   - Text layout: {dynamic_options.get("text_layout") or "minimal and readable"}',
            f'   - Quality focus: {dynamic_options.get("quality_focus") or "high-end finish"}',
        ]
        if on_image_text:
            lines.append(f'   - On-image text: {on_image_text}')
        lines += [
            '',
            '## Usage Notes',
            '- Use this plan for a single polished hero image.',
            '- If variations are needed, keep the same subject and lighting while changing framing or background density.',
        ]
        return '\n'.join(lines)

    scene_count = extract_scene_count(dynamic_options, 3)
    opening = dynamic_options.get('opening_shot') or 'Introduce the subject with a strong opening hero shot.'
    camera = dynamic_options.get('camera_motion') or 'Use elegant, smooth camera motion.'
    subject_motion = dynamic_options.get('subject_motion') or 'Show subtle product or subject motion.'
    ending = dynamic_options.get('ending_shot') or 'Finish on a strong centered hero frame.'
    duration = dynamic_options.get('duration') or '5-8 seconds'
    audio = dynamic_options.get('audio') or 'No dialogue, premium ambient sound.'

    lines = [
        '# Storyboard / Shot Plan',
        '',
        f'- Idea: {idea}',
        f'- Target model: {target_model or "-"}',
        f'- Media: video',
        f'- Use case: {use_case}',
        f'- Aspect ratio: {aspect_ratio}',
        f'- Duration: {duration}',
        f'- Scene count: {scene_count}',
        '',
        '## Scene Breakdown',
    ]

    for idx in range(1, scene_count + 1):
        if idx == 1:
            shot = opening
            motion = camera
            action = subject_motion
        elif idx == scene_count:
            shot = ending
            motion = 'Slow settle or final reveal.'
            action = 'Resolve the product/subject into a clean ending composition.'
        else:
            shot = f'Build the middle sequence for {idea} while emphasizing the core value or selling point.'
            motion = camera
            action = subject_motion
        lines += [
            f'### Scene {idx}',
            f'- Shot goal: {shot}',
            f'- Visual mood: {style}',
            f'- Must include: {must_include}',
            f'- Camera: {motion}',
            f'- Subject action: {action}',
            f'- Notes: Keep pacing coherent with the {use_case} goal.',
        ]
        if on_image_text and idx == scene_count:
            lines.append(f'- Visible end text (if appropriate): {on_image_text}')
        lines.append('')

    lines += [
        '## Audio / Delivery',
        f'- {audio}',
        '',
        '## Usage Notes',
        '- Keep transitions smooth and physically believable.',
        '- Maintain visual continuity across all scenes.',
    ]
    return '\n'.join(lines)


def build_target_variant(target: str, idea: str, style: str = '', use_case: str = 'auto', aspect_ratio: str = 'auto',
                         must_include: str = '', avoid: str = '', on_image_text: str = '',
                         dynamic_options: dict | None = None, examples: list[dict] | None = None) -> dict:
    target = (target or '').lower()
    if target in {'openai', 'gpt', 'gpt_image', 'gpt_image_2'}:
        model_key, media = 'gpt_image_2', 'image'
        use_case_final = recommend_use_case(idea, use_case if use_case != 'auto' else 'advertising')
        ar = recommend_aspect_ratio(media, use_case_final, aspect_ratio)
    elif target in {'veo', 'gemini'}:
        model_key, media = 'veo', 'video'
        use_case_final = recommend_use_case(idea, use_case if use_case != 'auto' else 'advertising')
        ar = recommend_aspect_ratio(media, use_case_final, aspect_ratio)
    elif target in {'higgsfield', 'higgs'}:
        model_key, media = 'higgsfield', 'video'
        use_case_final = recommend_use_case(idea, use_case if use_case != 'auto' else 'advertising')
        if use_case_final == 'general':
            use_case_final = 'advertising'
        ar = recommend_aspect_ratio(media, use_case_final, aspect_ratio if aspect_ratio != 'auto' else '9:16')
    else:
        model_key = canonical_model(target)
        media = guess_media(model_key, None)
        use_case_final = recommend_use_case(idea, use_case)
        ar = recommend_aspect_ratio(media, use_case_final, aspect_ratio)
    result = build_prompt(
        idea=idea, model_key=model_key, media=media, use_case=use_case_final, style=style,
        aspect_ratio=ar, must_include=must_include, avoid=avoid, on_image_text=on_image_text,
        examples=examples or [], dynamic_options=dynamic_options or {}
    )
    storyboard = build_storyboard(idea, media, use_case_final, style, ar, must_include, on_image_text, dynamic_options or {}, model_key)
    result['storyboard'] = storyboard
    return result


if __name__ == '__main__':
    raise SystemExit(main())
