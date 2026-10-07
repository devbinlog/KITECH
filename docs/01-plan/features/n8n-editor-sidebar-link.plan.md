---
template: plan-plus
feature: n8n-editor-sidebar-link
date: 2026-05-02
author: xession
project: agents-workspace
phase: plan
---

# n8n-editor-sidebar-link — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | 시나리오 편집기는 frontend(`/master/scenarios/[id]/edit`)에 native React Flow로 통합되어 있지만, n8n 자체 editor(:5678)에는 frontend에서 접근 경로가 없음. credentials/webhook/execution history 등 native 편집기로 다루지 않는 작업 시 사용자가 직접 URL을 입력해야 함. |
| **Solution** | Sidebar 메뉴에 "n8n 에디터" 외부 링크 1개 추가 (Workflow 아이콘 + ExternalLink ↗ 인디케이터). `NEXT_PUBLIC_N8N_EDITOR_URL` 환경변수로 URL 주입. 새 탭에서 열림. |
| **Function / UX / Effect** | • Sidebar 분석리포트 그룹 다음, AI 어시스턴트 위에 단일 항목 노출<br>• Workflow 아이콘 + 라벨 "n8n 에디터" + 외부 링크 ↗ 아이콘<br>• `target="_blank"` `rel="noopener noreferrer"` — 보안 안전<br>• Tooltip "n8n 워크플로우 에디터 (외부 사이트, 새 탭)" — 의도 명확화<br>• `process.env.NEXT_PUBLIC_N8N_EDITOR_URL` 빌드타임 inject (기본 `http://localhost:5678`) |
| **Core Value** | **고급 사용자가 n8n editor의 모든 기능에 한 클릭으로 접근**. native scenario-editor가 다루지 못하는 영역(credentials, webhook, execution history, node 설치)을 frontend 떠나지 않고도 시작할 수 있게 함. UX는 "도구함의 외부 도구" 메타포. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | 시나리오 편집은 native, 그 외 n8n 기능은 직접 URL 입력 — 협업 후속 사이클에서 사용성 마찰 발생 |
| **WHO** | 시나리오 운영자 / admin / dev |
| **RISK** | 사용자가 외부 사이트로 나간다는 사실을 모르고 클릭 — tooltip + ExternalLink 아이콘으로 완화. n8n owner-account 가입 필요 시점에 혼란 가능 — Out of Scope |
| **SUCCESS** | Sidebar에 nav item 노출, 클릭 시 새 탭에서 NEXT_PUBLIC_N8N_EDITOR_URL 열림, frontend 컨테이너 재빌드 후 즉시 동작 |
| **SCOPE** | `Sidebar.tsx` 1개 + `docker-compose.yml` 1줄 + `.env` 1줄. **Out of scope: SSO, iframe 임베드, healthz ping, 안내 hint, feature flag** |

---

## 1. User Intent Discovery

### Q1. 통합 종류
선택: **frontend에서 n8n editor(:5678)로 링크 추가**
(다른 후보: 실제 n8n으로 Test Run 실행 / n8n 워크플로우 import / iframe 임베드 — 모두 미선택)

### Q2. 노출 위치
선택: **C: Top-nav menu** (Sidebar)
(A: 시나리오 목록만 / B: A + 편집기 툴바 / D: 안 만들고 주소 창에 주입 — 미선택)

### Q3. Scope (multiSelect)
선택: **Should 4-6: external icon / tooltip / Workflow icon (Recommended)**
(미선택: Nice 7 hint, Nice 8 feature flag, Nice 9 healthz ping)

## 2. Alternatives Explored

| 위치 후보 | 비교 결과 |
|---|---|
| α (분석리포트 후, AI 어시스턴트 위 — Recommended) | ✅ 단일 항목으로 위계 적절 |
| β (새 "도구" 그룹) | ❌ 단일 외부 링크에 그룹 만들 가치 없음 |

## 3. YAGNI Review

### 3.1 Included
- (1) MenuItem 신규 항목
- (2) `target="_blank"` + `rel="noopener noreferrer"`
- (3) `NEXT_PUBLIC_N8N_EDITOR_URL` 환경변수
- (4) ExternalLink ↗ 아이콘
- (5) Tooltip / aria-label
- (6) lucide-react Workflow 아이콘 (이미 import됨)

### 3.2 Out of Scope
- SSO between cell-mes ↔ n8n
- iframe 임베드
- 첫 방문 안내 hint
- Feature flag (NEXT_PUBLIC_SHOW_N8N_LINK)
- /healthz ping (클릭 전 상태 확인)
- n8n 워크플로우 리스트 미리보기

## 4. Architecture & Module Map

### 4.1 변경 파일 (3개)

| 파일 | 변경 |
|---|---|
| `agents/cell-mes/frontend/components/ui/Sidebar.tsx` | MenuItem 인터페이스 `external?: boolean` 추가, 외부 링크 렌더 분기, 신규 항목 추가 |
| `docker-compose.yml` | frontend service env에 `NEXT_PUBLIC_N8N_EDITOR_URL=${N8N_EDITOR_URL:-http://localhost:5678}` |
| `.env` | `N8N_EDITOR_URL=http://localhost:5678` (gitignore'd) |

### 4.2 데이터 흐름

```
1. Build time:
   .env (N8N_EDITOR_URL) → docker-compose.yml → frontend container env
   → next.js build inject (NEXT_PUBLIC_*) → bundle

2. Runtime:
   Sidebar.tsx → process.env.NEXT_PUBLIC_N8N_EDITOR_URL
              → fallback "http://localhost:5678"
              → <a href={URL} target="_blank">

3. User click:
   New tab → http://localhost:5678 (n8n editor)
   현재는 owner-account 가입 화면 (n8n 1.0+ user-management)
```

## 5. Implementation Order

```
1. Sidebar.tsx 수정      (UI)
2. docker-compose.yml    (env wiring)
3. .env                  (default value)
4. frontend rebuild      (docker compose build frontend)
5. 시각 검증             (브라우저 확인)
```

## 6. Success Criteria (Plan Success Criteria)

| # | Criteria | 평가 |
|---|---|---|
| 1 | Sidebar에 "n8n 에디터" 항목 가시성 | UI 확인 |
| 2 | 클릭 시 새 탭으로 열림 (target=_blank) | UI 확인 |
| 3 | Workflow + ExternalLink 아이콘 노출 | UI 확인 |
| 4 | Tooltip "n8n 워크플로우 에디터 (외부 사이트, 새 탭)" | hover 확인 |
| 5 | URL이 NEXT_PUBLIC_N8N_EDITOR_URL 환경변수에서 로드 | DevTools 확인 |
| 6 | rel="noopener noreferrer" 적용 | 보안 확인 |
| 7 | 기존 Sidebar 항목 회귀 0 | 클릭 테스트 |
| 8 | TypeScript 0 에러 | tsc --noEmit |

## 7. Risk

| 위험 | 완화 |
|---|---|
| frontend 재빌드 필요 | docker-compose.yml의 NEXT_PUBLIC_* 변경은 빌드타임 inject, 재빌드 필수 |
| 사용자가 외부로 나감 모름 | tooltip + ExternalLink 아이콘 |
| n8n owner-account 가입 화면 노출 | Out of scope (별도 사이클 또는 사용자 1회 셋업) |
| URL 환경변수 미설정 | fallback `http://localhost:5678` |

## 8. Out of Scope

- SSO / 인증 통합
- iframe 임베드
- n8n 워크플로우 import
- 첫 방문 안내
- Feature flag
- 클릭 전 healthz ping

## 9. Next Step

```
구현 → frontend rebuild → 시각 검증 → commit
```
