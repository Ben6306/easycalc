# 홈 화면 unslop 체크리스트 (2026-11-13)

목표: 홈(`/`, 10개 언어)을 다듬기 모드로 정리하고, 첫 화면에 실제 계산 예시 영수증 1장을 둔다.

- [x] build.py `HOME_SAMPLE` 상수 추가 (연봉 5천만·1인·식대 20만 → netPay 결과값)
- [x] test_calc.py가 `HOME_SAMPLE`을 netPay 결과와 비교 → 요율 바뀌면 빌드 중단
- [x] calc.html 번역 블록 추가: homeH, homeLede, homeEx, homeTry (10개 언어)
- [x] 홈 마크업: 히어로(제목·설명·버튼 1개 + 영수증) → 계산기 목록(카드 전체 링크) → 가이드
- [x] 홈 CSS: `.home` 아래로 한정, 4px 단위 간격, 굵기 600 이하, 초록은 영수증 금액·버튼 1곳만
- [x] 안 쓰게 된 `.cards` 규칙 제거
- [x] PWA 설치 버튼: 초록 테두리 알약 → 조용한 고스트 버튼
- [x] `python3 _src/build.py` (검산 포함) 통과
- [x] 결과 HTML 확인 (ko·en·my, 모바일 폭), 다크 모드 변수 확인
- [x] PROJECT_NOTES.md 갱신
- [x] 커밋
