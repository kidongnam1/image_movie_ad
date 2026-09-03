# V2.7 광고 성과 데이터 입력 가이드

## V2.7 권장 입력 방법

광고 플랫폼에서 내려받은 원본 CSV/XLSX의 열 이름을 직접 V2.6 공통 형식으로 바꿀 필요가 없습니다.

먼저 다음을 사용하세요.

```bat
IMPORT_PLATFORM_PERFORMANCE_V27.bat
```

지원 모드:

- auto
- meta
- tiktok
- naver
- coupang
- generic

V2.7 어댑터는 헤더 별칭을 이용해 원본 성과를 V2.6 공통 스키마로 변환합니다. 플랫폼 export 형식은 변경될 수 있으므로 감지하지 못한 열은 `unmapped_headers`로 보고합니다.

가장 정확한 연결 방법은 광고명/소재명에 V2.7이 생성한 `CR-XXXXXXXXXXXX`를 넣는 것입니다. 그러면 Creative Registry에서 상품·카테고리·Angle·Hook·Selling Point를 자동 복원합니다.

CR ID가 없는 과거 광고는 가져오기 BAT에서 기본 상품명과 카테고리를 지정할 수 있습니다.

V2.6 공통 스키마 CSV/JSON/XLSX를 직접 가져오는 기존 `IMPORT_AD_PERFORMANCE_V26.bat`도 계속 사용할 수 있습니다.

---

## 가장 중요한 원칙

`observed_at`은 **파일을 가져온 날짜가 아니라 성과가 집계된 기간의 식별값**으로 사용합니다.

성과 DB는 다음 항목을 같은 성과행의 자연키로 봅니다.

```text
observed_at + campaign_id + creative_id + product + category + platform + angle + hook_text + selling_point
```

같은 자연키를 다시 가져오면:

- 성과 수치가 동일함 → `duplicates_skipped`
- 성과 수치가 변경됨 → 기존 행을 `updated`
- 자연키가 새로움 → `inserted`

따라서 같은 누적 성과를 여러 번 더해 과대학습하는 것을 방지합니다.

## 방식 A — 광고 플랫폼의 누적 성과 스냅샷을 계속 갱신하는 경우

같은 광고의 누적 수치를 매번 다시 가져온다면 `observed_at`을 비워두거나 동일한 기간명으로 유지하세요.

예:

```text
observed_at: (빈칸)
creative_id: CR-123456789ABC
impressions: 첫날 1,000 → 다음 export 2,500 → 다음 export 5,000
```

DB에는 3개 행이 쌓이는 것이 아니라 **같은 행 1개가 1,000 → 2,500 → 5,000으로 UPDATE**됩니다.

## 방식 B — 날짜별 비중복 실적을 저장하는 경우

플랫폼에서 일별 실적을 따로 내려받아 각 날짜의 숫자가 서로 중복되지 않는다면 날짜를 넣습니다.

```text
2026-09-01 / CR-... / 1,000 impressions
2026-09-02 / CR-... / 1,300 impressions
2026-09-03 / CR-... /   900 impressions
```

이 경우 각 날짜는 서로 다른 성과행으로 저장되고 합산됩니다.

## 피해야 할 방식

누적 성과인데 export 날짜를 매번 다른 `observed_at`으로 넣으면 같은 과거 실적이 중복 합산될 수 있습니다.

```text
9/1 누적 1,000
9/2 누적 2,500
9/3 누적 5,000
```

이 세 행을 각각 다른 날짜 성과로 넣으면 실제 5,000 노출을 8,500으로 잘못 합산하게 됩니다.

누적 스냅샷이라면 **동일 자연키로 UPDATE**, 일별 비중복 실적이라면 **날짜별 INSERT**를 사용하세요.

## Creative ID 운영

V2.7의 `experiment_plan`에서 생성한 ID를 실제 광고 이름 또는 메모에 같이 기록하세요.

```text
CR-XXXXXXXXXXXX
```

예:

```text
Serum_A_CR-12AB34CD56EF
Golf_B_CR-98FE76DC54BA
```

V2.7은 광고명에서 CR ID를 찾아 Creative Registry와 연결합니다. 과거 experiment_plan은 다음으로 소급 등록할 수 있습니다.

```bat
REGISTER_EXPERIMENT_PLAN_V27.bat
```

## 최소 권장 데이터

학습은 작은 표본을 자동 축소하지만 후보 비교 시 각 Creative당 최소 1,000 노출을 기본 권장값으로 사용합니다.

```text
impressions
views_2s
views_3s
clicks
detail_views
purchases
revenue
spend
```

## 대시보드

성과를 가져온 뒤:

```bat
OPEN_PERFORMANCE_DASHBOARD_V27.bat
```

에서 플랫폼/상품/Angle/Hook/Creative별 CTR·CVR·ROAS를 비교합니다.

## 안전

성과가 좋더라도 허위 후기, 가짜 희소성, 근거 없는 효능·수치·의료 주장을 재사용 대상으로 승격하지 않습니다. V2.7은 기존 안전/품질 Gate를 통과한 후보 안에서만 성과 순위를 조정합니다.
