# SNS Creative TOP50 단계별 점검

1. 범위 정의 — PASS
   - AI Thumbnail / Social Card & OG / Banner & Poster / Design & Composition / Image & Video utilities
2. 후보 풀 — PASS
   - 58 unique repositories
3. Stars 우선 평가 — PASS
   - Stars 40% weight + 별도 `stars_rank`
4. SNS 실무 적합도 — PASS
   - `recommended_rank` 별도 생성
5. 원본/상태 Gate — PASS
   - fork=false, archived=false만 TOP50 eligibility
6. 라이선스 필드 — PASS
   - SPDX 또는 UNKNOWN/NOASSERTION 표시
7. 최신 GitHub metadata refresh — PASS (Windows execution script)
8. CSV / SQLite / HTML — PASS
9. Stars TOP50 50개 전체 다운로드 — PASS (synthetic 50/50)
10. 기존 Prompt DB와 Unified Search — PASS (code-path validation)
11. 기존 prompt manifest 회귀검증 — PASS
12. 배포 ZIP 무결성 — final packaging에서 검증
