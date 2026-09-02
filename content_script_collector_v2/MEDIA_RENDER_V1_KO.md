# MEDIA_RENDER_V1

## 목표
`CREATIVE_PACKAGE_V1` 결과를 실제 미디어 생성 서비스와 FFmpeg에 연결하기 위한 중간 렌더링 계층입니다.

이 단계는 비용이 발생하는 외부 이미지/영상/TTS API를 직접 호출하지 않습니다. 대신 각 Provider에 보낼 요청 파일과 결과 자산의 저장 위치를 표준화하고, 자산이 준비되면 FFmpeg로 최종 MP4를 합성합니다.

## 1. 준비 실행

```bat
PREPARE_MEDIA_RENDER_V1.bat
```

또는:

```bat
python generator\media_render_v1.py "outputs_creative\<project_id>" --variant recommended --video-model kling
```

## 2. 생성되는 파일

프로젝트 폴더에 다음이 추가됩니다.

```text
render_plan.json
render_readiness.json
media_requests/
└─ <variant>/
   ├─ image_requests.json
   ├─ video_requests.json
   └─ tts_request.json
media_assets/
└─ <variant>/
   └─ README_KO.md
```

## 3. 외부 Provider 결과 저장 규칙

예를 들어 UGC 광고라면:

```text
media_assets/
├─ ugc/
│  ├─ scene_01.png
│  ├─ scene_01.mp4
│  ├─ scene_02.png
│  ├─ scene_02.mp4
│  ├─ ...
│  ├─ scene_07.mp4
│  └─ voiceover.mp3
├─ bgm.mp3          # 선택
└─ logo.png         # 선택
```

필수:
- 장면별 `scene_XX.mp4`
- `voiceover.mp3`
- 기존 `subtitles.srt`
- FFmpeg 설치

선택:
- `bgm.mp3`
- `logo.png`

## 4. readiness

`render_readiness.json`에서 다음을 확인합니다.

- `ffmpeg_ready`
- `missing_scene_videos`
- `voiceover_ready`
- `subtitles_ready`
- `bgm_ready`
- `logo_ready`
- `ready_to_render`

`ready_to_render=true`일 때 최종 합성을 실행할 수 있습니다.

## 5. 최종 MP4

```bat
RENDER_FINAL_AD_V1.bat
```

또는:

```bat
python generator\media_render_v1.py "outputs_creative\<project_id>" --variant recommended --video-model kling --execute
```

최종 파일:

```text
final/<variant>_ad_<duration>s.mp4
```

## 6. FFmpeg 합성 순서

1. Scene MP4 7개 연결
2. Voiceover 오디오 길이를 광고 길이에 맞춰 패딩/트림
3. BGM이 있으면 낮은 볼륨으로 믹스
4. Logo가 있으면 우측 하단 오버레이
5. 기존 SRT 자막을 영상에 Burn-in
6. H.264 + AAC 기반 최종 MP4 생성

## 7. 안전장치

- Creative Package `manifest.json`이 PASS가 아니면 중단
- Scene / image prompt / video prompt 개수가 다르면 중단
- Scene 영상이 하나라도 없으면 `--execute` 중단
- voiceover가 없으면 중단
- FFmpeg가 없으면 중단
- 오류 시 traceback과 FFmpeg stderr를 로그에 기록

## 8. 외부 API 연결 경계

현재 `image_requests.json`, `video_requests.json`, `tts_request.json`까지 생성하므로 OpenAI Image, Kling, Veo, Seedance, HeyGen 또는 TTS Provider 어댑터를 붙일 준비가 되어 있습니다.

실제 Provider API 호출은 API Key·요금·호출 정책 확인이 필요한 외부 서비스 변경/비용 발생 작업이므로 이 단계에서는 자동 실행하지 않습니다.

## 다음 단계

`PROVIDER_ADAPTER_V1`

- Image Provider Adapter
- Video Provider Adapter
- TTS Provider Adapter
- 요청/응답 상태 저장
- 실패 재시도
- 비용 추정/상한
- 생성 결과 자동 다운로드 및 `media_assets` 배치
