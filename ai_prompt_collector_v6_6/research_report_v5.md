# Research Report v5

## 조사 결론
- 이미지/동영상 프롬프트 생태계는 모델별 전용 corpus와 범용 multi-model corpus가 혼재합니다.
- Runway/Vidu처럼 대형 독립 corpus가 약한 모델은 multi-model corpus + model prompting profile + tooling으로 보완하는 편이 합리적입니다.
- fork=false는 원본성의 중요한 신호지만 내용 복제까지 보증하지 않으므로 실제 clone 후 repo overlap 분석이 필요합니다.

## v5에서 새로 강화한 모델
- Qwen Image 3
- LTX Video
- CogVideoX / Hunyuan Video tooling
- Higgsfield tooling
- Z-Image, Mochi 등 모델 프로필/키워드 확장

## 검증 우선순위
1. verified_original + corpus
2. probable_original + 높은 repo_quality_score
3. verified tooling
4. candidate는 기본 수집에서 제외

## 데이터 사용 주의
레포 코드 라이선스와 프롬프트/예제 이미지 콘텐츠 라이선스는 동일하지 않을 수 있습니다. 상업적 재사용 전 원본 레포와 원출처 조건을 별도 확인해야 합니다.
