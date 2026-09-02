# AI Prompt Collector v6 — 단계별 점검 보고서

## 1. 기준선
- 관리 93 / 활성 73 / corpus 63 / tooling 10 / 모델 36
- Manifest validator: PASS (errors 0, warnings 0)

## 2. Windows 실행 안정성
- preflight: Python, Git, 쓰기권한, 디스크, GitHub 연결 확인
- clone retry/backoff: 구현
- 매 레포 clone 후 `clone_status.json` 즉시 checkpoint 저장
- 재실행 시 기존 Git repo는 pull 후 재사용
- `--no-pull`, `--index-only` 지원

## 3. 다운로드 최적화
- `--text-only-clone`: sparse checkout으로 프롬프트 친화 텍스트 파일 중심 수집
- `GIT_LFS_SKIP_SMUDGE=1`: 대형 LFS 자산 자동 다운로드 방지
- Windows `core.longpaths=true`를 Git 명령에 적용

## 4. 인덱싱
- JSON/JSONL/NDJSON/CSV/TSV/Markdown/TXT/YAML/JS/TS/Python 후보 추출
- 언어 추정, text/image-to-video/edit 입력모드 추정
- 모델별/태그별/이미지·동영상별 CSV 생성
- SQLite FTS 검색 DB 생성

## 5. 중복
- Exact SHA-256 dedupe: 자동 통합
- Near duplicate: MinHash + token Jaccard, **검토만 하고 자동 삭제 안 함**
- Repo overlap: 대규모 레포 중복 후보 보고

## 6. 추적성
- source URL, 라이선스, 검증일, repo commit, attribution을 프롬프트 레코드에 보존
- UNKNOWN 라이선스는 `license_verified=False`로 정리

## 7. 로컬 종합 셀프테스트
- 로컬 Git repo 2개 실제 clone: PASS
- 두 번째 실행 pull/update: PASS
- sparse text-only clone: PASS
- prompt extraction/SQLite/recommendation/model profile: PASS
- postflight count reconciliation: PASS
- near-duplicate 의도 사례 탐지: PASS

## 8. 남은 외부 실행
- 실제 공개 GitHub 73개 활성 레포의 대량 clone은 현재 ChatGPT 서버 네트워크 제약 때문에 미실행.
- Windows `START_HERE.bat`이 해당 단계를 수행하도록 준비 완료.
