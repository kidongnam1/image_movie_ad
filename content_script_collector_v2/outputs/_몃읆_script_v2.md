# Script Generator V2.2 — ?몃읆

## DB 연동 검증
- DB 연결: **YES**
- Database: `H:\program-kdn\image_movie_ad\content_script_collector_v2\database\content_script.sqlite`
- DB counts: `{"sources": 377, "viral_hooks": 1355, "short_form_scripts": 1384, "ctas": 930, "before_after_patterns": 601, "product_demo_patterns": 297, "testimonial_patterns": 431}`
- 정책: COMMERCIAL_OK + TRANSFORM_ONLY only; RESEARCH_ONLY/BLOCKED/UNKNOWN excluded from direct generation
- TOP3 Hook reference IDs: `[{'hook_id': 28, 'source_id': 22}, {'hook_id': 28, 'source_id': 22}, {'hook_id': 28, 'source_id': 22}]`

## TOP 3 Hooks
1. **왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?** — 96.2점 (question) · DB hook=28 source=22
2. **혹시 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?** — 96.2점 (question) · DB hook=28 source=22
3. **먼저 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?** — 96.2점 (question) · DB hook=28 source=22

## 30초 대본

### 0-3s · HOOK
- 대사: 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?
- 자막: 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?
- 화면: ?몃읆 제품을 빠르게 클로즈업. 손에 들고 카메라 쪽으로 보여준다.

### 3-8s · PROBLEM
- 대사: ?몃읆는 제품 자체만큼 내 피부 상태와 바르는 순서, 사용량을 같이 보는 게 중요합니다.
- 자막: 제품 + 피부상태 + 사용순서
- 화면: 세안 후 피부와 제품을 번갈아 보여주는 짧은 컷.

### 8-17s · DEMO
- 대사: 제형 확인 → 소량 도포 → 사용감 체크. ?몃읆는 손등에서 먼저 제형을 확인하고 얼굴에는 소량씩 나눠 발라보세요.
- 자막: 제형 확인 → 소량 도포 → 사용감 체크
- 화면: 드로퍼/펌프에서 ?몃읆 한 방울. 매크로 제형 촬영 후 볼에 소량 도포.

### 17-25s · PROOF_SAFE
- 대사: 바른 직후에는 끈적임, 밀림, 당김 같은 사용감을 확인하고 내 루틴과 맞는지 비교해보세요.
- 자막: 끈적임 · 밀림 · 당김 체크
- 화면: 피부 표면을 가볍게 터치하고 사용 전후의 느낌을 과장 없이 비교.

### 25-30s · CTA
- 대사: 더 자세한 사용법은 제품 페이지에서 확인해보세요.
- 자막: 제품 정보·사용법 확인
- 화면: ?몃읆 패키지와 제품 페이지를 연상시키는 깔끔한 엔드카드.

## CTA
더 자세한 사용법은 제품 페이지에서 확인해보세요.

## KLING 장면별 Prompt

### Shot 1
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 0-3s. Purpose: HOOK.
Visual action: ?몃읆 제품을 빠르게 클로즈업. 손에 들고 카메라 쪽으로 보여준다.
On-screen text concept: 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion.
```

### Shot 2
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 3-8s. Purpose: PROBLEM.
Visual action: 세안 후 피부와 제품을 번갈아 보여주는 짧은 컷.
On-screen text concept: 제품 + 피부상태 + 사용순서
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion.
```

### Shot 3
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 8-17s. Purpose: DEMO.
Visual action: 드로퍼/펌프에서 ?몃읆 한 방울. 매크로 제형 촬영 후 볼에 소량 도포.
On-screen text concept: 제형 확인 → 소량 도포 → 사용감 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion.
```

### Shot 4
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 17-25s. Purpose: PROOF_SAFE.
Visual action: 피부 표면을 가볍게 터치하고 사용 전후의 느낌을 과장 없이 비교.
On-screen text concept: 끈적임 · 밀림 · 당김 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion.
```

### Shot 5
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 25-30s. Purpose: CTA.
Visual action: ?몃읆 패키지와 제품 페이지를 연상시키는 깔끔한 엔드카드.
On-screen text concept: 제품 정보·사용법 확인
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera: controlled handheld-to-macro push-in, subtle parallax, realistic hand motion, consistent product label, smooth 24fps motion.
```

## VEO 장면별 Prompt

### Shot 1
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 0-3s. Purpose: HOOK.
Visual action: ?몃읆 제품을 빠르게 클로즈업. 손에 들고 카메라 쪽으로 보여준다.
On-screen text concept: 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts.
```

### Shot 2
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 3-8s. Purpose: PROBLEM.
Visual action: 세안 후 피부와 제품을 번갈아 보여주는 짧은 컷.
On-screen text concept: 제품 + 피부상태 + 사용순서
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts.
```

### Shot 3
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 8-17s. Purpose: DEMO.
Visual action: 드로퍼/펌프에서 ?몃읆 한 방울. 매크로 제형 촬영 후 볼에 소량 도포.
On-screen text concept: 제형 확인 → 소량 도포 → 사용감 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts.
```

### Shot 4
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 17-25s. Purpose: PROOF_SAFE.
Visual action: 피부 표면을 가볍게 터치하고 사용 전후의 느낌을 과장 없이 비교.
On-screen text concept: 끈적임 · 밀림 · 당김 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts.
```

### Shot 5
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 25-30s. Purpose: CTA.
Visual action: ?몃읆 패키지와 제품 페이지를 연상시키는 깔끔한 엔드카드.
On-screen text concept: 제품 정보·사용법 확인
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Camera/audio: cinematic macro lens, gentle dolly-in, natural Korean spoken-ad ambience, clean room tone, realistic liquid physics, continuity across cuts.
```

## SEEDANCE 장면별 Prompt

### Shot 1
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 0-3s. Purpose: HOOK.
Visual action: ?몃읆 제품을 빠르게 클로즈업. 손에 들고 카메라 쪽으로 보여준다.
On-screen text concept: 왜 어떤 날은 ?몃읆를 발라도 사용감이 다르게 느껴질까요?
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Motion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing.
```

### Shot 2
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 3-8s. Purpose: PROBLEM.
Visual action: 세안 후 피부와 제품을 번갈아 보여주는 짧은 컷.
On-screen text concept: 제품 + 피부상태 + 사용순서
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Motion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing.
```

### Shot 3
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 8-17s. Purpose: DEMO.
Visual action: 드로퍼/펌프에서 ?몃읆 한 방울. 매크로 제형 촬영 후 볼에 소량 도포.
On-screen text concept: 제형 확인 → 소량 도포 → 사용감 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Motion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing.
```

### Shot 4
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 17-25s. Purpose: PROOF_SAFE.
Visual action: 피부 표면을 가볍게 터치하고 사용 전후의 느낌을 과장 없이 비교.
On-screen text concept: 끈적임 · 밀림 · 당김 체크
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Motion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing.
```

### Shot 5
```text
Vertical 9:16 premium Korean beauty short-form ad for a skincare ?몃읆.
Scene timing: 25-30s. Purpose: CTA.
Visual action: ?몃읆 패키지와 제품 페이지를 연상시키는 깔끔한 엔드카드.
On-screen text concept: 제품 정보·사용법 확인
Natural realistic skin texture, premium clean bathroom/vanity environment, soft daylight, macro product cinematography,
authentic UGC-commercial hybrid, no medical claims, no exaggerated transformation, readable product-focused composition.
Motion design: concise 3-8 second shot, precise product-hand interaction, dynamic but stable camera motion, strong first-frame composition, social-ad pacing.
```
