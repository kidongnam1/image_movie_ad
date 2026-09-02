# Script Generator V2.3 — TOP3 다양성 보강

수정 내용:
- TOP3가 동일한 `hook_id`를 반복 참조하지 않도록 우선 분산
- 가능하면 서로 다른 Hook category까지 분산
- 우선순위:
  1. 서로 다른 hook_id + 서로 다른 category
  2. 서로 다른 hook_id
  3. 데이터가 부족한 경우 점수순 fallback
- 결과 JSON에 `top3_diversity.unique_hook_ids`, `unique_categories` 추가
- 검증 BAT에서 최소 2개 이상의 서로 다른 hook_id, category를 자동 확인

목표 예:
- TOP1 Curiosity
- TOP2 Problem
- TOP3 Comparison/Contrarian

기존 DB는 건드리지 않습니다.
