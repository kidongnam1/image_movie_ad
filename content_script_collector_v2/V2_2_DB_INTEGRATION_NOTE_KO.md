# Script Generator V2.2 — 실제 DB 연동

## 발견한 문제
기존 V2 Generator는 SQLite DB를 import만 하고 실제 조회하지 않았습니다.
Hook/CTA는 코드 내부 고정 템플릿만 사용했습니다.

## V2.2 수정
- `database/content_script.sqlite` 실제 조회
- `viral_hooks`, `short_form_scripts`, `ctas`, `before_after_patterns`, `product_demo_patterns`, `testimonial_patterns` 참조
- 상업 광고 생성 시 `COMMERCIAL_OK` + `TRANSFORM_ONLY`만 사용
- `RESEARCH_ONLY`, `BLOCKED`, `UNKNOWN`은 직접 생성 근거에서 제외
- HIGH/PROHIBITED claim-risk 항목 제외
- 원문 복제 대신 카테고리/구조/유형 신호를 추출하여 새 문장 생성
- 결과 JSON/MD에 DB counts, source_id, hook_id 등 추적 정보 기록
- `--require-db` 옵션 추가: DB가 비면 생성 실패
- `VERIFY_DB_GENERATOR.bat` 추가: 세럼으로 실제 DB 참조 여부 자동 검증

## 사용자 PC 검증
`VERIFY_DB_GENERATOR.bat` 실행 후 마지막 줄이:
`VERIFY_DB_GENERATOR PASS`
이면 실제 DB 연동 검증 완료입니다.
