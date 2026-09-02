# CREATIVE_PACKAGE_V1

## 목표
상품 정보를 한 번 입력하면 Content DB를 근거로 다음 3종 광고 제작 패키지를 자동 생성합니다.

- UGC 후기형
- Product Demo 제품 시연형
- Cinematic 브랜드형

현재 단계의 최종 산출물은 **영상 생성 직전까지 사용할 수 있는 구조화된 광고 패키지**입니다. MP4 렌더링은 다음 마일스톤에서 외부 이미지/영상/TTS Provider와 FFmpeg를 연결해 구현합니다.

## 입력

필수:
- 상품명

선택:
- 상품 설명
- 타깃 고객
- 광고 길이: 15 / 30 / 60초
- 상품 URL
- 상품 이미지 경로

## 실행

Windows에서는:

```bat
GENERATE_CREATIVE_PACKAGE_V1.bat
```

직접 실행:

```bat
python generator\creative_package_v1.py "안티에이징 세럼" ^
  --description "탄력과 보습을 위한 데일리 세럼" ^
  --target "40~60대 여성" ^
  --duration 30 ^
  --require-db
```

기존 `project.json`으로 재생성:

```bat
python generator\creative_package_v1.py --project-file "outputs_creative\프로젝트ID\project.json" --require-db
```

## 출력 구조

```text
outputs_creative/
└─ <project_id>/
   ├─ project.json
   ├─ strategy.md
   ├─ creative_scores.json
   ├─ compliance_report.json
   ├─ manifest.json
   ├─ ugc/
   │  ├─ script.md
   │  ├─ storyboard.md
   │  ├─ shot_list.json
   │  ├─ image_prompts.json
   │  ├─ video_prompts.json
   │  ├─ voiceover.txt
   │  └─ subtitles.srt
   ├─ product_demo/
   │  └─ 동일 7종 파일
   └─ cinematic/
      └─ 동일 7종 파일
```

## 단계별 통과 기준

1. 기존 DB 연결 및 Script Generator V2 호출
2. `project.json` 생성
3. UGC / Product Demo / Cinematic 3종 생성
4. 각 광고를 7 Scene으로 분해하고 storyboard 생성
5. `shot_list.json`에 시작/종료 시간, 대사, 자막, 화면, 카메라 저장
6. 장면별 이미지 Prompt와 Kling/Veo/Seedance 영상 Prompt 생성
7. `voiceover.txt`와 SRT 자막 생성
8. Hook/CTA/제품집중도/명확성/Claim Safety 점수화
9. 금지표현 검사 후 `manifest.json`에서 전체 패키지 PASS/FAIL 판정

## 광고 점수

`creative_scores.json`은 아래 기준으로 3개 광고를 비교합니다.

- Hook Strength
- CTA Clarity
- Product Focus
- Clarity
- Claim Safety
- Total

가장 높은 Total을 `recommended_variant`로 기록합니다.

## Compliance Gate

현재 자동 BLOCK 대상 예시는 다음과 같습니다.

- 치료
- 완치
- 주름 제거
- 여드름 치료
- 100%
- 즉시 효과
- 완전히 사라

이는 1차 안전 필터입니다. 실제 광고 집행 전에는 제품 상세정보, 화장품 표시광고 관련 규정, 플랫폼 정책을 별도로 최종 확인해야 합니다.

## 로깅

실행 진행 상황은 화면에 `print()`로 표시하고 동시에 아래에 저장합니다.

```text
logs/app.log
```

예외 발생 시 traceback 전체를 화면과 로그에 남깁니다.

## 검증

```bat
VERIFY_CREATIVE_PACKAGE_V1.bat
```

검증 내용:

- Python unittest
- 실제 Content DB 연결
- 3종 광고 end-to-end 생성
- 필수 파일 누락 여부
- Compliance PASS 여부
- 추천 광고 버전 생성 여부

성공 기준:

```text
VERIFY_CREATIVE_PACKAGE_V1 PASS
```

## 다음 마일스톤

`MEDIA_RENDER_V1`

1. 실제 상품 URL/이미지 분석
2. 이미지 Provider Adapter
3. Kling/Veo/기타 영상 Provider Adapter
4. TTS Provider Adapter
5. 장면별 생성 결과 캐시 및 재시도
6. FFmpeg Scene 연결
7. 음성 + 자막 + BGM + 로고 합성
8. `final_ad.mp4` 생성
9. GUI
