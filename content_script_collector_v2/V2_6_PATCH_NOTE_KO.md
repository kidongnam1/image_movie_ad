# Script Generator V2.6 패치 노트

## 목표

V2.5의 강한 Hook/카테고리 중립 구조 위에 **실제 광고 성과를 학습하는 폐쇄루프(Closed-loop) 개선**을 추가했습니다.

## 핵심 흐름

```text
대본 생성 → A/B/C creative_id → 실제 집행 → 성과 수집 → 성과 DB 누적 → 다음 대본 점수 보정
```

## 추가된 파일

- `generator/ad_performance_learning.py`
- `generator/script_generator_v26.py`
- `generator/creative_package_v26.py`
- `IMPORT_AD_PERFORMANCE_V26.bat`
- `CREATE_AD_PERFORMANCE_TEMPLATE_V26.bat`
- `samples/ad_performance_template.csv`
- `tests/test_ad_performance_learning.py`
- `tests/test_script_generator_v26.py`
- `tests/test_creative_package_v26.py`

## 변경된 파일

- `generator/script_generator_v2.py` → V2.6 호환 진입점
- `GENERATE_SCRIPT_V2.bat` → 성과 파일 선택 입력 추가
- `GENERATE_CREATIVE_PACKAGE_V1.bat` → V2.6 패키지 래퍼 사용
- `VERIFY_DB_GENERATOR.bat` → V2.6 검증 확장
- `requirements.txt` → `openpyxl` 추가
- `README_V2_KO.md` → V2.6 운영 루프 반영

## 성과 DB

`database/ad_performance.sqlite`

기존 `database/content_script.sqlite`와 분리합니다.

성과 행은 SHA-256 fingerprint로 중복 삽입을 방지합니다.

## 지원 성과 파일

- CSV
- JSON
- XLSX
- XLSM

## 주요 입력 필드

```text
observed_at
campaign_id
creative_id
product
category
platform
angle
hook_text
selling_point
impressions
video_starts
views_2s
views_3s
clicks
detail_views
purchases
revenue
spend
```

## 학습 가중치

| 항목 | 비중 |
|---|---:|
| 2초 유지율 | 25% |
| 3초 유지율 | 15% |
| CTR | 25% |
| 구매전환율(click→purchase) | 25% |
| ROAS | 10% |

## 과적합 방지

- 작은 표본은 Bayesian shrinkage 적용
- 노출 200 미만은 confidence 추가 축소
- 노출이 누적될수록 학습 영향 증가
- Angle 성과 보정은 최대 `-6 ~ +6`점
- 안전/품질 Gate를 우회하지 않고 Gate 통과 후보의 순위만 조정

## 카테고리 학습

가능하면 `category + angle` 성과를 우선 사용합니다.

카테고리 표본이 적으면 전체 Angle 성과를 제한적으로 섞습니다.

예:

```text
golf/problem_attack 성과 충분 → 골프 문제공격형 성과 우선
데이터 부족 → 전체 problem_attack 성과를 약하게 fallback
```

## Cold Start

성과 데이터가 없으면:

- V2.5 기본 품질점수 유지
- 성과 보정 0점
- A/B/C 권장 배분 34/33/33

성과 누적 노출이 충분하면:

- 학습 점수 반영
- 기본 A/B/C 배분 40/30/30

## A/B/C 후보

각 후보에 고유 ID를 부여합니다.

```text
CR-XXXXXXXXXXXX
```

ID는 `상품 + 카테고리 + Angle + Hook`을 기반으로 결정적으로 생성합니다.

이 ID를 실제 광고 이름/메모에 남긴 뒤 성과 파일의 `creative_id`에 다시 넣으면 추적이 쉽습니다.

## Creative Package

기존 `GENERATE_CREATIVE_PACKAGE_V1.bat`를 그대로 사용합니다.

V2.6에서 추가되는 파일:

- `performance_learning.json`
- `experiment_plan.json`

`project.json`, `strategy.md`, `manifest.json`에도 성과학습 상태를 기록합니다.

## 안전 범위

이 패치는 실제 Meta/TikTok/Naver 광고를 자동 게시하거나 예산을 지출하지 않습니다.

그 단계는 비용 발생 및 외부 서비스 변경이므로 별도 승인 후 수행해야 합니다.

## 검증

```bat
VERIFY_DB_GENERATOR.bat
```

합성 데이터에서 다음 방향성을 확인하도록 테스트가 포함됩니다.

- 좋은 `problem_attack` 성과 → 양(+) 보정
- 낮은 `comparison` 성과 → 음(-) 보정
- 작은 표본 → 거의 0점으로 축소
- 중복 import → SKIP
- 잘못된 funnel 수치 → 오류 행으로 거부
- Cold Start → 성과 보정 0점
- A/B/C 후보 항상 3개
