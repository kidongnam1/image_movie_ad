# Content / Script Collector + Script Generator V2.6

## 현재 활성 엔진

기존 실행 경로 `generator/script_generator_v2.py`는 그대로 유지되며 내부적으로 **V2.6 성과학습 엔진**을 사용합니다.

V2.6 흐름:

1. 상품 카테고리 자동 판별
2. 사용자가 지정한 `반드시 강조할 Selling Point` 우선 반영
3. 광고 강도 1~5 + V2.5 Strong Hook Gate
4. Hook 30개 + Creative Competition
5. 과거 실광고 성과가 있으면 Angle별 점수 자동 보정
6. A/B/C 후보 3개와 `creative_id` 생성
7. 15초 / 30초 / 45초 대본 + 영상 Prompt 생성
8. 실제 광고 성과를 CSV/JSON/XLSX로 다시 입력
9. 다음 생성부터 2초·3초 유지율 / CTR / 구매전환 / ROAS를 학습

## 성과학습에서 사용하는 지표

| 지표 | 비중 |
|---|---:|
| 2초 유지율 | 25% |
| 3초 유지율 | 15% |
| CTR | 25% |
| 구매전환율 | 25% |
| ROAS | 10% |

성과 보정은 Angle별 **최대 ±6점**으로 제한합니다. 표본이 작으면 Bayesian shrinkage와 신뢰도 보정으로 영향이 거의 0에 가깝게 줄어듭니다.

## 성과 DB

기존 Content DB와 분리합니다.

- Content 지식 DB: `database/content_script.sqlite`
- 광고 성과 DB: `database/ad_performance.sqlite`

성과 DB는 자동 생성되며 같은 행을 두 번 가져오면 fingerprint로 중복 저장하지 않습니다.

## 1. 성과 입력 템플릿 만들기

가장 쉬운 방법:

```bat
CREATE_AD_PERFORMANCE_TEMPLATE_V26.bat
```

또는 저장소의 다음 샘플을 복사해 사용합니다.

```text
samples/ad_performance_template.csv
```

필드:

```text
observed_at,campaign_id,creative_id,product,category,platform,angle,hook_text,selling_point,impressions,video_starts,views_2s,views_3s,clicks,detail_views,purchases,revenue,spend
```

지원 파일:

- CSV
- JSON
- XLSX / XLSM (`openpyxl` 사용)

## 2. 광고 성과 가져오기

```bat
IMPORT_AD_PERFORMANCE_V26.bat
```

또는:

```bat
python generator\ad_performance_learning.py import "내광고성과.xlsx" --db database\ad_performance.sqlite
```

학습 현황 확인:

```bat
python generator\ad_performance_learning.py report --category golf
```

## 3. 대본 생성

기존 실행 파일 그대로 사용합니다.

```bat
GENERATE_SCRIPT_V2.bat
```

입력 항목:

- 상품명
- 반드시 강조할 특징
- 추가 특징
- Pain Point
- 타깃 고객
- 광고 강도 1~5
- 성과 파일 경로(선택)

예:

```bat
python generator\script_generator_v2.py "골프 거리측정기" ^
  --must-emphasize "0.2초 측정|손떨림 보정" ^
  --features "800m 측정|150g 초경량" ^
  --pain-point "거리 판단이 늦어 샷 템포가 끊기는 문제" ^
  --target "40~60대 골퍼" ^
  --intensity 5 ^
  --performance-file "광고성과.xlsx" ^
  --require-db
```

성과 데이터가 아직 없으면 **Cold Start**로 V2.5 품질점수를 그대로 사용하고 A/B/C 트래픽은 34/33/33으로 제안합니다.

충분한 성과 데이터가 있으면 성과가 높은 Angle을 제한적으로 올리고 낮은 Angle을 내리며 A/B/C 기본 배분은 40/30/30으로 제안합니다.

## 4. V2.6 주요 산출물

기존 산출물에 다음 필드가 추가됩니다.

- `performance_learning`
  - 누적 성과 행
  - 누적 노출
  - 기준 지표
  - Angle별 성과 보정
- `experiment_plan`
  - A/B/C 후보
  - 고유 `creative_id`
  - Hook
  - Selling Point
  - base score / performance adjustment / learned score
  - 권장 트래픽 배분
  - 후보별 최소 노출

예:

```text
A / CR-XXXXXXXXXXXX / 문제공격형 / 40%
B / CR-XXXXXXXXXXXX / 호기심형   / 30%
C / CR-XXXXXXXXXXXX / 손실회피형 / 30%
```

## 5. Creative Package

기존 BAT를 그대로 사용합니다.

```bat
GENERATE_CREATIVE_PACKAGE_V1.bat
```

내부적으로 V2.6 래퍼를 사용하며 기존 UGC / Product Demo / Cinematic 산출물에 추가로 다음 파일을 만듭니다.

- `performance_learning.json`
- `experiment_plan.json`

또한 `project.json`, `strategy.md`, `manifest.json`에도 V2.6 학습 정보를 기록합니다.

## 6. 반복 운영 루프

```text
상품 입력
  ↓
V2.6 대본 생성
  ↓
A/B/C creative_id 생성
  ↓
실제 광고 집행 (외부 플랫폼에서 사람이 승인/집행)
  ↓
노출 / 2초 / 3초 / 클릭 / 구매 / 매출 / 광고비 수집
  ↓
IMPORT_AD_PERFORMANCE_V26.bat
  ↓
ad_performance.sqlite 누적
  ↓
다음 생성 시 Angle 점수 자동 보정
```

프로그램은 **실제 광고 게시나 예산 지출을 자동 실행하지 않습니다.** 비용 발생 단계는 외부 플랫폼에서 별도 승인 후 실행해야 합니다.

## 7. 품질·안전 원칙

V2.5의 다음 원칙을 그대로 유지합니다.

- 카테고리 중립
- 강도 4~5 Strong Hook Gate
- Generic Hook 감점
- First 2s Power
- Specificity
- 필수 Selling Point Coverage
- 허위 후기 차단
- 가짜 희소성 차단
- 근거 없는 1위·최고·100% 차단
- 치료·완치 등 의료적 과장 차단

성과가 좋았다는 이유만으로 위험 표현을 다시 허용하지 않습니다. **성과학습은 안전/품질 Gate를 통과한 후보의 순위만 제한적으로 조정합니다.**

## 8. 전체 검증

```bat
VERIFY_DB_GENERATOR.bat
```

검증 내용:

1. Python 구문검사
2. V2.5 5상품 회귀테스트
3. V2.6 성과 DB 중복/유효성/표본축소 테스트
4. V2.6 성과 기반 재랭킹 + Cold Start 테스트
5. 실제 Content DB 연동
6. Hook 30개 / 강조점 Coverage / A/B/C 3개 확인

## 광고 집행 전 주의

사용자가 입력한 수치·성능·효능은 실제 집행 전에 상품 상세페이지, 제조사 공식 자료, 시험성적서 등으로 확인해야 합니다.

외부 이미지/영상/TTS 및 광고 플랫폼 API는 비용·키·계정 권한이 필요한 단계이므로 자동 집행하지 않습니다.
