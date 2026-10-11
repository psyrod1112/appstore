## Just Type https://appstore.psyrod.dev/

### And welcome to enjoy and consume my projects

### 활용(배운) 기술
- JWT 인증과 역할 기반 인가(RBAC)로 관리자 전용 API 구현
- UNIQUE 제약과 트랜잭션으로 결제 원자성 보장, 동시 요청 시 중복 결제 방지
- XSS(escape, URL 검증)와 IDOR 취약점을 직접 재현하고 수정
- S3 호환 오브젝트 스토리지(R2) 연동, presigned URL로 구매자 전용 다운로드
- SMTP와 SPF/DKIM 도메인 인증으로 결제 영수증 발송, BackgroundTasks로 비동기 처리
- Tailwind 빌드 최적화 (3MB → 21KB)
- Docker 컨테이너화 (레이어 캐시, 볼륨, 시크릿 분리, 시간대 이슈 해결)
- GitHub 브랜치 → PR 워크플로우


### v2 할 일들
- 상품 수정/삭제 API + soft delete (지운 상품 때문에 구매 기록이 사라졌던 그 문제)
- 회원가입 이메일 인증 → 진짜 환영 메일
- 토큰을 httpOnly 쿠키로, 로그인 시도 횟수 제한
- (진짜 나중) 포트폴리오 계정으로 agar.io에 로그인하는 SSO ㅋㅋ
