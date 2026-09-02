# SNS Creative GitHub TOP50 사용 가이드

## 목적
SNS 썸네일, YouTube 썸네일, Instagram/Facebook 광고 소재, OpenGraph/Social Card, 배너·포스터, 이미지 합성·편집, 짧은 영상 제작에 활용할 GitHub 레포를 Stars 우선으로 선별합니다.

## 평가 기준
- GitHub Stars: 40%
- SNS 제작 직접성: 25%
- 최근 활동성: 10%
- 자동화/템플릿: 10%
- AI/프롬프트 연동성: 10%
- 라이선스 명확성: 5%
- fork 또는 archived 레포는 최종 TOP50에서 제외

## 가장 쉬운 방법 — TOP50 모두 다운로드
패키지 최상위의 `DOWNLOAD_ALL_SOCIAL_TOP50.bat`을 더블클릭하세요.

이 한 번의 실행으로:
1. 58개 후보의 최신 GitHub Stars/라이선스/fork/archive/최근 push를 확인
2. Stars TOP50과 Recommended TOP50 생성
3. SQLite 검색 DB 생성
4. Stars TOP50 50개 레포를 전부 shallow clone/update
5. HTML 보고서 오픈

다운로드 정책:
- Git history 전체는 받지 않고 `--depth 1`
- partial clone `--filter=blob:none`
- Git LFS 대용량 파일은 자동 다운로드하지 않음
- 현재 소스 트리는 내려받음

## 메뉴에서 실행
`MENU_LAUNCHER.bat` → **11번** `Refresh + Download ALL SNS Creative Stars TOP50`

## 결과 위치
- 인덱스 DB: `social_creative/social_creative_catalog.sqlite`
- Stars TOP50: `social_creative/social_top50_stars.csv`
- 추천 TOP50: `social_creative/social_top50_recommended.csv`
- 보고서: `social_creative/social_top50_report.html`
- 실제 레포: `social_creative/SOCIAL_CREATIVE_LIBRARY/repos/`
- 다운로드 로그: `social_creative/SOCIAL_CREATIVE_LIBRARY/logs/`

## 상태 확인
`MENU_LAUNCHER.bat` → 14번 또는 `social_creative/CHECK_SOCIAL_TOP50.bat`

## 통합 검색
`MENU_LAUNCHER.bat` → 13번 `Unified Search (Prompts + SNS Tools)`
기존 73개 프롬프트 DB와 SNS Creative 도구 DB를 함께 검색합니다.

## 주의
GitHub Stars와 라이선스/활성도는 계속 변합니다. `REFRESH_SOCIAL_TOP50.bat`을 다시 실행하면 최신 상태로 재정렬됩니다.
코드 레포의 라이선스가 생성된 이미지·모델 가중치·외부 에셋의 상업 이용권을 자동 보장하지는 않습니다.
