# Script Generator V2.7 패치 노트

## 목표

V2.6의 Closed-loop 성과학습 위에 **플랫폼 원본 성과 자동변환 + Creative Registry + 로컬 KPI Dashboard + Windows 이미지 입력**을 추가했습니다.

## 핵심 변경

### 1. Creative Registry
- A/B/C `CR-XXXXXXXXXXXX` 자동 등록
- 광고명 속 CR ID를 이용해 상품/카테고리/Angle/Hook/Selling Point 복원
- 과거 experiment_plan.json 소급 등록 지원
- experiment_plan 옆 project.json 자동 참조

### 2. 플랫폼 원본 성과 어댑터
지원 모드:
- meta
- tiktok
- naver
- coupang
- generic
- auto

입력 파일:
- CSV
- JSON
- XLSX
- XLSM

헤더 alias 방식으로 공통 V2.6 성과 스키마로 정규화합니다. 알 수 없는 열은 `unmapped_headers`로 보고해 silently drop하지 않습니다.

### 3. Standalone 성과 Dashboard
`OPEN_PERFORMANCE_DASHBOARD_V27.bat`

- 외부 CDN 없음
- 인터넷 없이 로컬 HTML 실행
- 플랫폼/상품/카테고리/Angle 필터
- 2초/3초 유지율
- CTR
- 상세페이지 유입률
- 구매전환율
- 구매/매출/광고비/ROAS
- Angle별 CTR/CVR/ROAS
- Hook별 CTR/CVR/ROAS
- 상품별/Creative별 성과

### 4. Windows 상품 이미지 입력 GUI
`OPEN_PRODUCT_IMAGE_INPUT_V27.bat`

지원:
- Ctrl+V 클립보드 이미지
- PNG/JPG/JPEG/WebP/BMP 파일
- 직접 http/https 이미지 URL
- 상품 페이지 URL 메타데이터
- 이미지 미리보기

로컬 저장:
`input_images/YYYYMMDD/`

이미지마다 `.source.json` 생성:
- source_type
- source URL/file
- SHA-256
- rights_basis
- approved_for_ad_use
- 기록 시각

### 5. 저작권/권리 Gate
다음 권리 상태 중 하나를 확인해야 이미지가 포함된 광고/패키지를 생성할 수 있습니다.
- 직접 촬영/제작
- 상업 이용 라이선스 보유
- 판매자/권리자 사용허락
- 퍼블릭 도메인/상업 이용 가능 라이선스

`확인 필요` 상태는 미리보기만 가능하고 광고 생성은 차단합니다.

지원하지 않는 기능:
- 워터마크 제거
- 출처 은폐
- 저작권 추적 회피
- 무단 이미지 세탁

### 6. URL 안전 처리
- http/https만 허용
- localhost/loopback/private/link-local/reserved/multicast 차단
- 인증정보 포함 URL 차단
- redirect 단계별 재검사
- 직접 image Content-Type만 허용
- 최대 20MB

### 7. 운영 데이터 보호
- `input_images/` Git ignore
- `ad_performance.sqlite`, WAL, SHM Git ignore 유지
- selftest는 임시 Performance DB를 사용해 운영 Registry 오염 방지

## 권장 운영 흐름

```text
OPEN_PRODUCT_IMAGE_INPUT_V27.bat
  ↓
대본/패키지 생성 + CR ID
  ↓
광고명에 CR ID 포함
  ↓
플랫폼에서 실제 광고 집행
  ↓
IMPORT_PLATFORM_PERFORMANCE_V27.bat
  ↓
OPEN_PERFORMANCE_DASHBOARD_V27.bat
  ↓
Hook/Angle/Creative 성과 분석
  ↓
다음 V2.7 생성에 V2.6 성과학습 자동 반영
```

## 비용 경계

실제 광고 게시, 광고비 집행, 외부 유료 이미지/영상/TTS API 호출은 자동 실행하지 않습니다.
