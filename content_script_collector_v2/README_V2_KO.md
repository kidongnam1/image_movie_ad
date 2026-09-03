# Image Movie Ad — Script Generator V2.7

## 현재 활성 엔진

기존 실행 경로 `generator/script_generator_v2.py`는 유지되며 내부적으로 **V2.7**을 사용합니다.

V2.7은 V2.5의 강한 Hook + V2.6의 실광고 성과학습 위에 다음을 추가합니다.

1. A/B/C `CR-XXXXXXXXXXXX` Creative Registry 자동 등록
2. Meta / TikTok / Naver / Coupang / Generic 성과 파일 헤더 자동 매핑
3. CR ID를 이용한 상품·카테고리·Angle·Hook·Selling Point 자동 복원
4. 플랫폼/상품/카테고리/Angle/Hook/Creative 성과 대시보드
5. Windows 상품 이미지 입력창
   - Ctrl+V 클립보드 이미지
   - PNG/JPG/JPEG/WebP/BMP 파일
   - 직접 이미지 URL
   - 상품 페이지 URL 메타데이터
6. 이미지 출처·권리 상태 sidecar 기록 및 광고 사용 권리 Gate

---

## 가장 쉬운 사용법

### A. 상품 이미지까지 넣고 광고를 만들 때

```bat
OPEN_PRODUCT_IMAGE_INPUT_V27.bat
```

Windows 창에서 다음을 입력합니다.

- 상품명
- 상품 페이지 URL(선택)
- 반드시 강조할 특징
- 추가 특징
- Pain Point
- 타깃
- 광고 강도
- 상품 이미지

상품 이미지는 세 가지 방식으로 넣을 수 있습니다.

- 화면 캡처 후 `Ctrl+V`
- `이미지 파일 불러오기`
- `이미지 URL 불러오기`

URL은 **직접 이미지 URL(http/https)** 을 사용합니다. 상품 상세페이지 주소는 별도의 `상품 페이지 URL` 칸에 넣습니다.

이미지는 `input_images/YYYYMMDD/` 폴더에 로컬 보관됩니다.

이미지마다 다음 sidecar가 같이 생성됩니다.

```text
상품이미지.png.source.json
```

기록 항목:

- 원본 출처 타입
- 파일 원본 경로 또는 이미지 URL
- SHA-256
- 저장 시각
- 광고 사용 권리 상태

### 이미지 권리 Gate

광고/영상 생성에 이미지를 사용하려면 다음 중 하나를 선택해야 합니다.

- 내가 직접 촬영/제작
- 상업 이용 라이선스 보유
- 판매자/권리자 사용허락
- 퍼블릭 도메인/상업 이용 가능 라이선스

`확인 필요` 상태에서는 이미지를 미리볼 수 있지만 이미지가 포함된 광고/영상 생성은 중단합니다.

프로그램은 **워터마크 제거, 출처 은폐, 저작권 회피, 무단 이미지 세탁 기능을 제공하지 않습니다.** 실제 상업 이용 가능 범위는 권리자 허락·라이선스·플랫폼 약관을 확인해야 합니다.

### B. 텍스트 정보만으로 대본을 만들 때

```bat
GENERATE_SCRIPT_V2.bat
```

기존 사용법을 그대로 유지합니다.

---

## Creative Package

```bat
GENERATE_CREATIVE_PACKAGE_V1.bat
```

UGC / Product Demo / Cinematic 결과를 생성하며 V2.7 Creative Registry가 활성화됩니다.

이미지 GUI에서 실행하면 선택한 상품 이미지 경로와 상품 페이지 URL도 `project.json`에 전달됩니다.

---

# Creative ID 운영 규칙

V2.7에서 A/B/C 후보는 다음과 같은 ID를 갖습니다.

```text
A  CR-XXXXXXXXXXXX
B  CR-XXXXXXXXXXXX
C  CR-XXXXXXXXXXXX
```

실제 광고 플랫폼에서 광고명 또는 소재명에 이 ID를 포함하는 것을 권장합니다.

예:

```text
Golf_Rangefinder_A_CR-1234ABCDEF56
```

이후 플랫폼에서 내려받은 성과 파일에 이 광고명이 들어 있으면 V2.7이 `CR-...`를 찾아 Creative Registry에서 다음 정보를 복원합니다.

- 상품명
- 카테고리
- Angle
- Hook
- Selling Point

과거 V2.6의 `experiment_plan.json`도 등록할 수 있습니다.

```bat
REGISTER_EXPERIMENT_PLAN_V27.bat
```

`experiment_plan.json` 옆에 `project.json`이 있으면 상품명과 카테고리까지 자동 복원합니다.

---

# 플랫폼 성과 파일 가져오기

가장 쉬운 방법:

```bat
IMPORT_PLATFORM_PERFORMANCE_V27.bat
```

지원 입력:

- CSV
- JSON
- XLSX
- XLSM

플랫폼 선택:

- auto
- meta
- tiktok
- naver
- coupang
- generic

`auto`는 헤더 별칭을 이용해 best-effort로 플랫폼을 감지합니다. 플랫폼의 export 형식은 변경될 수 있으므로 알 수 없는 헤더는 버리지 않고 `unmapped_headers`로 보고합니다.

CR ID가 없는 기존 광고 파일은 기본 상품명/카테고리를 직접 입력해 가져올 수 있습니다.

V2.6 공통 입력 형식도 계속 지원합니다.

```bat
IMPORT_AD_PERFORMANCE_V26.bat
```

---

# 성과 DB

- Content DB: `database/content_script.sqlite`
- 광고 성과 DB: `database/ad_performance.sqlite`

성과 저장은 Snapshot-safe입니다.

- 같은 광고·같은 기간·같은 수치 → SKIP
- 같은 광고·같은 기간의 갱신 누적수치 → UPDATE
- 새로운 광고/기간 → INSERT

따라서 누적 export를 반복 가져와도 같은 성과를 단순 합산해 과대집계하지 않습니다.

운영 SQLite와 `input_images/`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

---

# V2.6/V2.7 성과학습 지표

| 지표 | 비중 |
|---|---:|
| 2초 유지율 | 20% |
| 3초 유지율 | 10% |
| CTR | 25% |
| 상세페이지 유입률 | 10% |
| 구매전환율 | 25% |
| ROAS | 10% |

성과 보정 상한:

- Category + Angle: ±6점
- 동일 Hook: ±3점
- 동일 Creative: ±2점
- 최종 합산: ±8점

표본이 적으면 Bayesian shrinkage / 노출 신뢰도 보정으로 영향이 작아집니다.

성과학습은 **안전 Gate → 품질 Gate**를 통과한 후보끼리 순위만 조정합니다.

---

# V2.7 로컬 성과 대시보드

```bat
OPEN_PERFORMANCE_DASHBOARD_V27.bat
```

생성 파일:

```text
outputs/performance_dashboard_v27.html
outputs/performance_dashboard_v27.json
```

HTML은 외부 CDN이나 Chart.js가 필요 없는 standalone 파일입니다.

필터:

- 플랫폼
- 상품
- 카테고리
- Angle

주요 KPI:

- 노출
- 2초 유지율
- 3초 유지율
- CTR
- 상세페이지 유입률
- 구매전환율
- 구매수
- 매출
- 광고비
- ROAS

비교표:

- Angle별 CTR / CVR / ROAS
- Hook별 CTR / CVR / ROAS
- 상품별 성과
- Creative ID별 성과
- 플랫폼별 ROAS

---

# 전체 운영 루프

```text
상품 + 강조점 + 상품 이미지 입력
        ↓
V2.7 대본 / Creative Package
        ↓
A/B/C CR Creative ID 생성 및 Registry 등록
        ↓
실제 광고 플랫폼에서 사람이 승인/게시
        ↓
플랫폼 성과 CSV/XLSX 다운로드
        ↓
IMPORT_PLATFORM_PERFORMANCE_V27.bat
        ↓
플랫폼 헤더 자동 변환 + CR ID 메타데이터 복원
        ↓
ad_performance.sqlite
        ↓
OPEN_PERFORMANCE_DASHBOARD_V27.bat
        ↓
Hook / Angle / Product / Creative 성과 비교
        ↓
다음 V2.7 생성에서 성과학습 반영
```

프로그램은 실제 광고 게시나 예산 지출을 자동 수행하지 않습니다.

---

# 전체 검증

```bat
VERIFY_DB_GENERATOR.bat
```

검증 범위:

1. Python 구문검사
2. V2.5 대본 회귀
3. V2.6 성과 DB / Snapshot UPDATE / 학습 회귀
4. V2.7 Creative Registry
5. Meta/TikTok/Naver/Coupang 어댑터
6. Standalone Dashboard
7. 이미지 파일/권리 sidecar/URL 안전검사
8. 기존 Creative Package 회귀
9. 실제 Content DB 연동
10. 검증용 격리 Performance DB

---

# 광고·이미지 안전 원칙

- 허위 후기 금지
- 가짜 희소성 금지
- 근거 없는 1위·최고·100% 금지
- 치료·완치 등 의료적 과장 금지
- 사용자가 제공한 성능·효능 수치는 집행 전 공식 자료 확인
- 이미지 워터마크 제거/출처 은폐/권리 회피 기능 없음
- 라이선스가 확인되지 않은 이미지는 광고 생성 Gate에서 차단

외부 이미지/영상/TTS 또는 광고 플랫폼 API 호출 중 비용이 발생하는 단계는 자동 집행하지 않습니다.
