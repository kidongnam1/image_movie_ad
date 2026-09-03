# Content / Script Collector + Script Generator V2.4

## V2.4 핵심 변경

기존 V2.2는 Hook, 대본, 영상 Prompt가 `피부·제형·바르기·Korean beauty` 문맥에 고정되어 있어 비화장품 상품도 화장품 광고처럼 생성되는 구조적 문제가 있었습니다.

V2.4에서는 아래 구조로 교체했습니다.

1. 상품 카테고리 자동 판별
2. 사용자가 지정한 `반드시 강조할 Selling Point` 최우선 반영
3. 추가 상품 특징 자동 결합
4. 고객 Pain Point 연결
5. 광고 강도 1~5
6. Hook 30개 생성
7. 80점 미만 Hook 폐기
8. 5개 Copywriter/Angle Creative Competition
9. 우승 Angle 기준 15초 / 30초 / 45초 대본 생성
10. Kling / Veo / Seedance 카테고리별 영상 Prompt 생성
11. UGC / Product Demo / Cinematic Creative Package도 동일한 카테고리 문맥 유지

## 지원 카테고리

- 뷰티/스킨케어
- 골프
- 자동차용품
- 반려동물
- 여행
- 주방용품
- 패션
- 식품/음료
- 생활가전
- 전자기기
- 스포츠/운동
- 사무/오피스
- 생활용품
- 일반 상품 fallback

## 가장 쉬운 실행

기존 방식은 그대로 유지됩니다.

```bat
GENERATE_SCRIPT_V2.bat
```

상품명만 입력해도 카테고리를 자동 판별하고 기본 광고 강도 4로 생성합니다.

## 고급 실행

예: 골프 거리측정기

```bat
python generator\script_generator_v2.py "골프 거리측정기" ^
  --must-emphasize "0.2초 측정, 손떨림 보정" ^
  --features "800m 측정|150g 초경량" ^
  --pain-point "거리 판단이 늦어 샷 템포가 끊기는 문제" ^
  --target "40~60대 골퍼" ^
  --intensity 4 ^
  --require-db
```

예: 무선 청소기

```bat
python generator\script_generator_v2.py "무선 청소기" ^
  --must-emphasize "18,000Pa 흡입력" ^
  --features "480g 초경량|USB-C 충전" ^
  --intensity 5
```

`18,000Pa`처럼 숫자 내부의 쉼표는 하나의 특징으로 보존됩니다. 여러 특징은 `|`, `;`, 줄바꿈 또는 숫자 사이가 아닌 일반 쉼표로 구분할 수 있습니다.

## 광고 강도

| 단계 | 용도 |
|---:|---|
| 1 | 정보 중심 |
| 2 | 관심 유도 |
| 3 | 강한 후킹 |
| 4 | 퍼포먼스 광고 기본값 |
| 5 | 극강 후킹 테스트 |

강도를 높여도 허위 후기, 가짜 희소성, 근거 없는 1위·최고·100%, 치료·완치 표현은 허용하지 않습니다.

## Creative Competition 점수

대본 후보는 다음 가중치로 평가합니다.

| 항목 | 비중 |
|---|---:|
| Hook Strength | 30% |
| Scroll Stop Power | 20% |
| Curiosity Gap | 15% |
| Purchase Desire | 15% |
| Clarity | 10% |
| Credibility | 10% |

기본 품질 Gate는 80점입니다.

## 산출물

상품 1개 기준:

- Hook 30개
- TOP 3 Hook
- Creative Competition 5개 후보
- 우승 광고 Angle
- 15초 대본
- 30초 대본
- 45초 대본
- CTA
- Kling / Veo / Seedance 장면별 Prompt

JSON과 Markdown 결과는 `outputs` 폴더에 저장됩니다.

## Creative Package

```bat
GENERATE_CREATIVE_PACKAGE_V1.bat
```

고급 실행 예:

```bat
python generator\creative_package_v1.py "골프 거리측정기" ^
  --must-emphasize "0.2초 측정" ^
  --pain-point "거리 판단이 늦어 샷 템포가 끊기는 문제" ^
  --target "40~60대 골퍼" ^
  --duration 30 ^
  --intensity 4 ^
  --require-db
```

각 상품에 대해 아래 3종을 생성합니다.

- UGC 후기형
- Product Demo 제품 시연형
- Cinematic 브랜드형

각 광고별 산출물:

- `script.md`
- `storyboard.md`
- `shot_list.json`
- `image_prompts.json`
- `video_prompts.json`
- `voiceover.txt`
- `subtitles.srt`

프로젝트 공통 산출물:

- `project.json`
- `strategy.md`
- `creative_scores.json`
- `compliance_report.json`
- `manifest.json`

## 회귀 테스트

```bat
python tests\selftest_v2.py
python -m unittest tests.test_creative_package_v1
```

V2.4 self-test는 다음을 확인합니다.

- Hook 30개 유지
- 모든 출력 Hook 80점 이상
- 세럼은 뷰티 카테고리 유지
- 골프 거리측정기는 골프 카테고리 유지
- 무선 청소기는 생활가전 카테고리 유지
- 비화장품 대본에 `피부` 강제 삽입 없음
- 비화장품 Prompt에 `Korean beauty` 강제 삽입 없음
- `18,000Pa` Selling Point 보존

## 광고 집행 전 주의

사용자가 직접 입력한 수치·성능·효능은 생성기에서 사실로 단정해 검증하지 않습니다. 실제 광고 집행 전에 상품 상세페이지, 제조사 공식자료, 시험성적서 등으로 확인해야 합니다.

외부 이미지/영상/TTS API는 비용과 API Key가 필요한 단계이므로 기존과 동일하게 자동 호출하지 않고 요청 파일과 자산 규격까지만 생성합니다.
