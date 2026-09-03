# Script Generator V2.5 패치 노트

## 목표
V2.4의 카테고리 중립 구조는 유지하면서, 광고 대본의 첫 2초·Hook·Selling Point 반영을 더 강하게 개선합니다.

## 핵심 변경

1. **강도 4~5용 Strong Gate**
   - 요청 최소점수가 80점이어도 강도 4~5에서는 Hook 품질 기준을 최소 84점으로 상향합니다.

2. **사용자 지정 Selling Point 우선**
   - `반드시 강조할 특징`의 첫 번째 값을 `primary_selling_point`로 지정합니다.
   - TOP1 Hook 선정 시 primary Selling Point를 포함한 문장에 우선 가중치를 줍니다.
   - 30초/45초 대본에서 필수 강조점 Coverage를 검사합니다.

3. **Hook 문장 강화**
   - 문제공격 / 손실회피 / 호기심 / 비교 / 반전 / 발견 / 증거 7개 Angle 사용
   - 첫 2초 Power, Specificity, Purchase Desire를 별도 평가합니다.
   - `오늘 소개`, `정말 좋은`, `인생템`, `무조건 사세요` 같은 평범하거나 저품질 표현은 Generic Penalty 대상입니다.

4. **대본 구조 강화**
   - HOOK → TENSION → REVEAL → PROOF → CTA
   - 강도 4~5에서는 문제의 반복 비용을 더 분명하게 보여주되, 확인되지 않은 공포·효능·품절·후기 조작 표현은 사용하지 않습니다.

5. **카테고리 중립 유지**
   - 뷰티 / 골프 / 자동차 / 반려동물 / 여행 / 주방 / 패션 / 식품 / 생활가전 / 전자기기 / 스포츠 / 사무 / 생활용품 / 일반 상품
   - 비화장품 대본에서 피부·제형·바르기 문맥이 강제로 들어오지 않는지 자동 검사합니다.

6. **자동 품질 감사**
   - Hook 30개 생성 여부
   - 최저 Hook 점수
   - Generic Hook hit
   - 금지 표현 hit
   - 15/30/45초 필수 강조점 Coverage
   - 비화장품 카테고리 중립성

## BAT 사용법

`GENERATE_SCRIPT_V2.bat` 실행 후 아래 순서로 입력합니다.

1. 상품명
2. 반드시 강조할 특징
3. 추가 특징
4. 고객 Pain Point
5. 타깃 고객
6. 광고 강도 1~5

예시:

```text
상품명: 골프 거리측정기
반드시 강조: 0.2초 측정, 손떨림 보정
추가 특징: 800m 측정, 150g 초경량
Pain Point: 거리 판단이 늦어 샷 템포가 끊김
타깃: 40~60대 골퍼
강도: 5
```

## Creative Package

`GENERATE_CREATIVE_PACKAGE_V1.bat`에서도 동일하게 Selling Point / Pain Point / 강도를 입력할 수 있습니다. V2.5 Hook이 UGC / Product Demo / Cinematic 패키지에 전달됩니다.

## 검증

`VERIFY_DB_GENERATOR.bat` 실행 시:

- Python syntax check
- 세럼 / 골프 거리측정기 / 무선 청소기 / 여행용 캐리어 / 고양이 자동급식기 5상품 회귀테스트
- 숫자 쉼표 특징 `18,000Pa` 보존
- 사용자 1순위 Selling Point TOP1 Hook 반영
- 30초/45초 필수 강조점 100% Coverage
- Generic / 금지 Hook 0건
- 실제 Content DB 연결 확인

을 순차 검사합니다.

## 광고 표현 원칙
강하고 자극적인 문장을 사용하되, 근거 없는 효능·절대 표현·가짜 후기·가짜 희소성·허위 수치·의료적 단정은 생성하지 않습니다. 사용자가 입력한 수치나 성능도 실제 광고 집행 전 공식 상세페이지 또는 제조사 자료와 대조해야 합니다.
