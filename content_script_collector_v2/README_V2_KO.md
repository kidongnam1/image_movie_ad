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

---

# Creative Package V1

Script Generator V2 위에 광고 제작 패키지 오케스트레이터를 추가했습니다.

실행:

```bat
GENERATE_CREATIVE_PACKAGE_V1.bat
```

검증:

```bat
VERIFY_CREATIVE_PACKAGE_V1.bat
```

상품 1개 입력으로 아래 광고 3종을 동시에 만듭니다.

- UGC 후기형
- Product Demo 제품 시연형
- Cinematic 브랜드형

각 광고별 산출물:

- `script.md`
- `storyboard.md`
- `shot_list.json`
- `image_prompts.json`
- `video_prompts.json`
- `voiceover.txt`
- `subtitles.srt`

프로젝트 공통 산출물:

- `project.json`
- `strategy.md`
- `creative_scores.json`
- `compliance_report.json`
- `manifest.json`

상세 설명은 `CREATIVE_PACKAGE_V1_KO.md`를 참고하세요.

---

# MEDIA_RENDER_V1

Creative Package 결과를 실제 미디어 파일과 FFmpeg 최종 MP4에 연결하는 렌더링 계층입니다.

준비:

```bat
PREPARE_MEDIA_RENDER_V1.bat
```

최종 합성:

```bat
RENDER_FINAL_AD_V1.bat
```

핵심 기능:

- `render_plan.json` 생성
- Image / Video / TTS Provider 요청 JSON 생성
- Scene 영상·voiceover·자막·FFmpeg readiness 검사
- Scene 영상 자동 연결
- Voiceover 길이 보정
- BGM 선택 믹스
- Logo 선택 오버레이
- SRT 자막 Burn-in
- `final/<variant>_ad_<duration>s.mp4` 출력

외부 이미지/영상/TTS API는 비용과 API Key 확인이 필요한 단계이므로 직접 호출하지 않고 요청 파일과 자산 규격까지만 자동화합니다.

상세 설명은 `MEDIA_RENDER_V1_KO.md`를 참고하세요.
