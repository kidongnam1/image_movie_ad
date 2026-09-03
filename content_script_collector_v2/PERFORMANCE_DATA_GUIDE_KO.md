# V2.6 광고 성과 데이터 입력 가이드

## 가장 중요한 원칙

`observed_at`은 **파일을 가져온 날짜가 아니라 성과가 집계된 기간의 식별값**으로 사용합니다.

V2.6은 다음 항목을 같은 성과행의 자연키로 봅니다.

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

V2.6 DB에는 3개 행이 쌓이는 것이 아니라 **같은 행 1개가 1,000 → 2,500 → 5,000으로 UPDATE**됩니다.

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

예:

```text
9/1 누적 1,000
9/2 누적 2,500
9/3 누적 5,000
```

이 세 행을 각각 다른 날짜 성과로 넣으면 실제 5,000 노출을 8,500으로 잘못 합산하게 됩니다.

누적 스냅샷이라면 **동일 자연키로 UPDATE**, 일별 비중복 실적이라면 **날짜별 INSERT**를 사용하세요.

## creative_id 권장

V2.6의 `experiment_plan`에서 생성한 다음 ID를 실제 광고 이름 또는 메모에 같이 기록하는 것을 권장합니다.

```text
CR-XXXXXXXXXXXX
```

그러면 다음 성과 입력에서 동일 Creative를 직접 찾아 ±2점 범위의 성과보정을 적용할 수 있습니다.

## 최소 권장 데이터

학습은 작은 표본을 자동으로 축소하지만, 후보 비교 시에는 각 Creative당 최소 1,000 노출을 기본 권장값으로 사용합니다.

수집 권장 필드:

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

## 안전

성과가 좋더라도 허위 후기, 가짜 희소성, 근거 없는 효능·수치·의료 주장을 재사용 대상으로 승격하지 않습니다. V2.6은 V2.5 안전/품질 Gate를 통과한 후보 안에서만 성과 순위를 조정합니다.
