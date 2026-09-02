# repos_manifest v6 주요 필드

- `active`: 기본 수집 대상 여부
- `origin_status`: `verified_original` / `probable_original` / `candidate` / `duplicate_excluded`
- `verified_fork_false`: GitHub API에서 `fork=false`를 직접 확인했는지 여부
- `media_type`: image / video
- `model_family`: 주 대상 AI/모델 계열
- `source_kind`: corpus / tooling / watchlist
- `repo_quality_score`: 저장소 자체 품질 점수 0~100
- `specialization`, `use_case`: 분야/용도 검색용 태그
- `license_spdx`, `license_verified`: 저장소 라이선스 확인 정보
- `prompt_count_claimed`: 저장소가 주장하는 프롬프트 수
- `prompt_count_verified`: README/구조를 직접 확인한 수량
- `content_structure_verified`: 실제 프롬프트 파일 구조 확인 여부
- `evidence_url`: 원본성/구조 검증 근거 URL
