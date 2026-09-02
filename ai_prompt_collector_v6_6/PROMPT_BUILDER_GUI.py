from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

import PROMPT_BUILDER as pb

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / 'AI_PROMPT_LIBRARY' / 'indexes' / 'prompt_library.sqlite'
DEFAULT_OUT = HERE / 'AI_PROMPT_LIBRARY' / 'prompt_outputs'

MODEL_LABELS = {
    'gpt_image_2': 'GPT Image 2', 'midjourney': 'Midjourney', 'flux': 'Flux', 'nano_banana': 'Nano Banana',
    'seedream': 'Seedream', 'qwen_image_3': 'Qwen Image 3', 'stable_diffusion': 'Stable Diffusion',
    'ideogram': 'Ideogram', 'recraft': 'Recraft', 'seedance': 'Seedance', 'veo': 'Veo', 'kling': 'Kling',
    'ltx_video': 'LTX Video', 'higgsfield': 'Higgsfield', 'runway': 'Runway', 'sora': 'Sora',
    'minimax_hailuo': 'Hailuo / MiniMax', 'wan': 'Wan', 'luma': 'Luma', 'pika': 'Pika',
}
LABEL_TO_MODEL = {v: k for k, v in MODEL_LABELS.items() if k in pb.MODEL_PROFILES}
MODEL_TO_LABEL = {k: v for v, k in LABEL_TO_MODEL.items()}
USE_CASES = ['auto', 'advertising', 'product', 'detail page', 'poster', 'social media', 'cinematic', 'ugc', 'portrait', 'architecture', 'infographic', 'fashion', 'food', 'general']
ASPECTS = ['auto', '1:1', '4:5', '3:4', '9:16', '16:9', '21:9']
OUTPUT_TYPES = [('auto', '자동 판단'), ('image', '이미지'), ('video', '동영상')]
SERVICE_KEYS = ['OpenAI', 'Gemini', 'Higgsfield']
CATEGORY_PRESETS = {
    '직접 설정': {},
    '화장품': {
        'use_case': 'advertising',
        'style': 'luxury commercial beauty, premium clean finish, photorealistic product advertising',
        'must_include': '제품 형태, 용기 재질, 라벨과 패키징을 정확하게 보존하고 제품이 주인공으로 보이게 구성',
        'avoid': '가짜 효능·인증·수치, 왜곡된 용기, 잘못된 라벨, 과도한 피부 보정, 지저분한 배경',
        'image': {
            'composition': 'centered hero product composition with controlled negative space',
            'background': 'premium dark or clean studio background with subtle reflective surface',
            'lighting': 'soft beauty key light with elegant rim light and controlled specular highlights',
            'lens': '85mm commercial beauty/product photography',
            'text_layout': 'minimal premium typography with clear hierarchy',
            'quality_focus': 'accurate glass/plastic texture, clean reflections, premium cosmetic finish',
        },
        'video': {
            'duration': '6-8 seconds',
            'scene_count': '3 scenes',
            'opening_shot': 'macro close-up introducing the cosmetic product and packaging',
            'camera_motion': 'slow dolly-in with subtle orbit and controlled macro movement',
            'subject_motion': 'elegant moving reflections, subtle particles or product texture motion',
            'ending_shot': 'clean centered hero product shot with premium end-frame composition',
            'audio': 'premium ambient sound, no dialogue unless requested',
        },
    },
    '건축': {
        'use_case': 'architecture',
        'style': 'photorealistic architectural visualization, refined material realism, professional real-estate presentation',
        'must_include': '건물의 형태, 층수, 개구부, 재료, 주변 맥락과 공간 비례를 일관되게 유지',
        'avoid': '휘어진 수직선, 불가능한 구조, 비정상적인 창문 반복, 과장된 스케일, 실제와 다른 재료',
        'image': {
            'composition': 'architectural hero framing with strong perspective control and readable massing',
            'background': 'realistic surrounding streetscape, sky and landscaping appropriate to the project',
            'lighting': 'soft daylight or golden-hour architectural lighting with realistic shadows',
            'lens': '24-35mm tilt-shift architectural photography, corrected verticals',
            'text_layout': 'clean architectural presentation labels only when requested',
            'quality_focus': 'accurate materials, facade joints, glazing, scale and vertical geometry',
        },
        'video': {
            'duration': '8-12 seconds',
            'scene_count': '4 scenes',
            'opening_shot': 'wide establishing exterior shot revealing the full building massing',
            'camera_motion': 'slow cinematic crane, dolly or orbit with stable corrected perspective',
            'subject_motion': 'subtle environmental movement such as trees, people and realistic traffic',
            'ending_shot': 'signature facade or entrance hero shot with clear architectural identity',
            'audio': 'subtle urban/ambient sound, no dialogue unless requested',
        },
    },
    '물류': {
        'use_case': 'advertising',
        'style': 'clean industrial corporate visual, realistic logistics operation, professional B2B presentation',
        'must_include': '요청한 창고·랙·장비·화물·작업 동선을 정확하고 안전한 산업 현장으로 표현',
        'avoid': '위험한 지게차 동선, 보호구 누락, 비현실적인 적재, 왜곡된 팔레트/컨테이너, 과장된 자동화',
        'image': {
            'composition': 'wide industrial hero composition with clear operational flow and scale',
            'background': 'organized warehouse or logistics yard with clean lanes and realistic equipment',
            'lighting': 'bright neutral industrial lighting with realistic daylight contribution',
            'lens': '24-35mm documentary/industrial photography',
            'text_layout': 'clear B2B information hierarchy with restrained corporate typography',
            'quality_focus': 'accurate racks, pallets, forklifts, containers, floor markings and safety details',
        },
        'video': {
            'duration': '8-12 seconds',
            'scene_count': '4 scenes',
            'opening_shot': 'wide establishing shot of the logistics facility and organized operations',
            'camera_motion': 'smooth tracking shot following the operational flow, with occasional elevated reveal',
            'subject_motion': 'realistic forklift, pallet, truck or container movement with safe separation',
            'ending_shot': 'clean facility hero shot emphasizing capacity, order and reliability',
            'audio': 'subtle industrial ambience with polished corporate sound design',
        },
    },
}
CATEGORY_NAMES = list(CATEGORY_PRESETS.keys())


class PromptBuilderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AI Prompt Builder v6.4')
        self.geometry('1380x900')
        self.minsize(1160, 780)
        self.result = None
        self.storyboard = ''
        self.examples = []
        self.output_dir = DEFAULT_OUT
        self.dynamic_widgets = {}
        self.service_vars = {k: tk.BooleanVar(value=(k == 'OpenAI')) for k in SERVICE_KEYS}
        self._create_vars()
        self._build_ui()
        self._set_defaults()
        self.refresh_dynamic_options()
        self.refresh_db_status()

    def _create_vars(self):
        self.idea = tk.StringVar()
        self.category = tk.StringVar(value='직접 설정')
        self.output_pref = tk.StringVar(value='auto')
        self.use_case = tk.StringVar(value='auto')
        self.style = tk.StringVar()
        self.aspect = tk.StringVar(value='auto')
        self.model_label = tk.StringVar(value='GPT Image 2')
        self.rec_media = tk.StringVar(value='-')
        self.rec_model = tk.StringVar(value='-')
        self.rec_use_case = tk.StringVar(value='-')
        self.rec_aspect = tk.StringVar(value='-')
        self.must_include = tk.StringVar()
        self.avoid = tk.StringVar(value='bad text, distortion, clutter')
        self.on_text = tk.StringVar()
        self.media_badge = tk.StringVar(value='결과물 유형: 자동')
        # image dynamic
        self.img_composition = tk.StringVar(value='centered hero composition')
        self.img_background = tk.StringVar()
        self.img_lighting = tk.StringVar()
        self.img_lens = tk.StringVar(value='85mm commercial product photography')
        self.img_text_layout = tk.StringVar()
        self.img_quality_focus = tk.StringVar(value='premium product finish, clean reflections')
        # video dynamic
        self.vid_duration = tk.StringVar(value='5-8 seconds')
        self.vid_scene_count = tk.StringVar(value='3 scenes')
        self.vid_opening = tk.StringVar()
        self.vid_camera = tk.StringVar(value='slow dolly-in and subtle orbit')
        self.vid_subject = tk.StringVar(value='elegant product motion and light movement')
        self.vid_ending = tk.StringVar()
        self.vid_audio = tk.StringVar(value='no dialogue, premium ambient sound')

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill='both', expand=True)
        ttk.Label(root, text='AI Prompt Builder', font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(root, text='구조: 기본설정 → AI별 동적 옵션 → 자동추천 → 프롬프트 생성').pack(anchor='w', pady=(2,6))
        ttk.Label(root, textvariable=self.media_badge).pack(anchor='w', pady=(0,10))

        main = ttk.Panedwindow(root, orient='horizontal')
        main.pack(fill='both', expand=True)
        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=5)
        main.add(right, weight=5)

        self.nb = ttk.Notebook(left)
        self.nb.pack(fill='both', expand=True)
        self.tab_basic = ttk.Frame(self.nb, padding=10)
        self.tab_dynamic = ttk.Frame(self.nb, padding=10)
        self.tab_recommend = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_basic, text='1. 기본설정')
        self.nb.add(self.tab_dynamic, text='2. AI별 동적 옵션')
        self.nb.add(self.tab_recommend, text='3. 자동추천')
        self._build_basic_tab()
        self._build_dynamic_tab()
        self._build_recommend_tab()

        ex_frame = ttk.LabelFrame(right, text='로컬 참고 예제', padding=10)
        ex_frame.pack(fill='both', expand=False)
        self.example_list = tk.Listbox(ex_frame, height=10)
        self.example_list.pack(fill='both', expand=True)
        self.db_status = ttk.Label(ex_frame, text='')
        self.db_status.pack(anchor='w', pady=(6,0))

        self.result_nb = ttk.Notebook(right)
        self.result_nb.pack(fill='both', expand=True, pady=(10,0))
        prompt_tab = ttk.Frame(self.result_nb, padding=6)
        storyboard_tab = ttk.Frame(self.result_nb, padding=6)
        self.result_nb.add(prompt_tab, text='4. 최종 프롬프트')
        self.result_nb.add(storyboard_tab, text='스토리보드')
        self.output = tk.Text(prompt_tab, wrap='word', font=('Consolas', 10))
        self.output.pack(fill='both', expand=True)
        self.storyboard_output = tk.Text(storyboard_tab, wrap='word', font=('Consolas', 10))
        self.storyboard_output.pack(fill='both', expand=True)

        btns1 = ttk.Frame(root)
        btns1.pack(fill='x', pady=(10,0))
        ttk.Button(btns1, text='자동추천', command=self.auto_recommend).pack(side='left')
        ttk.Button(btns1, text='예제 검색', command=self.search_examples).pack(side='left', padx=6)
        ttk.Button(btns1, text='프롬프트 생성', command=self.generate).pack(side='left')
        ttk.Button(btns1, text='스토리보드 생성', command=self.generate_storyboard_only).pack(side='left', padx=6)
        ttk.Button(btns1, text='OpenAI 이미지용', command=self.generate_openai).pack(side='left', padx=(20, 6))
        ttk.Button(btns1, text='Gemini/Veo 영상용', command=self.generate_veo).pack(side='left', padx=6)
        ttk.Button(btns1, text='Higgsfield 광고용', command=self.generate_higgsfield).pack(side='left', padx=6)

        btns2 = ttk.Frame(root)
        btns2.pack(fill='x', pady=(8,0))
        ttk.Button(btns2, text='클립보드 복사', command=self.copy_prompt).pack(side='left')
        ttk.Button(btns2, text='스토리보드 복사', command=self.copy_storyboard).pack(side='left', padx=6)
        ttk.Button(btns2, text='TXT 저장', command=lambda: self.save_as('txt')).pack(side='left', padx=(20,0))
        ttk.Button(btns2, text='MD 저장', command=lambda: self.save_as('md')).pack(side='left', padx=6)
        ttk.Button(btns2, text='JSON 저장', command=lambda: self.save_as('json')).pack(side='left', padx=6)
        ttk.Button(btns2, text='3종 모두 저장', command=self.save_all).pack(side='left', padx=6)
        ttk.Button(btns2, text='초기화', command=self.clear_all).pack(side='right')

        self.status = ttk.Label(root, text='준비 완료')
        self.status.pack(anchor='w', pady=(8,0))

    def _build_basic_tab(self):
        f = self.tab_basic
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text='만들 것').grid(row=0, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Entry(f, textvariable=self.idea).grid(row=0, column=1, sticky='ew', pady=4)

        ttk.Label(f, text='카테고리 프리셋').grid(row=1, column=0, sticky='w', padx=(0,8), pady=4)
        preset_row = ttk.Frame(f)
        preset_row.grid(row=1, column=1, sticky='ew', pady=4)
        preset_row.columnconfigure(0, weight=1)
        ttk.Combobox(preset_row, textvariable=self.category, values=CATEGORY_NAMES, state='readonly').grid(row=0, column=0, sticky='ew')
        ttk.Button(preset_row, text='프리셋 적용', command=self.apply_category_preset).grid(row=0, column=1, padx=(6,0))

        ttk.Label(f, text='결과물 유형').grid(row=2, column=0, sticky='nw', padx=(0,8), pady=6)
        out_frame = ttk.Frame(f)
        out_frame.grid(row=2, column=1, sticky='w')
        for idx, (val, label) in enumerate(OUTPUT_TYPES):
            ttk.Radiobutton(out_frame, text=label, value=val, variable=self.output_pref, command=self.refresh_dynamic_options).grid(row=0, column=idx, padx=(0,12))

        ttk.Label(f, text='구독 서비스').grid(row=3, column=0, sticky='nw', padx=(0,8), pady=6)
        svc_frame = ttk.Frame(f)
        svc_frame.grid(row=3, column=1, sticky='w')
        for idx, key in enumerate(SERVICE_KEYS):
            ttk.Checkbutton(svc_frame, text=key, variable=self.service_vars[key]).grid(row=0, column=idx, padx=(0,16))

        ttk.Label(f, text='용도').grid(row=4, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Combobox(f, textvariable=self.use_case, values=USE_CASES, state='readonly').grid(row=4, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='스타일/분위기').grid(row=5, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Entry(f, textvariable=self.style).grid(row=5, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='화면비').grid(row=6, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Combobox(f, textvariable=self.aspect, values=ASPECTS, state='readonly').grid(row=6, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='추천/수동 AI 모델').grid(row=7, column=0, sticky='w', padx=(0,8), pady=4)
        cb = ttk.Combobox(f, textvariable=self.model_label, values=list(LABEL_TO_MODEL.keys()), state='readonly')
        cb.grid(row=7, column=1, sticky='ew', pady=4)
        cb.bind('<<ComboboxSelected>>', lambda e: self.refresh_dynamic_options())
        ttk.Label(f, text='반드시 포함').grid(row=8, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Entry(f, textvariable=self.must_include).grid(row=8, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='피하고 싶은 요소').grid(row=9, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Entry(f, textvariable=self.avoid).grid(row=9, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='화면 안 텍스트').grid(row=10, column=0, sticky='w', padx=(0,8), pady=4)
        ttk.Entry(f, textvariable=self.on_text).grid(row=10, column=1, sticky='ew', pady=4)
        ttk.Label(f, text='권장 흐름: 만들 것 입력 → 카테고리 프리셋 적용 → 자동추천 → 추천값 반영 → 동적 옵션 조정 → 프롬프트 생성', foreground='#555555', wraplength=640).grid(row=11, column=0, columnspan=2, sticky='w', pady=(10,0))

    def _build_dynamic_tab(self):
        self.dynamic_container = ttk.Frame(self.tab_dynamic)
        self.dynamic_container.pack(fill='both', expand=True)

    def _build_recommend_tab(self):
        f = self.tab_recommend
        f.columnconfigure(1, weight=1)
        self.reason_text = tk.Text(f, height=8, wrap='word')
        rows = [('추천 결과물 유형', self.rec_media), ('추천 AI 모델', self.rec_model), ('추천 용도', self.rec_use_case), ('추천 화면비', self.rec_aspect)]
        for i, (label, var) in enumerate(rows):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky='w', padx=(0,8), pady=6)
            ttk.Entry(f, textvariable=var, state='readonly').grid(row=i, column=1, sticky='ew', pady=6)
        ttk.Label(f, text='추천 이유').grid(row=4, column=0, sticky='nw', padx=(0,8), pady=6)
        self.reason_text.grid(row=4, column=1, sticky='nsew', pady=6)
        f.rowconfigure(4, weight=1)
        ttk.Button(f, text='추천값을 기본설정에 반영', command=self.apply_recommendation).grid(row=5, column=1, sticky='w', pady=(12,0))

    def _set_defaults(self):
        self.idea.set('')
        self.category.set('직접 설정')
        self.output_pref.set('auto')
        self.use_case.set('auto')
        self.style.set('')
        self.aspect.set('auto')
        self.model_label.set('GPT Image 2')
        self.must_include.set('')
        self.avoid.set('bad text, distortion, clutter')
        self.on_text.set('')
        self.reason_text.delete('1.0', 'end')
        self.reason_text.insert('1.0', '자동 추천 전')
        self.update_media_badge()

    def current_model_key(self):
        return LABEL_TO_MODEL.get(self.model_label.get(), 'gpt_image_2')

    def current_media(self):
        explicit = self.output_pref.get()
        return pb.guess_media(self.current_model_key(), explicit)

    def selected_providers(self):
        return [k.lower() for k, v in self.service_vars.items() if v.get()]

    def refresh_db_status(self):
        self.db_status.config(text=f'DB: {DEFAULT_DB} | 존재={DEFAULT_DB.exists()}')

    def update_media_badge(self):
        pref = self.output_pref.get()
        if pref == 'auto':
            inferred = pb.infer_media_from_text(self.idea.get(), pb.guess_media(self.current_model_key(), None))
            self.media_badge.set(f'결과물 유형: 자동 판단 ({"이미지" if inferred == "image" else "동영상"})')
        else:
            self.media_badge.set(f'결과물 유형: {"이미지" if pref == "image" else "동영상"}')

    def refresh_dynamic_options(self):
        self.update_media_badge()
        for child in self.dynamic_container.winfo_children():
            child.destroy()
        media = self.current_media() if self.output_pref.get() != 'auto' else pb.infer_media_from_text(self.idea.get(), pb.guess_media(self.current_model_key(), None))
        frame = ttk.LabelFrame(self.dynamic_container, text=f'{"이미지" if media == "image" else "동영상"} 동적 옵션', padding=10)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        self.dynamic_widgets = {}
        if media == 'image':
            fields = [('구도', self.img_composition, 'composition'), ('배경', self.img_background, 'background'), ('조명', self.img_lighting, 'lighting'), ('렌즈/카메라', self.img_lens, 'lens'), ('텍스트 배치', self.img_text_layout, 'text_layout'), ('품질 초점', self.img_quality_focus, 'quality_focus')]
            helper = '예: 중앙 히어로 제품컷, 검정 반사 바닥, 골드 림라이트, 85mm 렌즈'
        else:
            fields = [('영상 길이', self.vid_duration, 'duration'), ('장면 수', self.vid_scene_count, 'scene_count'), ('시작 장면', self.vid_opening, 'opening_shot'), ('카메라 움직임', self.vid_camera, 'camera_motion'), ('피사체 움직임', self.vid_subject, 'subject_motion'), ('종료 장면', self.vid_ending, 'ending_shot'), ('오디오/대사', self.vid_audio, 'audio')]
            helper = '예: 5-8초, 3씬, 슬로우 돌리 인, 미세 오빗, 엔딩 히어로 샷'
        for idx, (label, var, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky='w', padx=(0,8), pady=4)
            ttk.Entry(frame, textvariable=var).grid(row=idx, column=1, sticky='ew', pady=4)
            self.dynamic_widgets[key] = var
        ttk.Label(frame, text=helper, foreground='#555555', wraplength=650).grid(row=len(fields), column=0, columnspan=2, sticky='w', pady=(10,0))

    def apply_category_preset(self):
        name = self.category.get()
        preset = CATEGORY_PRESETS.get(name) or {}
        if not preset:
            self.status.config(text='직접 설정 모드입니다.')
            return
        self.use_case.set(preset.get('use_case', 'auto'))
        self.style.set(preset.get('style', ''))
        self.must_include.set(preset.get('must_include', ''))
        self.avoid.set(preset.get('avoid', self.avoid.get()))

        # Fill both image and video defaults so switching media later still keeps the preset.
        img = preset.get('image', {})
        self.img_composition.set(img.get('composition', self.img_composition.get()))
        self.img_background.set(img.get('background', self.img_background.get()))
        self.img_lighting.set(img.get('lighting', self.img_lighting.get()))
        self.img_lens.set(img.get('lens', self.img_lens.get()))
        self.img_text_layout.set(img.get('text_layout', self.img_text_layout.get()))
        self.img_quality_focus.set(img.get('quality_focus', self.img_quality_focus.get()))

        vid = preset.get('video', {})
        self.vid_duration.set(vid.get('duration', self.vid_duration.get()))
        self.vid_scene_count.set(vid.get('scene_count', self.vid_scene_count.get()))
        self.vid_opening.set(vid.get('opening_shot', self.vid_opening.get()))
        self.vid_camera.set(vid.get('camera_motion', self.vid_camera.get()))
        self.vid_subject.set(vid.get('subject_motion', self.vid_subject.get()))
        self.vid_ending.set(vid.get('ending_shot', self.vid_ending.get()))
        self.vid_audio.set(vid.get('audio', self.vid_audio.get()))

        self.refresh_dynamic_options()
        self.status.config(text=f'카테고리 프리셋 적용 완료: {name}')

    def auto_recommend(self):
        if not self.idea.get().strip():
            messagebox.showinfo('안내', '먼저 “만들 것”을 입력해주세요.')
            return
        rec = pb.auto_recommend_setup(self.idea.get(), providers=self.selected_providers(), requested_media=self.output_pref.get(), requested_use_case=self.use_case.get(), requested_aspect_ratio=self.aspect.get())
        label = MODEL_TO_LABEL.get(rec['model'], rec['model'])
        self.rec_media.set('이미지' if rec['media'] == 'image' else '동영상')
        self.rec_model.set(label)
        self.rec_use_case.set(rec['use_case'])
        self.rec_aspect.set(rec['aspect_ratio'])
        reason = rec['reason'] or '입력한 목적과 구독 서비스를 기준으로 자동 추천했습니다.'
        if self.output_pref.get() == 'auto':
            reason += f'\n- 입력 내용상 결과물 유형을 {self.rec_media.get()}로 판단했습니다.'
        self.reason_text.delete('1.0', 'end')
        self.reason_text.insert('1.0', reason)
        self._last_recommendation = rec
        self.status.config(text='자동추천 완료')
        self.nb.select(self.tab_recommend)

    def apply_recommendation(self):
        rec = getattr(self, '_last_recommendation', None)
        if not rec:
            messagebox.showinfo('안내', '먼저 자동추천을 실행해주세요.')
            return
        self.output_pref.set(rec['media'])
        self.use_case.set(rec['use_case'])
        self.aspect.set(rec['aspect_ratio'])
        self.model_label.set(MODEL_TO_LABEL.get(rec['model'], rec['model']))
        self.refresh_dynamic_options()
        self.status.config(text='추천값을 기본설정에 반영했습니다.')
        self.nb.select(self.tab_dynamic)

    def gather_dynamic_options(self):
        return {k: v.get().strip() for k, v in self.dynamic_widgets.items()}

    def search_examples(self, forced_model=None, forced_media=None, forced_use_case=None):
        model_key = forced_model or self.current_model_key()
        media = forced_media or (self.current_media() if self.output_pref.get() != 'auto' else pb.infer_media_from_text(self.idea.get(), pb.guess_media(model_key, None)))
        use_case = forced_use_case or ('' if self.use_case.get() == 'auto' else self.use_case.get())
        query = ' '.join(x for x in [self.idea.get(), self.style.get(), use_case] if x)
        self.examples = pb.search_examples(DEFAULT_DB, query=query, media=media, model=model_key, use_case=use_case, limit=8)
        self.example_list.delete(0, 'end')
        for ex in self.examples:
            title = ex.get('title') or ex.get('repo') or 'Untitled'
            score = ex.get('combined_score') or '-'
            media_t = ex.get('media_type') or '-'
            self.example_list.insert('end', f'[{score}][{media_t}] {title[:100]}')
        if not self.examples:
            self.example_list.insert('end', '예제가 없습니다. 모델 프로필만 사용합니다.')
        self.status.config(text=f'예제 검색 완료: {len(self.examples)}개')

    def _effective_media_use_case_aspect(self, model_key=None):
        mk = model_key or self.current_model_key()
        media = self.output_pref.get()
        if media == 'auto':
            media = pb.infer_media_from_text(self.idea.get(), pb.guess_media(mk, None))
        use_case = self.use_case.get()
        if use_case == 'auto':
            use_case = pb.recommend_use_case(self.idea.get())
        aspect = self.aspect.get()
        if aspect == 'auto':
            aspect = pb.recommend_aspect_ratio(media, use_case)
        return media, use_case, aspect

    def _set_result(self, result):
        self.result = result
        self.storyboard = result.get('storyboard') or pb.build_storyboard(
            self.idea.get().strip(), result['media'], result['use_case'], self.style.get().strip(), result['aspect_ratio'],
            self.must_include.get().strip(), self.on_text.get().strip(), self.gather_dynamic_options(), result['model']
        )
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', self.result['final_prompt'])
        self.storyboard_output.delete('1.0', 'end')
        self.storyboard_output.insert('1.0', self.storyboard)
        self.result_nb.select(0)
        self.status.config(text=f'프롬프트 생성 완료 | model={self.result["model"]} | media={self.result["media"]}')

    def generate(self):
        if not self.idea.get().strip():
            messagebox.showwarning('입력 필요', '“만들 것”을 먼저 입력해주세요.')
            return
        model_key = self.current_model_key()
        media, use_case, aspect = self._effective_media_use_case_aspect(model_key)
        self.search_examples(forced_model=model_key, forced_media=media, forced_use_case=use_case)
        result = pb.build_prompt(self.idea.get().strip(), model_key, media, use_case, self.style.get().strip(), aspect, self.must_include.get().strip(), self.avoid.get().strip(), self.on_text.get().strip(), self.examples, self.gather_dynamic_options())
        result['storyboard'] = pb.build_storyboard(self.idea.get().strip(), media, use_case, self.style.get().strip(), aspect, self.must_include.get().strip(), self.on_text.get().strip(), self.gather_dynamic_options(), model_key)
        self._set_result(result)

    def generate_storyboard_only(self):
        if not self.idea.get().strip():
            messagebox.showwarning('입력 필요', '“만들 것”을 먼저 입력해주세요.')
            return
        model_key = self.current_model_key()
        media, use_case, aspect = self._effective_media_use_case_aspect(model_key)
        self.storyboard = pb.build_storyboard(self.idea.get().strip(), media, use_case, self.style.get().strip(), aspect, self.must_include.get().strip(), self.on_text.get().strip(), self.gather_dynamic_options(), model_key)
        self.storyboard_output.delete('1.0', 'end')
        self.storyboard_output.insert('1.0', self.storyboard)
        self.result_nb.select(1)
        self.status.config(text='스토리보드 생성 완료')

    def _generate_target(self, target):
        if not self.idea.get().strip():
            messagebox.showwarning('입력 필요', '“만들 것”을 먼저 입력해주세요.')
            return
        use_case = self.use_case.get()
        aspect = self.aspect.get()
        result = pb.build_target_variant(target, self.idea.get().strip(), self.style.get().strip(), use_case, aspect, self.must_include.get().strip(), self.avoid.get().strip(), self.on_text.get().strip(), self.gather_dynamic_options(), self.examples)
        # align UI with target
        self.output_pref.set(result['media'])
        self.model_label.set(MODEL_TO_LABEL.get(result['model'], result['model']))
        self.use_case.set(result['use_case'])
        self.aspect.set(result['aspect_ratio'])
        self.refresh_dynamic_options()
        self.search_examples(forced_model=result['model'], forced_media=result['media'], forced_use_case=result['use_case'])
        # rebuild with examples if we found some
        result = pb.build_target_variant(target, self.idea.get().strip(), self.style.get().strip(), result['use_case'], result['aspect_ratio'], self.must_include.get().strip(), self.avoid.get().strip(), self.on_text.get().strip(), self.gather_dynamic_options(), self.examples)
        self._set_result(result)
        self.status.config(text=f'{target} 전용 프롬프트 생성 완료')

    def generate_openai(self):
        self._generate_target('openai')

    def generate_veo(self):
        self._generate_target('veo')

    def generate_higgsfield(self):
        self._generate_target('higgsfield')

    def copy_prompt(self):
        text = self.output.get('1.0', 'end').strip()
        if not text:
            messagebox.showinfo('안내', '복사할 프롬프트가 없습니다.')
            return
        self.clipboard_clear(); self.clipboard_append(text)
        self.status.config(text='프롬프트를 클립보드에 복사했습니다.')

    def copy_storyboard(self):
        text = self.storyboard_output.get('1.0', 'end').strip()
        if not text:
            messagebox.showinfo('안내', '복사할 스토리보드가 없습니다.')
            return
        self.clipboard_clear(); self.clipboard_append(text)
        self.status.config(text='스토리보드를 클립보드에 복사했습니다.')

    def _payload(self):
        return {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'input': {
                'idea': self.idea.get(), 'category': self.category.get(), 'output_pref': self.output_pref.get(), 'providers': [k for k, v in self.service_vars.items() if v.get()],
                'model': self.result['model'] if self.result else self.current_model_key(), 'media': self.result['media'] if self.result else self.current_media(),
                'use_case': self.result['use_case'] if self.result else self.use_case.get(), 'style': self.style.get(),
                'aspect_ratio': self.result['aspect_ratio'] if self.result else self.aspect.get(), 'must_include': self.must_include.get(),
                'avoid': self.avoid.get(), 'on_image_text': self.on_text.get(), 'dynamic_options': self.gather_dynamic_options(),
            },
            'examples': [{'title': ex.get('title'), 'repo': ex.get('repo'), 'model_family': ex.get('model_family'), 'combined_score': ex.get('combined_score'), 'auto_tags': ex.get('auto_tags')} for ex in self.examples],
            'final_prompt': self.result['final_prompt'] if self.result else '',
            'short_prompt': self.result['short_prompt'] if self.result else '',
            'storyboard': self.storyboard,
        }

    def save_as(self, kind):
        if kind in {'txt', 'md', 'json'} and not self.result:
            messagebox.showinfo('안내', '먼저 프롬프트를 생성해주세요.')
            return
        ext = {'txt': '.txt', 'md': '.md', 'json': '.json'}[kind]
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(kind.upper(), f'*{ext}'), ('All files', '*.*')])
        if not path:
            return
        p = Path(path)
        if kind == 'txt':
            p.write_text(self.result['final_prompt'] + '\n', encoding='utf-8')
        elif kind == 'md':
            md = self.result['markdown']
            if self.storyboard:
                md += '\n\n## Storyboard\n\n' + self.storyboard + '\n'
            p.write_text(md, encoding='utf-8')
        else:
            p.write_text(json.dumps(self._payload(), ensure_ascii=False, indent=2), encoding='utf-8')
        self.status.config(text=f'저장 완료: {p}')

    def save_all(self):
        if not self.result:
            messagebox.showinfo('안내', '먼저 프롬프트를 생성해주세요.')
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        base = f'{ts}_{pb.slugify(self.idea.get())}_{self.result["model"]}'
        txt = self.output_dir / f'{base}.txt'
        md = self.output_dir / f'{base}.md'
        js = self.output_dir / f'{base}.json'
        storyboard_path = self.output_dir / f'{base}_storyboard.md'
        txt.write_text(self.result['final_prompt'] + '\n', encoding='utf-8')
        md_body = self.result['markdown'] + ('\n\n## Storyboard\n\n' + self.storyboard + '\n' if self.storyboard else '')
        md.write_text(md_body, encoding='utf-8')
        js.write_text(json.dumps(self._payload(), ensure_ascii=False, indent=2), encoding='utf-8')
        if self.storyboard:
            storyboard_path.write_text(self.storyboard + '\n', encoding='utf-8')
        self.status.config(text=f'저장 완료: {self.output_dir}')
        messagebox.showinfo('저장 완료', f'{self.output_dir}\n\nTXT / MD / JSON / Storyboard 저장 완료')

    def clear_all(self):
        self.result = None
        self.storyboard = ''
        self.examples = []
        self.example_list.delete(0, 'end')
        self.output.delete('1.0', 'end')
        self.storyboard_output.delete('1.0', 'end')
        for k in SERVICE_KEYS:
            self.service_vars[k].set(k == 'OpenAI')
        self._set_defaults(); self.refresh_dynamic_options(); self.status.config(text='초기화 완료')


if __name__ == '__main__':
    app = PromptBuilderGUI()
    app.mainloop()
