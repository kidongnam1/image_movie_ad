# Windows BAT 인코딩 수정

증상:
- `'al'은(는)...`
- `'cript'은(는)...`
- `'errorlevel'은(는)...`
- 한글 상품명이 `_몃읆`처럼 깨짐

원인:
- 기존 BAT가 UTF-8/LF로 생성되어 일부 Windows cmd.exe 환경에서 명령행 자체가 잘못 해석됨.
- 한글 인수도 시스템 코드페이지와 UTF-8 사이에서 깨질 수 있음.

수정:
- 실행 BAT를 ASCII + CRLF로 재작성
- 검증 BAT에서는 상품명을 `serum`으로 사용하여 인코딩 변수를 제거
- 실제 DB 연동 검증에는 상품명 언어가 중요하지 않음
- 실제 한국어 상품 생성은 PowerShell에서 Python을 직접 호출하는 방법을 권장

한국어 세럼 생성:
```powershell
python .\generator\script_generator_v2.py "세럼" --require-db
```
