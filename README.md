# EasyCalc (easycalc.co.kr)

설치·가입 없이 바로 쓰는 생활 계산기 사이트.

## 현재 계산기
- 더치페이 계산기 (똑같이 / 항목별)
- 대출이자 계산기 (원리금균등 / 원금균등 / 만기일시)
- 연봉 실수령액 계산기 (2026년 7월 요율)

## 지원 언어
한국어(/) · English(/en/) · Tiếng Việt(/vi/) · 简体中文(/zh/) · नेपाली(/ne/) · Bahasa Indonesia(/id/) · ខ្មែរ(/km/) · Oʻzbekcha(/uz/) · ไทย(/th/) · မြန်မာ(/my/)
- 번역 원문은 `_src/calc.html` 안의 `window.I18N`에 있음
- 원어민 검수 권장: 특히 km, my, ne, uz

## 사이트 구조 (2026-10-18 개편)
- `/` 언어별 홈 · `/salary/` `/loan/` `/dutch/` 계산기 · `/guide/` 가이드 · `/about/` `/contact/` `/privacy/`
- 다른 언어는 앞에 `/en/`, `/vi/` 등이 붙음. 가이드·소개·문의·개인정보처리방침은 한국어·영어만 있음
- 문의 이메일: easycalc.kr@gmail.com

## 수정하는 방법
1. 원본은 `_src/` 폴더에만 있음 (GitHub Pages에 공개되지 않음)
   - 계산기·번역: `_src/calc.html`
   - 가이드 글: `_src/guides/ko/*.html`, `_src/guides/en/*.html` (첫 줄 `<!--{...}-->`가 제목·설명)
   - 소개·문의·개인정보: `_src/pages/`
2. 수정 후 터미널에서 `cd ~/Documents/easycalc && python3 _src/build.py`
3. 미리보기: `python3 -m http.server 8000` 실행 후 브라우저에서 http://localhost:8000
4. GitHub Desktop으로 Commit → Push

## 파일 구성
| 파일 | 역할 |
|---|---|
| index.html | 사이트 본체 |
| robots.txt | 검색엔진 수집 허용 |
| sitemap.xml | 검색엔진용 페이지 목록 |
| CNAME | GitHub Pages 커스텀 도메인 지정 |

## 배포
- 호스팅: GitHub Pages (이 폴더 전체를 저장소 루트에 업로드)
- 도메인: 가비아 easycalc.co.kr
  - A @ → 185.199.108.153 / .109.153 / .110.153 / .111.153
  - CNAME www → <GitHub아이디>.github.io.
- HTTPS: GitHub Settings → Pages → Enforce HTTPS

## 유지보수 일정
- 매년 1월: 건강보험·장기요양·고용보험 요율 확인
- 매년 7월: 국민연금 기준소득월액 상·하한 확인 (2026.7~2027.6: 상한 659만 / 하한 41만)

## 할 일
- [ ] GitHub 저장소 생성 및 업로드
- [ ] 가비아 DNS 설정
- [ ] HTTPS 활성화
- [ ] 구글 서치 콘솔 / 네이버 서치어드바이저 등록
- [x] 탭별 페이지 분리 (/dutch, /loan, /salary)
- [x] 광고 심사용 페이지 (가이드 글 9편, 개인정보처리방침, 소개, 문의)
- [ ] 애드센스 신청 (색인 확인 후)
