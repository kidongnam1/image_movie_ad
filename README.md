# image_movie_ad

이미지·동영상 광고 제작을 위한 프롬프트/콘텐츠 수집 및 생성 도구 모음입니다.

## 구성

### `ai_prompt_collector_v6_6`
이미지·동영상 생성 프롬프트 GitHub 저장소를 원본성/모델/용도별로 관리하고, 다운로드·추출·중복제거·검색 인덱싱·프롬프트 생성(GUI 포함)까지 지원하는 패키지입니다. 자세한 내용은 [`ai_prompt_collector_v6_6/README_KO.md`](ai_prompt_collector_v6_6/README_KO.md) 참고.

### `content_script_collector_v2`
SNS Shorts / Reels / TikTok 광고용 Content/Script(바이럴 훅, 숏폼 스크립트, CTA, Before/After, 제품 데모, 후기 등) 지식베이스를 수집·정규화하는 패키지입니다. 자세한 내용은 [`content_script_collector_v2/README_KO.md`](content_script_collector_v2/README_KO.md) 참고.

## 참고

각 도구는 Windows에서 `START_HERE.bat` 실행으로 시작합니다. GitHub 저장소를 대량으로 수집/캐시하는 참조용 산출물(`repos/` 등)은 용량이 크고 로컬에서 재생성 가능하므로 이 저장소에는 포함하지 않았습니다(`.gitignore` 참고).
