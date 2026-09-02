# SELFTEST RESULT v5

작성일: 2026-08-31 (KST)

## 종합 결과: PASS

- synthetic base set: corpus 2 + tooling 1
- base extraction: raw 5 / unique 5
- verified-only + video + LTX: 1 repo / 2 unique prompts
- verified-only + image: 1 repo / 2 unique prompts
- recommendation: Qwen synthetic product prompt 정상 추천 (`RECOMMEND=96.8`)
- optimize_prompt: Higgsfield/LTX 모델 구조 출력 정상
- FTS 오류 수정: JOIN 컬럼 alias 명시 + token-wise LIKE fallback
- auto-tag 오류 수정: 짧은 태그(`ui`, `ux`, `3d`)를 word-boundary로 판정
- manifest validator: 93 rows / errors 0 / warnings 0
- refresh_manifest_views + repo_catalog.sqlite 재생성 정상

## 검증 범위의 한계
실제 활성 GitHub 레포 전체 clone은 현재 실행환경의 `git clone github.com` 네트워크 제한 때문에 수행하지 못했습니다. 이 selftest는 수집/추출/중복/검색/추천/필터 코드 경로를 synthetic data로 검증한 것입니다.
