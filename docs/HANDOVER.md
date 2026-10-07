# HANDOVER — 신규 개발자 30분 온보딩

> **읽는 사람**: 본 프로젝트를 처음 받은 Mac 또는 Windows 개발자
> **소요 시간**: 30분 (Docker 설치된 경우 기준)

## 0. 첫 30초 — 프로젝트 정체

`agents-workspace`는 **제조 MES 멀티 에이전트 시스템**입니다:

- 7개 컨테이너 서비스 (Cell-MES + NL-Router + Cell-Scheduler + Frontend + n8n + Redis + DTP)
- Python 백엔드(FastAPI/uv) + Next.js 프론트엔드 + n8n 워크플로우 엔진
- Mac+Windows **SynologyDrive 폴더 공유** + git 협업 모델 (자세한 룰: [COLLABORATION.md](./COLLABORATION.md))

## 1. 사전 요구사항

### 공통 (Mac/Windows)
- Docker Desktop (최신)
- git (>= 2.30)
- Python 3.11 (uv가 자동 설치 처리 — 수동 설치 불필요)
- Node.js 20+ (frontend 로컬 개발 시)

### Mac
```bash
# 1. Docker Desktop 설치 (https://www.docker.com/products/docker-desktop/)
# 2. uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
# 3. (선택) agent-browser CLI
brew install rust  # cargo가 필요한 경우만
cargo install agent-browser
```

### Windows
```powershell
# 1. Docker Desktop 설치 (WSL2 backend 권장)
#    Settings → General → "Use the WSL 2 based engine" 체크
#    Settings → Resources → WSL Integration → 활성화
# 2. uv 설치
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# 3. (선택) agent-browser CLI
winget install Rustlang.Rust  # cargo가 필요한 경우만
cargo install agent-browser
```

## 2. SynologyDrive 셋업

이 단계가 가장 중요합니다 — 잘못 설정하면 git이 망가집니다.

### Mac
1. App Store → **Synology Drive Client** 설치
2. NAS 주소 + 계정 입력
3. 동기화 작업 추가: 원격 폴더 = `Drive/Development/agents-workspace_260416/agents-workspace_260409` → 로컬 폴더 = `~/SynologyDrive/Drive/Development/agents-workspace_260416/agents-workspace_260409`
4. **반드시** [COLLABORATION-SYNOLOGY-EXCLUDE.md](./COLLABORATION-SYNOLOGY-EXCLUDE.md) 따라 제외 패턴 등록

### Windows
1. https://www.synology.com 에서 Synology Drive Client 설치
2. 위와 동일 (Windows에서는 `C:\Users\<user>\SynologyDrive\...`)
3. **반드시** 제외 패턴 등록

확인:
```bash
cd <로컬 폴더>
ls .git/HEAD                  # git이 깨지지 않았는지
git status                    # 정상 출력
```

## 3. 환경변수 셋업

```bash
# 양쪽 OS 공통
cp .env.example .env.dev
# 필요시 값 편집 (대부분 기본값으로 OK)
```

VM/DP 5개 키(`VM_API_URL`, `VM_USERNAME`, `VM_PASSWORD`, `DP_BASE_URL`, `DP_API_KEY`)는 `.env.example`에 placeholder가 있습니다. 실 환경 연동 시 별도 시크릿 매니저(1Password 등)에서 받아 교체하세요.

## 4. 빌드 + 가동

### 양쪽 OS 동일 (Makefile 사용)
```bash
make up      # 모든 서비스 시작 (docker compose up -d)
make ps      # 상태 확인
make logs    # 로그 보기
```

### Make 미설치 환경
**Mac/Linux**:
```bash
docker compose up -d
docker compose ps
```

**Windows (PowerShell)**:
```powershell
docker compose up -d
docker compose ps
# 또는 기존 .ps1 스크립트
.\start-mes.ps1
```

확인 — 모든 서비스가 `Up` 상태:
```
SERVICE          STATUS
cell-mes         Up
cell-scheduler   Up
dtp              Up
frontend         Up
n8n              Up (healthy)
nl-router        Up
redis            Up
```

## 5. 접속 검증

브라우저로:

| URL | 기대 결과 |
|---|---|
| http://localhost:3000 | Next.js 프론트엔드 |
| http://localhost:8000/api/docs | Cell-MES Swagger |
| http://localhost:8001/docs | NL-Router Swagger |
| http://localhost:8002/api/docs | Cell-Scheduler Swagger |
| http://localhost:5678 | n8n Editor |
| http://localhost:8005/docs | DTP Swagger |
| http://localhost:3000/master/scenarios | 시나리오 편집 페이지 (Workflow 보라색 아이콘 클릭 → /edit 진입) |

## 6. 백엔드 테스트

```bash
make test
# 또는 직접:
cd agents/cell-mes && uv run pytest
```

기대: `25/25 PASS`

## 7. 프론트엔드 (선택)

컨테이너 안에서 자동 실행되므로 접속만 하면 됨. 로컬에서 직접 개발하려면:

```bash
cd agents/cell-mes/frontend
npm install
npm run dev   # http://localhost:3000 (이때 docker frontend 컨테이너는 stop 권장)
```

## 8. 자주 막히는 곳

### 8.1 Docker Desktop이 시작 안 됨 (Windows)
- WSL2 backend 활성화 확인
- `wsl --list -v`로 `docker-desktop` 보이는지
- 안 보이면: `wsl --update` 후 Docker Desktop 재시작

### 8.2 포트 충돌
- 3000, 8000, 8001, 8002, 8005, 5678, 6379 중 하나가 이미 점유
- `docker-compose.override.yml`로 포트 변경 (`docker-compose.override.yml.example` 복사 후 편집)

### 8.3 `.venv/`가 양쪽 PC에서 깨짐
- SynologyDrive 제외 가이드 미설정 → [COLLABORATION-SYNOLOGY-EXCLUDE.md](./COLLABORATION-SYNOLOGY-EXCLUDE.md) 적용
- 임시 복구: `rm -rf .venv && uv sync --python 3.11`

### 8.4 `.git/index.lock` 에러
- 위와 동일 원인. 즉시 가이드 적용
- 임시 복구: `rm .git/index.lock` (다른 git 프로세스 없는 거 확인 후)

### 8.5 `mes.db`가 갑자기 빈 상태
- SynologyDrive 동기화로 다른 PC의 빈 DB가 덮어씀
- 복구: `agents/cell-mes/data/_archive/mes.db.bak.*` 중 가장 최신 사용
- 또는: `make seed` (또는 `./scripts/seed-mes-db.{sh|ps1}`)

### 8.6 OCC import 에러 (DTP)
- DTP는 Docker 컨테이너 안에서만 실행 (host에서 실행 X)
- `docker compose up -d dtp` 후 `docker exec dtp python -c "from OCC.Core.STEPControl import STEPControlReader"` 으로 확인

## 9. 다음 단계

- [COLLABORATION.md](./COLLABORATION.md) 읽기 — 협업 룰 숙지
- [README.md](../README.md) 의 Architecture 섹션 — 시스템 이해
- [docs/02-design/features/](./02-design/features/) — 진행 중 기능 설계 문서
- [docs/04-report/features/](./04-report/features/) — 완료된 기능 보고서 (학습 자료)

## 10. 도움 요청

문제 발생 시:
1. 본 문서 §8 자주 막히는 곳 확인
2. `docker compose logs <service>` 로그 확인
3. 직전 작업자에게 작업 인계 메시지 확인
4. `_archive/` 디렉토리에 비슷한 충돌 흔적 있는지
