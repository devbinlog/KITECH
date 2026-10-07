# Security Rotation Log

> 시크릿 회전 이력. 새 회전 시 본 파일 위에 항목 추가.

## 2026-05-02 — n8n 노출 차단 + auth 보강 (audit C4)

**계기**: security-reviewer 감사 CRITICAL C4 — n8n(2.18.5)이 0.0.0.0:5678 인증 0건으로 LAN
공격자가 워크플로우를 임의 실행할 수 있었음.

**조치**:
1. **포트 바인딩 제한**: `docker-compose.yml` 의 n8n 서비스 ports를 `5678:5678` →
   `127.0.0.1:5678:5678` 로 변경. 호스트 loopback에서만 접근 가능, 외부 LAN은 차단.
   docker 내부 네트워크의 cell-mes는 service name `n8n:5678` 으로 변함없이 접근 가능.
2. **N8N_BASIC_AUTH_* 환경변수**: 추가했으나 n8n 1.0+ 에서 deprecated 되어 미작동 확인.
   대안: 첫 방문 시 사용자 관리(owner account) 가입을 통해 인증 활성화. 인계 후
   첫 셋업 시 `http://localhost:5678` 방문해서 sign-up 완료 권고.
3. **n8n_runner.py**: `httpx.AsyncClient(auth=(USER, PASS))` 패턴 추가 — 향후 Basic
   Auth 또는 owner account 비밀번호로 인증 시 사용.
4. **방어선 검토**:
   - LAN → cell-mes:8000: cell-mes endpoint 인증 필요 (audit 동시 처리됨)
   - LAN → n8n:5678: 차단 (127.0.0.1 binding)
   - cell-mes → n8n:5678 (docker network 내부): 통제됨

**검증**:
- `curl http://localhost:5678/healthz` 200 (loopback OK)
- `curl http://<LAN-IP>:5678/healthz` connection refused (외부 차단 OK — 권장 추가 검증)

## 2026-05-02 — 초기 회전 (audit-driven)

## 2026-05-02 — 초기 회전 (audit-driven)

**계기**: security-reviewer 감사 CRITICAL C1 — `SECRET_KEY` 및 `INTERNAL_SERVICE_KEY`가
공개 소스코드의 default placeholder("your-secret-key-change-in-production",
"internal-service-key-change-in-production")로 노출. JWT 위조 + 내부 서비스 인증 우회 가능.

**대상**:
- `cell-mes` 서비스의 JWT 서명 키 (`SECRET_KEY`)
- 서비스 간 통신 인증 키 (`INTERNAL_SERVICE_KEY`)

**조치**:
1. `python -c "import secrets; print(secrets.token_urlsafe(64))"` 로 신규 64-byte URL-safe 토큰 2개 생성
2. 루트 `.env` 파일에 적재 (gitignore'd, SynologyDrive 동기화 대상)
3. `docker-compose.yml` 의 `cell-mes` / `nl-router` 서비스 environment에 `${SECRET_KEY}` / `${INTERNAL_SERVICE_KEY}` 노출
4. `docker compose up -d --force-recreate cell-mes nl-router` 로 신규 키 적용
5. 기존 발급된 모든 JWT 토큰 자동 무효화 (서명 키 변경)
6. 운영 환경 (`.env.prod`)도 동일 패턴 적용 권고 (다음 운영 배포 시)

**영향**:
- 기존 로그인 사용자는 재로그인 필요 (JWT 무효)
- 내부 서비스 호출 시 새 `INTERNAL_SERVICE_KEY` 헤더 필요 (호출자가 동일 .env 사용 시 자동 동기화)

**검증**:
- `docker compose exec cell-mes printenv SECRET_KEY` — 새 값 노출 확인
- `curl http://localhost:8000/health` — 200 OK
- 컨테이너 로그에 "Using default SECRET_KEY is insecure!" 경고 사라짐

**다음 회전 권고**:
- 90일 후 또는 시크릿 노출 의심 시
- 시크릿 매니저 (1Password / HashiCorp Vault / AWS Secrets Manager) 도입 후 자동화

## 운영 권고

1. **루트 `.env` 파일은 절대 git에 커밋 금지** — `.gitignore`에 등록되어 있지만 매번 확인
2. **SynologyDrive 평문 동기화 = NAS에 시크릿 평문 보관** — 진정한 보안을 위해서는 시크릿 매니저 필요
3. **회전 시 양쪽 PC가 동일 `.env`를 가져야 함** — SynologyDrive 동기화 완료 확인 후 두 번째 PC도 컨테이너 재시작
4. **회전 직후 기존 발급 JWT 토큰 무효화**: 이는 의도된 동작
5. **`.env.example` 의 placeholder 값은 영원히 placeholder로** — 실 시크릿 절대 commit 금지

## 시크릿 발급 명령

### Python
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### OpenSSL (모든 OS)
```bash
openssl rand -base64 64
```

### PowerShell (Windows native)
```powershell
[Convert]::ToBase64String((1..64 | ForEach-Object { Get-Random -Min 0 -Max 256 }))
```
