---
template: plan-plus
feature: test-coverage-improvement
date: 2026-05-03
author: xession
project: agents-workspace
phase: plan
---

# test-coverage-improvement — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | 직전 audit reviewer D 보고서: shared/common 0 tests / test_internal_service_key_access 실패 (pre-commit hook -x로 cell-mes commit 차단) / asyncio.sleep flaky 5+ files / CI 부재. `src.api.core` 같은 import 에러가 가동 후에야 발견됨. |
| **Solution** | 4 sub-agent 병렬: ① shared/common (service_base + tracing) 단위 테스트, ② test_internal_service_key_access 헤더 mismatch fix, ③ asyncio.sleep flaky → freezegun/event-based 교체, ④ .github/workflows/test.yml 작성 (push/PR 시 14 service 자동 회귀). |
| **Function / UX / Effect** | • shared/common ~30-40 tests (require_internal/create_app/error_envelope/TraceIdMiddleware)<br>• 헤더 이름 통일 → pre-commit hook 정상 작동<br>• flaky asyncio.sleep 5+ 파일 → 결정론적 sync 패턴<br>• GitHub Actions: 14 service pytest matrix + frontend tsc + vitest |
| **Core Value** | **신규 코드가 실제 회귀 안전망에 들어옴.** 현재는 commit 후 docker compose up으로 발견되는 import 에러가, 이후엔 PR/pre-commit 시점에 차단. shared/common이 토대인데 검증 없이 14 service에 영향 줬던 위험 차단. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | 신규 코드 (직전 5 사이클) 회귀 보호 부재 → src.api.core 같은 import 에러 가동 시 발견 |
| **WHO** | xession (commit 시) + Mac dev (인계 후) + 향후 PR 보호 |
| **RISK** | shared/common 변경이 14 service에 영향 — 자체 테스트 없이는 회귀 발생 시 14 service 모두 깨짐 |
| **SUCCESS** | shared/common 30+ tests / test_auth 통과 / flaky 0건 / .github/workflows pytest 자동 실행 |
| **SCOPE** | shared/common/tests/ + test_auth.py 수정 + 5 flaky 파일 + .github/workflows. **OOS: scenario-editor frontend tests 추가, e2e 신규, 다른 audit findings** |

---

## 1. User Intent Discovery

### Q1
선택: **4개 모두** (shared/common + test_auth fix + flaky + CI)

## 2. Approach
Single approach: 4 sub-agent 병렬 (file ownership 격리).
Alternative B (단일 sub-agent 순차)는 timeout 위험.

## 3. YAGNI
포함:
- 위 4개 항목

OOS:
- scenario-editor 컴포넌트별 vitest (다음 사이클)
- e2e Playwright 신규 (다음 사이클)
- coverage 리포팅 / pytest-cov badge
- 의존성 audit (pip-audit, npm audit) — 다음 사이클

## 4. Architecture & Module Map

### 신규 파일
- `shared/common/tests/__init__.py`
- `shared/common/tests/conftest.py`
- `shared/common/tests/test_service_base.py`
- `shared/common/tests/test_tracing.py`
- `.github/workflows/test.yml`

### 수정 파일
- `agents/cell-mes/tests/test_api/test_auth.py` (헤더 이름 mismatch fix)
- `agents/cell-mes/tests/services/test_event_publisher.py` (asyncio.sleep → event-based)
- `agents/cell-scheduler/tests/test_event_publisher.py` (동일)
- `agents/cell-mes/tests/test_api/test_scenario_test_runs.py` (polling → wait_for)
- `agents/torus-mock/tests/test_data_simulator.py` (mock clock)
- `agents/nl-router/tests/test_rate_limiting.py` (freezegun)

## 5. Implementation Order

```
1. Sub-agent A: shared/common 테스트 (병렬)
2. Sub-agent B: test_auth fix (병렬)
3. Sub-agent C: 5 flaky 파일 정리 (병렬)
4. Sub-agent D: .github/workflows/test.yml (병렬)
5. Main: 회귀 + commit
```

## 6. Success Criteria

| # | Criteria |
|---|---|
| 1 | shared/common/tests/ 30+ tests pass |
| 2 | test_internal_service_key_access pass |
| 3 | pre-commit hook 정상 작동 (-x로 안 막힘) |
| 4 | flaky 5+ 파일 asyncio.sleep 제거 |
| 5 | .github/workflows/test.yml 작성 (실행은 PR 시) |
| 6 | 14 service 회귀 0 |

## 7. Out of Scope (재확인)
- scenario-editor 잔여 컴포넌트 vitest
- Playwright e2e 신규
- coverage badge
- 의존성 audit
