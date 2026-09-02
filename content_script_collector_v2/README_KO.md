# Content / Script Collector V1

목적: SNS Shorts / Reels / TikTok 광고용 Content/Script 지식베이스를 6개 영역으로 수집·정규화합니다.

## 6개 DB
1. Viral Hook
2. Short-form Script
3. CTA
4. Before/After
5. Product Demo
6. Testimonial

## 실행
1. Python 3 설치
2. `START_HERE.bat` 더블클릭
3. GitHub API rate limit을 줄이려면 환경변수 `GITHUB_TOKEN` 설정 권장
4. 결과:
   - `database/content_script.sqlite`
   - `indexes/*.csv`
   - `reports/collection_report.html`

## 라이선스 정책
- `COMMERCIAL_OK`: permissive license/명시 승인 범위
- `TRANSFORM_ONLY`: 원문 직접 재사용 금지 또는 share-alike 등 추가 검토 필요
- `RESEARCH_ONLY`: 상업 DB 원문 수록 금지. 패턴/통계/벤치마크만 참고
- `UNKNOWN`: 자동 수집은 가능하더라도 상업 활용 대상에서 제외

## 안전 규칙
- Source URL, commit SHA, SHA-256, license를 sources 테이블에 보존
- RESEARCH_ONLY 원문은 상업 생성 결과로 직접 내보내지 않음
- 화장품/광고 문구는 claim_risk(LOW/MEDIUM/HIGH/PROHIBITED) 평가
- Exact duplicate 자동 제거, near-duplicate는 별도 개선 가능

## 현재 V1 범위
V1은 '수집 + 1차 분류 + DB/CSV 생성'까지 실행 가능합니다.
문장 수준의 정교한 semantic extraction/LLM 재작성은 다음 버전에서 추가하는 것이 좋습니다.
