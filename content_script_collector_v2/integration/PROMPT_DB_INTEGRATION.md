# Prompt DB Integration V2

## 권장 배치
`content_script_collector_v2`를 AI Prompt Collector 폴더와 같은 상위 폴더에 둡니다.

Script Generator는 우선 자체 모델별 Prompt 구조를 생성합니다.
기존 Prompt DB가 있으면 다음 검색어로 보강합니다.

- product + product_photography
- product + ugc
- product + creator_ads
- product + camera_motion
- product + cinematic
- model=kling / veo / seedance

향후 직접 API 연결 시 `AI_PROMPT_LIBRARY/indexes/prompt_library.sqlite`에서
CORE 레포 출처를 우선 랭킹하고 EXTENDED를 fallback으로 사용하세요.

## 검색 우선순위
1. CORE
2. CORE + EXTENDED
3. ARCHIVE는 명시적 fallback에서만
