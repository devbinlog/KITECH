# 협업 가이드 — Mac ↔ Windows 분산 개발

> **2026-05-02** 본 프로젝트는 **SynologyDrive 폴더 동기화 + git** 모델(Approach B)로 협업합니다.
> 안전한 운영을 위한 룰을 본 문서에 정리합니다.

## 0. TL;DR — 5가지 룰

1. **동시 작업 금지** — 같은 시점에 양쪽 PC에서 코드 변경 ❌
2. **작업 시작 전 동기화 완료 확인** — Synology Drive Client에서 "최신" 상태인지 확인
3. **`.git/`, `.venv/`, `node_modules/`는 절대 동기화 X** — [SynologyDrive 제외 가이드](./COLLABORATION-SYNOLOGY-EXCLUDE.md) 따라 설정
4. **빌드 산출물 커밋 금지** — pre-commit hook이 자동으로 검사함
5. **Conflict 파일 발견 즉시 보고** — 방치 금지, `_archive/`로 격리 + 양쪽 협의

## 1. 작업 모델

```
시간축:
T0   Windows xession 작업 시작
     └─ git status 확인 → 동기화 완료 확인 → 변경 → commit → 작업 종료
T1   (양쪽 PC가 SynologyDrive로 동기화 — 자동, 분 단위)
T2   Mac dev 작업 시작
     └─ git status 확인 → 동기화 완료 확인 → 변경 → commit → 작업 종료
T3   (다시 동기화)
```

**금지**:
- `T0~T2` 사이에 Mac에서 같은 파일 변경
- `T2~T3` 사이에 Windows에서 같은 파일 변경
- `git rebase`, `git reset --hard`, `git push --force`-style 작업 (history 분기 후 양쪽 동기화 시 복구 불가)

## 2. 작업 인계 체크리스트

### 시작 전 (작업을 받는 쪽)

- [ ] SynologyDrive Client 트레이 아이콘이 "최신 상태" / "동기화 완료" 표시
- [ ] `git status` 깨끗 (uncommitted 변경 0건 — 있으면 `git stash` 또는 commit 후 진행)
- [ ] `git log -1` 마지막 commit이 상대방의 최신 작업과 일치
- [ ] `docker compose ps` — 모든 서비스 healthy

### 종료 전 (작업을 끝내는 쪽)

- [ ] `git add` 후 `git commit`까지 완료 (untracked·staged 잔여 0건)
- [ ] `pre-commit run --all-files` PASS
- [ ] `make check` (또는 양쪽 OS 별 `scripts/check.sh`/`.ps1`) PASS
- [ ] **SynologyDrive 동기화 완료까지 대기** — 트레이 아이콘 "최신 상태" 표시까지
- [ ] 작업 인계 메시지 (Slack/이메일/메모) 전달 — "어디까지 했고 무엇이 다음"

## 3. 작업 분담 권장 패턴

| 작업 종류 | 권장 담당 | 이유 |
|---|---|---|
| Frontend (Next.js) | 어느 쪽이든 | OS 차이 적음 |
| Backend (FastAPI/uv) | 어느 쪽이든 | uv가 양쪽 OS 지원 |
| DTP (OCC + STEP) | Docker 안에서 | OCC는 Windows native 설치 어려움 |
| n8n 워크플로우 편집 | 어느 쪽이든 | container 안 |
| Docker Compose 변경 | 한 사람이 끝까지 | docker compose down/up이 양쪽에서 일어나면 충돌 |
| `pyproject.toml` / `package.json` 변경 | 한 사람이 끝까지 + 즉시 동기화 알림 | lock 파일 충돌 시 양쪽 다 sync 다시 |
| 마이그레이션 (alembic) | 한 사람이 끝까지 | DB 스키마 양쪽 동시 변경 절대 불가 |

## 4. 동시 편집 충돌 발생 시

### 시나리오 A — git이 잡은 충돌

양쪽 commit이 모두 있는 상태에서 SynologyDrive 동기화 후 `git status`에 "you have unmerged paths" 나옴:

```bash
git status                    # 충돌 파일 확인
git diff <conflicted-file>    # 양쪽 변경 비교
# 직접 편집해서 충돌 마커(<<<<<<<, =======, >>>>>>>)) 정리
git add <conflicted-file>
git commit                    # 충돌 해결 commit
```

### 시나리오 B — SynologyDrive가 잡은 충돌

같은 파일이 양쪽에서 수정되고 git에 commit이 안 된 상태:

- SynologyDrive가 한쪽 사본을 `..._Conflict.<ext>` 이름으로 만듦
- 처리: `agents/cell-mes/data/_archive/` 같은 격리 디렉토리로 즉시 이동
- 양쪽 변경을 비교하여 채택할 버전 결정 → commit

### 시나리오 C — `.git/index.lock` 또는 `.git/objects/` 손상

- `.git/`이 SynologyDrive에서 제외되지 않은 상태 → 본 가이드 §3의 [SynologyDrive 제외 가이드](./COLLABORATION-SYNOLOGY-EXCLUDE.md) 즉시 적용
- 손상된 `.git/`은 다른 PC의 정상 `.git/` 으로 통째로 교체 (해당 PC에서 commit이 적은 쪽을 희생)
- 미커밋 작업물은 `git stash` 또는 `_archive/`에 백업 후 진행

## 5. "지금 누가 작업 중인가" 추적

별도 도구 없이 운영하는 경우:

- 작업 시작 시 `docs/CURRENT_OWNER.md` 파일에 자기 ID + 작업 영역 + 시작 시각 작성
- 작업 종료 시 해당 줄 삭제 또는 "(완료)" 추가
- 양쪽이 이 파일 보고 동시 진입 회피

샘플:
```
# 현재 작업 중

- xession (Windows) — [2026-05-02 14:00] cross-platform-collab-readiness 작업 중
- (작업 추가 시 여기에 한 줄)
```

## 6. 명령어 단일 인터페이스

`Makefile`로 양쪽 OS에서 동일한 명령:

| Make 타겟 | 동작 | 양쪽 OS |
|---|---|:-:|
| `make up` | docker compose up -d | ✅ |
| `make down` | docker compose down | ✅ |
| `make ps` | docker compose ps | ✅ |
| `make logs` | docker compose logs -f | ✅ |
| `make test` | 백엔드 pytest | ✅ |
| `make check` | ruff + tsc + pytest 통합 | ✅ |
| `make seed` | mes.db 시드 (양쪽 OS 별 분기) | ✅ |

Windows에서 `make` 미설치 시:
- WSL: 그대로 `make` 사용 가능
- 또는 `winget install GnuWin32.Make` / `choco install make`
- 또는 `scripts/check.ps1`, `scripts/seed-mes-db.ps1` 직접 실행

## 7. TZ (시간대)

- 둘 다 **Asia/Seoul (KST, UTC+9)** 가정
- log timestamp 비교 / commit 시각 / docker container TZ 모두 동일
- Windows TZ 확인: `Get-TimeZone`
- Mac TZ 확인: `date +%Z`

## 8. 환경변수

- `.env.example` ← 템플릿 (커밋됨)
- `.env.dev` ← 양쪽 PC가 같은 값 보유 (커밋 안 됨, SynologyDrive 동기화로 공유)
- `.env.prod` ← 운영 (커밋 안 됨)

비밀값(API key, 패스워드 등):
- `.env.dev` 파일 자체가 SynologyDrive 동기화 = NAS에 평문 저장 → **민감 시크릿은 1Password 등 외부 시크릿 매니저에 보관**
- `.env.dev`에는 dev 시크릿(placeholder 또는 dev 계정)만

## 9. 참고 문서

- [HANDOVER.md](./HANDOVER.md) — 신규 개발자 30분 온보딩
- [COLLABORATION-SYNOLOGY-EXCLUDE.md](./COLLABORATION-SYNOLOGY-EXCLUDE.md) — 동기화 제외 패턴
- [`docs/01-plan/features/cross-platform-collab-readiness.plan.md`](./01-plan/features/cross-platform-collab-readiness.plan.md) — 본 협업 인프라의 PDCA Plan
