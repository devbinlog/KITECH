---
template: plan-plus
feature: cross-platform-collab-readiness
date: 2026-05-02
author: xession
project: agents-workspace
phase: plan
sync_model: B (SynologyDrive + 가드레일)
---

# cross-platform-collab-readiness — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | Mac 개발자(Jeongin Koo, mac mini)와 Windows 개발자(xession)가 SynologyDrive로 폴더를 공유하면서 git을 같이 쓰는 협업 환경이 구조적으로 불안정. `mes_Jeonginui-Macmini.local_..._Conflict.db` 충돌 잔여물이 이미 존재. VM/DP 외부 시스템 정보 부재로 다른 개발자에게 작업 위탁이 필요한 상황에서 환경 동질성/협업 룰/온보딩 자료가 미비. |
| **Solution** | 협업 모델 B(SynologyDrive 유지 + 가드레일) 채택. git remote는 도입하지 않고 폴더 동기화 + git history를 결합한 형태로 운영. 양쪽 OS에서 같은 결과를 내도록 가드레일(.gitignore 보강, .gitattributes, .python-version), 협업 룰(COLLABORATION.md/HANDOVER.md), 단일 인터페이스(Makefile + pre-commit), 환경 동질성(.vscode/.env.example/Docker 가이드) 19개 항목을 한 번에 적용. |
| **Function / UX / Effect** | • SynologyDrive 동기화 충돌 위험 최소화 (제외 패턴 가이드 + .gitignore 보강)<br>• 양쪽 OS 신규 개발자 30분 온보딩 (HANDOVER.md)<br>• `make up/down/test/check/seed` 단일 인터페이스 (양쪽 OS)<br>• `.python-version` 핀으로 uv 자동 동기화<br>• .vscode/{settings,extensions}.json 공유 — 인터프리터/포매터 자동<br>• pre-commit hook으로 빌드 산출물 실수 커밋 차단<br>• mes.db 시드 스크립트로 DB는 각자 로컬 재생성<br>• docker-compose.override.yml.example로 개인 환경 분리 |
| **Core Value** | **Mac+Windows 협업 환경의 구조적 위험을 제거하고, 새 개발자가 30분 안에 양쪽 OS에서 동일 결과로 합류할 수 있는 베이스라인 확보.** SynologyDrive를 그대로 두면서도 git 충돌·빌드 산출물 동기화·환경 차이 등 알려진 함정을 모두 가드레일로 막는다. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | 다른 개발자(Mac, VM/DP 정보 보유)에게 위탁하기 위한 협업 인프라 정비. Conflict.db 잔여물이 이미 발생. |
| **WHO** | xession(Windows, 작업 인계인) + Jeongin Koo or 후임 Mac 개발자(작업 위탁) |
| **RISK** | SynologyDrive에 .git/.venv/node_modules 동기화로 인한 손상, 양쪽 동시 작업 시 history 분기 불가, 빌드 산출물 중복 동기화 |
| **SUCCESS** | 19개 개선 항목 적용 + 양쪽 OS에서 `make up`/`make test`로 동일 결과 + 새 개발자가 30분 안에 셋업 |
| **SCOPE** | docs 5개 신규 + Makefile + pre-commit + .vscode 2개 + scripts seed 2개 + .python-version + override.yml.example + .gitignore/.gitattributes/.env.example/.env.dev/docker-compose.yml/README.md 보강. **Out of scope: GitHub/GitLab remote 도입, branch 전략, CI/CD** |

---

## 1. User Intent Discovery

### Q1. Core Purpose
선택: **위 3가지 모두 종합 평가** — 코드/데이터 손실 방지, 개발 환경 동질성, 인계/온보딩 효율을 모두 다룬다.

### Q2. Deliverable
선택: **리포트 + 전체 자동 수정** — 평가 보고서를 plan.md로 산출 + 19개 항목 모두 즉시 적용.

### Q3. Success Criteria (자동 도출)
- 모든 가드레일이 양쪽 OS에서 동작 (라인엔딩, 인터프리터 경로, 빌드 산출물 제외)
- Conflict.db 같은 잔여물 보존 + 격리 (삭제 금지)
- docker compose 가동 회귀 0건
- 새 개발자가 README 따라 30분 내 셋업 가능

## 2. Alternatives Explored

### Approach A — Git Remote 분리
- 산업 표준, 충돌 내성 최강
- GitHub/GitLab 계정 + repo 신설 필요, 폴더 이전 필요
- ❌ 비선택

### Approach B — SynologyDrive 유지 + 가드레일 ✅
- 현재 워크플로우 유지하면서 가장 위험한 함정만 막는다
- git의 분기/머지를 못 쓰지만 단방향(시간차) commit history는 유지
- ✅ **선택**

### Approach C — Hybrid
- 코드는 git remote, 대용량 데이터만 Synology
- symlink 관리 복잡도, OS별 차이
- ❌ 비선택

## 3. YAGNI Review

선택: **Critical 1-5 + High 6-11 + Medium 12-16 + Low 17-19 — 전부 포함**

### 3.1 Included (19개)

#### 🔴 Critical
1. `.gitignore` 강화 — `.bkit-memory.json`, `.omc/`, `.visual-check/`, 누락 항목 보강
2. Synology Drive 제외 가이드 문서 — `docs/COLLABORATION-SYNOLOGY-EXCLUDE.md`
3. mes.db 동기화 정책 — `_archive/` 이동 + seed 스크립트
4. `.gitattributes` 검증/보강 (이미 충실 — 대부분 통과)
5. 충돌 잔여 파일 정리 — `_archive/`로 격리

#### 🟡 High
6. README "협업" 섹션 추가
7. `docs/COLLABORATION.md` + `docs/HANDOVER.md` 신규
8. `.env.example` / `.env.dev` 5개 키(VM_*, DP_*) 추가
9. `Makefile` (양쪽 OS 단일 인터페이스)
10. `.pre-commit-config.yaml`
11. `.vscode/{settings,extensions}.json` 공유 (선택적 트래킹)

#### 🟢 Medium
12. `.python-version` (3.11 핀)
13. Docker Desktop OS별 가이드 (HANDOVER.md 안에)
14. agent-browser CLI 설치 가이드 (HANDOVER.md 안에)
15. `docker-compose.override.yml.example`
16. docker-compose.yml: VM/DP placeholder를 `${VAR:-default}` 패턴으로

#### 🔵 Low
17. `scripts/check.sh` + `scripts/check.ps1` — 커밋 전 통합 검증
18. `.bkit-memory.json` / `.omc/` / `.visual-check/` `.gitignore` 추가
19. TZ(Asia/Seoul) 문서 (HANDOVER.md 안에)

### 3.2 Out of Scope (배제)
- GitHub/GitLab remote 도입 (Approach B 비선택)
- Branch 전략 (단방향 commit history 가정)
- CI/CD 파이프라인 (remote 없음)
- Git LFS (대용량은 .gitignore + 시드)
- 자동 머지 도구
- VM/DP 실제 연동 (별도 작업, 본 plan에 포함 안 함)

## 4. Brainstorming Log

| 단계 | 핵심 결정 |
|---|---|
| Phase 0 | SynologyDrive 내부 작업 + Conflict.db 발견 → 협업 모델 결정이 가장 큰 의사결정점 |
| Phase 1-Q1 | 3축(데이터 안전+동질성+온보딩) 종합 평가 |
| Phase 1-Q2 | 리포트 + 전체 자동 수정 |
| Phase 2 | Approach B 선택 — 폴더 이전 비용 회피, 가드레일로 안전화 |
| Phase 3 | 19개 항목 모두 포함 |
| Phase 4 | 5단계 실행 흐름 + 위험 격리 매트릭스 승인 |

## 5. Architecture & Module Map

```
SynologyDrive (양방향 동기화)
├── .git/                   ← Synology Client에서 수동 제외 (가이드 문서 제공)
├── .venv/, node_modules/   ← Synology Client에서 수동 제외
├── 코드/문서/설정          ← 동기화됨
└── 단방향 협업 룰         ← COLLABORATION.md
```

### 5.1 신규 파일 (10)
- `docs/COLLABORATION.md`
- `docs/COLLABORATION-SYNOLOGY-EXCLUDE.md`
- `docs/HANDOVER.md`
- `Makefile`
- `.python-version`
- `.pre-commit-config.yaml`
- `.vscode/extensions.json`
- `docker-compose.override.yml.example`
- `scripts/seed-mes-db.sh` + `scripts/seed-mes-db.ps1`
- `scripts/check.sh` + `scripts/check.ps1`

### 5.2 수정 파일 (6)
- `.gitignore` (보강)
- `.env.example` (VM_*, DP_* 추가)
- `.env.dev` (동일 키 동기화)
- `docker-compose.yml` (placeholder → `${VAR:-default}`)
- `README.md` (협업 섹션)
- `.vscode/settings.json` (공유 + 기존 보존)

### 5.3 격리 (2)
- `agents/cell-mes/data/mes_..._Conflict.db` → `agents/cell-mes/data/_archive/`
- `agents/cell-mes/data/*.bak` → `agents/cell-mes/data/_archive/`

## 6. Implementation Order

```
1단계: 가드레일      (.gitignore / .python-version / 잔여 격리)
2단계: 환경 통합     (Makefile / .vscode / pre-commit / scripts/)
3단계: 환경변수      (.env.example / .env.dev / docker-compose.yml)
4단계: 협업 문서화   (COLLABORATION / HANDOVER / README)
5단계: override 템플릿 (docker-compose.override.yml.example)
6단계: 회귀 검증      (docker compose ps / config / git status)
```

## 7. Success Criteria (Plan Success Criteria)

| # | Criteria | 평가 방법 |
|---|---|---|
| 1 | `.gitignore` 보강 후 빌드 산출물 0건 추적 | `git ls-files \| grep -E "\.next/\|node_modules"` 0건 |
| 2 | `.gitattributes` 양쪽 OS 라인엔딩 정상 | `git check-attr eol -- file.ts` |
| 3 | `.python-version` 인식 | `uv python find` 결과 3.11 |
| 4 | Makefile 양쪽 OS 동작 | `make up` 양쪽 PC에서 docker compose up |
| 5 | pre-commit 양쪽 OS 동작 | `pre-commit run --all-files` PASS |
| 6 | .env.example/.env.dev/.env에 VM/DP 키 5개 | `grep -E "^(VM_\|DP_)"` 5건 |
| 7 | docker-compose.yml `${VAR:-default}` 적용 | `docker compose config` 정상 |
| 8 | docs/COLLABORATION.md 존재 + 핵심 룰 명시 | 파일 + "동시 편집 금지" 키워드 |
| 9 | docs/HANDOVER.md 30분 셋업 가이드 | 양쪽 OS 별 명령어 모두 포함 |
| 10 | docs/COLLABORATION-SYNOLOGY-EXCLUDE.md 존재 | 제외 패턴 리스트 명시 |
| 11 | _archive/ 디렉토리에 충돌 파일 격리 | `ls _archive/` 1건 이상 |
| 12 | README "협업" 섹션 추가 | grep "Mac.*Windows" |
| 13 | docker-compose.override.yml.example 템플릿 | 파일 존재 + .gitignore에 실제 .override는 제외 |
| 14 | scripts/seed-mes-db 양쪽 OS | `.sh` + `.ps1` 모두 존재 |
| 15 | scripts/check 양쪽 OS | `.sh` + `.ps1` 모두 존재 |
| 16 | 모든 docker compose 서비스 회귀 0 | `docker compose ps` 7/7 healthy 유지 |

## 8. Risk

| 위험 | 완화 |
|---|---|
| `.gitignore`로 인한 의도치 않은 untrack | 본 repo는 이미 빌드 산출물 0건 추적 중 (확인 완료) — 영향 없음 |
| Makefile Windows 미설치 | 부가 인터페이스로 두고 기존 .ps1 보존 |
| `${VAR:-default}` 패턴 변경으로 컨테이너 재시작 | 기본값 동일 → docker compose 무재시작 |
| pre-commit이 SynologyDrive 동기화 중 실행 | 충돌 가능성 있음 — 가이드에 명시 |
| _archive/ 디렉토리가 동기화됨 | 의도된 동작 (양쪽이 같은 백업 보유) |

## 9. Out of Scope (재확인)

- VM/DP 실 환경변수 연동 (사용자 권한 필요)
- MongoDB 서비스 추가 (별도 작업)
- NodeContextMenu / Disable 토글 (n8n editor M12 잔재)
- Frontend Playwright L2/L3 e2e (V2)
- 새 git remote 호스팅 (Approach A 비선택)

## 10. Next Step

```
/pdca design cross-platform-collab-readiness
```
또는 본 plan 승인 시 즉시 자동 수정 단계 진행 (사용자 선택: "전체 자동 수정")
