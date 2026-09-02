# AI Prompt Collector v6

이미지·동영상 생성 프롬프트 GitHub 저장소를 원본성/모델/용도별로 관리하고, Windows PC에서 한 번에 다운로드·추출·중복제거·검색 인덱싱하는 패키지입니다.

## 현재 기준선

- 전체 관리 레포: **93개**
- 활성 레포: **73개**
- 실제 프롬프트 corpus: **63개**
- 프롬프트 생성/강화 tooling: **10개**
- verified_original: **15개**
- probable_original: **58개**
- 검증 대기: **19개**
- 모델 패밀리: **36개**

## 가장 쉬운 실행

1. ZIP을 Windows 폴더에 압축 해제합니다.
2. **`START_HERE.bat` 더블클릭**
3. Git/Python이 없으면 setup 안내가 실행됩니다.
4. 사전점검이 통과하면 활성 corpus + tooling을 텍스트 전용 sparse clone으로 수집합니다.
5. 완료 후 `AI_PROMPT_LIBRARY/dashboard.html`이 자동으로 열립니다.

## 왜 text-only clone인가

프롬프트 레포에는 큰 PNG/WebP/동영상 미리보기가 포함된 경우가 많습니다. v6 기본 자동실행은 `JSON/CSV/MD/TXT/YAML/코드/라이선스` 중심으로 sparse checkout하여 불필요한 미디어 다운로드를 줄입니다. `GIT_LFS_SKIP_SMUDGE=1`도 자동 적용합니다.

## 실행 파일

- `START_HERE.bat` / `run_full_auto.bat`: 활성 **73개(corpus+tooling)** 전체 자동 처리
- `run_corpus_auto.bat`: corpus **63개**만 처리
- `run_verified_auto.bat`: `verified_original`만 처리
- `run_priority1_auto.bat`: 우선순위 1만 빠르게 처리
- `run_image_auto.bat`: 이미지 corpus만 처리
- `run_video_auto.bat`: 동영상 corpus만 처리
- `run_update_auto.bat`: 이미 받은 레포 pull + 재인덱싱
- `run_reindex_only.bat`: 다운로드 없이 현재 파일만 재인덱싱
- `CHECK_STATUS.bat`: 현재 진행/결과 수량 확인
- `open_dashboard.bat`: 결과 대시보드 열기

## 자동 생성 결과

`AI_PROMPT_LIBRARY/indexes/` 아래에 다음이 생성됩니다.

- `prompt_records.csv`, `prompt_records.jsonl`: 고유 프롬프트 MASTER
- `prompt_library.sqlite`: 전체 검색 DB
- `by_model/`: 모델별 프롬프트 CSV
- `by_tag/`: 제품/광고/UGC/카메라모션 등 태그별 CSV
- `by_media/image.csv`, `by_media/video.csv`
- `top_prompts_by_model.csv`: 모델별 상위 프롬프트
- `duplicate_prompt_groups.csv`: exact duplicate 그룹
- `near_duplicate_report.csv`: 유사 프롬프트 검토 목록 — 자동 삭제하지 않음
- `repo_overlap_report.csv`: 레포 간 프롬프트 겹침 분석
- `model_prompting_profiles.csv/json`: AI별 잘 맞는 프롬프트 구조
- `summary.json`: 전체 실행 요약

각 프롬프트 레코드는 모델/언어/입력모드/품질점수뿐 아니라 `source_url`, `license_spdx`, `verified_at`, `repo_commit`, `attribution`도 보존합니다.

## 중복 처리 정책

- **Exact duplicate**: 정규화 SHA-256으로 통합하고 가장 높은 점수 레코드를 대표로 사용합니다.
- **Near duplicate**: MinHash 후보화 + 토큰 Jaccard로 탐지하지만 자동 삭제하지 않습니다. `near_duplicate_report.csv`에서 사람이 검토합니다.
- **Repo overlap**: 동일 프롬프트 집합 겹침이 큰 레포 쌍을 별도 표시합니다.

## 품질/추천

프롬프트는 `prompt_quality_score`, `model_fit_score`, `combined_score`, `quality_tier(S~D)`를 갖습니다. `recommend_prompts.py`는 텍스트 관련도 + 품질 + 모델 적합도 + 원본 신뢰도를 조합해 랭킹합니다.

## 주의

이 ChatGPT 실행환경에서는 외부 GitHub로 대량 `git clone`이 차단되어 있어 공개 레포 73개의 실제 전체 다운로드는 여기서 대신 실행할 수 없습니다. **Windows에서 START_HERE.bat을 실행하면 그 단계가 자동 수행**됩니다.

라이선스가 `UNKNOWN`인 것은 사용 자유를 뜻하지 않습니다. 자세한 내용은 `LICENSE_GUIDE_KO.md`를 확인하세요.

## 메뉴형 실행기 / 결과 요약

- `MENU_LAUNCHER.bat`: 한 화면에서 63 Corpus 다운로드, Verified 다운로드, 73개 다운로드+인덱싱, 상태확인, 대시보드, 재인덱싱, 결과요약을 선택합니다.
- `RESULT_SUMMARY.bat`: 현재 실행 결과를 화면에 표시하고 `AI_PROMPT_LIBRARY\\reports` 아래에 `RESULT_SUMMARY.html`, `RESULT_SUMMARY.xlsx`, `RESULT_SUMMARY.json`을 생성합니다.
- `DOWNLOAD_73_ONLY.bat`: 73개 활성 레포 다운로드만 수행합니다.
- `DOWNLOAD_63_CORPUS_ONLY.bat`: 순수 Corpus 63개만 다운로드합니다.
- `DOWNLOAD_VERIFIED_ONLY.bat`: verified_original만 다운로드합니다.
- `DOWNLOAD_73_AND_INDEX.bat`: 73개 다운로드 후 추출/중복제거/인덱싱/대시보드까지 수행합니다.

## 클릭형 프롬프트 제작기 (GUI)

가장 쉬운 사용법:

1. `PROMPT_BUILDER_GUI.bat` 더블클릭
2. 만들고 싶은 내용 입력
3. AI 모델 드롭다운 선택
4. 용도/스타일/화면비/필수 요소 입력
5. `예제 검색` 또는 바로 `프롬프트 생성`
6. 결과를 `클립보드 복사` 또는 TXT/MD/JSON 저장

`MENU_LAUNCHER.bat`에서는 **9번 Make Prompt - GUI**를 선택하면 됩니다.

로컬 `prompt_library.sqlite`가 있으면 유사 프롬프트 예제를 자동 검색하여 참고하고, 아직 인덱싱하지 않았다면 모델별 Prompting Profile만으로도 프롬프트 생성은 가능합니다.


## Prompt Builder GUI v6.2 변경 사항
- 구조를 **기본설정 → AI별 동적 옵션 → 자동추천 → 프롬프트 생성** 순서로 개편했습니다.
- 이미지/동영상 구분을 자동 판단할 수 있게 했습니다.
- 구독 서비스(OpenAI / Gemini / Higgsfield)를 체크하면 추천 모델이 달라집니다.
- OpenAI는 이미지용 GPT Image 2, Gemini는 영상용 Veo 프로필, Higgsfield는 광고/UGC 영상에 우선 추천됩니다.
- 이미지와 동영상은 서로 다른 동적 옵션 UI를 사용합니다.


## Prompt Builder GUI v6.3 추가 기능
- OpenAI 이미지용 프롬프트 원클릭 생성 버튼 추가
- Gemini/Veo 영상용 프롬프트 원클릭 생성 버튼 추가
- Higgsfield 광고/UGC 영상용 프롬프트 원클릭 생성 버튼 추가
- 이미지/동영상 자동 구분 배지 추가
- 스토리보드 탭 및 스토리보드 저장 기능 추가
- 3종 저장 시 storyboard 파일도 함께 저장


## Prompt Builder GUI v6.4 카테고리 프리셋
기본설정 탭에 **카테고리 프리셋**을 추가했습니다.
- 화장품: 럭셔리 제품 광고, 제품/라벨 보존, 뷰티 조명, 허위 효능/인증 방지
- 건축: 건물 형태/재료/비례 보존, 수직선 교정, 건축 렌즈/동선 중심
- 물류: 창고/랙/장비/동선/안전 중심의 B2B 산업 표현
프리셋은 이미지용 6개 동적 옵션과 영상용 7개 동적 옵션을 동시에 채우므로, 이후 이미지/동영상을 바꿔도 해당 카테고리 기본값을 유지합니다.


## SNS Creative GitHub TOP50 (v6.5)
새로운 `social_creative` 모듈은 SNS 썸네일·Social Card·OG 이미지·배너·포스터·AI 이미지/영상 제작 기반 레포를 별도 관리합니다.

### 평가 기준
- GitHub Stars: 40%
- SNS 직접성: 25%
- 최근 활동성: 10%
- 템플릿/자동화성: 10%
- AI/프롬프트 연동성: 10%
- 라이선스 명확성: 5%

### 주요 파일
- `social_creative/social_repo_candidates.csv`: 58개 후보 풀
- `social_creative/REFRESH_SOCIAL_TOP50.bat`: 현재 GitHub 메타데이터 갱신 후 TOP50 확정
- `social_creative/social_top50_stars.csv`: 순수 Stars 상위 50
- `social_creative/social_top50_recommended.csv`: 종합 추천점수 상위 50
- `social_creative/social_creative_catalog.sqlite`: 검색용 SQLite
- `social_creative/DOWNLOAD_SOCIAL_TOP50.bat`: 선택된 50개 레포 다운로드
- `UNIFIED_SEARCH.bat`: 기존 프롬프트 DB + SNS 제작도구 통합검색

GitHub API는 `GITHUB_TOKEN` 또는 GitHub CLI 로그인 토큰이 있으면 인증 호출을 사용합니다. 인증이 없으면 58개 후보로 제한해 일반적인 비인증 REST 한도 안에서 1회 갱신이 가능하도록 설계했습니다.

## v6.6 — SNS Creative TOP50 전체 다운로드
SNS Creative TOP50을 모두 받고 싶으면 패키지 최상위의 `DOWNLOAD_ALL_SOCIAL_TOP50.bat`을 더블클릭하세요.
이 파일이 최신 Stars 갱신 → TOP50 확정 → SQLite/CSV/HTML 인덱싱 → Stars TOP50 50개 shallow clone까지 한 번에 수행합니다.
상태 확인은 메뉴 14번, 통합 검색은 메뉴 13번입니다.
