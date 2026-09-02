# Content / Script Collector + Script Generator V2

## 이번 V2 핵심
1. Prompt Repository 73개를 CORE 25 / EXTENDED 23 / ARCHIVE 25로 운영 분리
2. `FULL_AUDIT_CORE25.bat`:
   - 실제 AI Prompt Collector의 `repos_manifest.csv` 사용
   - `repo_overlap_report.csv`가 있으면 실측 중복률까지 반영
   - 없으면 품질/원본성/라이선스/모델 다양성/광고·상품 적합도로 분류
3. `GENERATE_SCRIPT_V2.bat`
   - 상품명 입력
   - Hook 30개 생성·점수화
   - TOP 3 선정
   - 30초 Script
   - CTA
   - Kling / Veo / Seedance 장면별 Prompt 생성
4. 화장품 관련 과장/치료 표현 Risk Gate 유지

## 중요
현재 ChatGPT 환경에는 공개 GitHub 73개를 실제 clone한 `AI_PROMPT_LIBRARY`가 없기 때문에,
동봉된 `CORE_25.csv`는 v6 manifest 메타데이터에 기반한 **사전 CORE25**입니다.

사용자 PC에서 AI Prompt Collector 다운로드/인덱싱을 완료한 뒤
`FULL_AUDIT_CORE25.bat`를 실행하면 `repo_overlap_report.csv`의 실제 중복률을 사용해
`prompt_core/final/CORE_25_FINAL.csv`가 생성됩니다.

즉 삭제하지 않고:
- CORE = 기본 검색
- EXTENDED = fallback
- ARCHIVE = 보존
방식으로 사용합니다.

## 세럼 테스트
`GENERATE_SCRIPT_V2.bat` 실행 후 `세럼` 입력.
샘플 결과는 `outputs/세럼_script_v2.md`와 JSON에 이미 포함되어 있습니다.
