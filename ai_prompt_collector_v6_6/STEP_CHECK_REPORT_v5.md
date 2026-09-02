# STEP CHECK REPORT v5

작성일: 2026-08-31 (KST)

| 단계 | 목표 | 점검 결과 |
|---|---|---|
| 1 | GitHub 레포 조사 확대 | PASS — 총 93개 관리 |
| 2 | 원본/후보/중복 상태 분리 | PASS — verified 15, probable 58, candidate 19, duplicate 1 |
| 3 | corpus/tooling 분리 | PASS — 활성 corpus 63, tooling 10 |
| 4 | 이미지/동영상 및 모델 분류 | PASS — 활성 image 39, video 34, 모델 36 패밀리 |
| 5 | 프롬프트 추출/정규화 | PASS — JSON/CSV/JSONL/NDJSON/MD/TXT/YAML 계열 처리 로직 유지 |
| 6 | exact prompt dedupe | PASS — SHA-256 정규화 중복 그룹 생성 |
| 7 | 레포 내용 중복 탐지 | PASS — repo overlap report 로직 및 heavy-overlap selftest 통과 |
| 8 | 품질/모델 적합도 | PASS — prompt quality, model fit, combined score |
| 9 | 자동 태깅 | PASS — 짧은 태그 단어경계 오탐(`luxury`→`ux`) 수정 |
| 10 | 추천 검색 | PASS — FTS JOIN ambiguous-column 오류 수정, 토큰별 fallback 추가 |
| 11 | 실행 필터 | PASS — verified-only / media / model / min-repo-quality 테스트 |
| 12 | MASTER 구조 검증 | PASS — 93행, errors 0, warnings 0 |
| 13 | 라이선스/근거 필드 | PASS — SPDX/확인상태/검증일/근거URL/프롬프트수 필드 추가 |
| 14 | Excel 탐색 인덱스 | PASS — 10개 시트 생성 |

## 핵심 수정 피드백
1. 단순 검색 건수보다 **원본성·실제 프롬프트 존재 여부·중복률**을 우선했습니다.
2. `corpus`와 `tooling`을 분리해 검색 결과 혼선을 줄였습니다.
3. `Qwen Image 3`은 API 설명의 2,000+ 문구 대신 README에서 확인한 **144 original recipes**를 검증값으로 기록했습니다.
4. `LTX Video`는 실제 `prompts/` 디렉터리와 카메라/대사/I2V/제품영상/오디오 파일을 확인했습니다.
5. Higgsfield의 `18 templates`는 프롬프트 개수로 오해하지 않도록 prompt_count에서 제거했습니다.
6. UNKNOWN/NOASSERTION 라이선스는 사용 허가로 해석하지 않도록 별도 표시했습니다.

## 남은 물리 실행
현재 세션에서 할 수 없는 단계는 GitHub 레포 전체 `git clone`입니다. 인터넷 연결 Windows PC에서 수집기를 실행한 뒤 실제 추출 프롬프트 수, cross-repo 중복률, 최종 MASTER 수를 재검증해야 합니다.
