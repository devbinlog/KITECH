# Unit Scenario Hold Change Plan

> Date: 2026-06-22
> Target: `agents/cell-mes`
> Scope: Work order detail screen, unit queue state, unit-level logistics scenario override, middleware-ready payloads

## Summary

작업지시 상세 화면의 Unit Tracker에서 특정 `READY` 유닛을 선택해 물류 YAML 시나리오를 교체한다.

핵심 안전 요구사항은 시나리오를 바꾸는 동안 미들웨어가 해당 유닛을 레디큐에서 가져가지 못하게 하는 것이다. 이를 위해 유닛을 일시적으로 `SCENARIO_HOLD` 상태로 전환한다. `SCENARIO_HOLD` 유닛은 MES 화면에는 계속 보이지만, 미들웨어 레디큐 API에는 노출되지 않는다.

현재 코드에는 이미 `Unit.scenario_id`가 있고, `/orders/ready-units` 및 `/orders/ready-units/execution-package`가 `unit.scenario or order.scenario` 순서로 시나리오를 선택하도록 구성되어 있다. 따라서 DB 대공사보다는 유닛 상태 전이, 원자적 claim/hold 처리, 프론트 UI, 테스트를 보강하는 작업이다.

## Current Code Anchors

- Unit model: `agents/cell-mes/src/app/models/production.py`
  - `Unit.scenario_id` already exists.
  - `Unit.status` is a string column, so `SCENARIO_HOLD` can be added without a status enum migration.
- Unit producer: `agents/cell-mes/src/app/services/dispatch_service.py`
  - Currently creates a new `READY` unit when `READY` count is zero.
  - Must be changed to treat `SCENARIO_HOLD` as occupying the one-unit queue slot.
- Middleware ready queue: `agents/cell-mes/src/app/api/v1/endpoints/production.py`
  - `/orders/ready-units` currently filters only `Unit.status == "READY"`.
  - This should remain true so held units are hidden from middleware.
- Middleware execution package:
  - `/orders/ready-units/execution-package` already resolves `unit.scenario or order.scenario`.
- Unit list for UI:
  - `/orders/{order_id}/units` returns all units and should continue to include `SCENARIO_HOLD` units.
- Frontend detail screen:
  - `agents/cell-mes/frontend/app/(main)/production/orders/page.tsx`
  - Unit Tracker already displays unit scenario info and unit actions.

## Final Business Rules

### Unit Status Meaning

| Status | MES UI | Middleware ready queue | Dispatch slot | Meaning |
|---|---:|---:|---:|---|
| `READY` | visible | visible | occupied | Middleware may claim this unit. |
| `SCENARIO_HOLD` | visible | hidden | occupied | Operator is changing the unit scenario. Middleware must not claim it. |
| `RUNNING` | visible | hidden | not a ready slot | Middleware has claimed/executing the unit. |
| `PAUSED` | visible | hidden | existing behavior unchanged | Unit was physically paused. |
| `DONE` | visible | hidden | not a ready slot | Unit completed. |
| `ERROR` | visible | hidden | not a ready slot | Unit failed. |

### Required State Transitions

```text
READY
  -> RUNNING          middleware claim
  -> SCENARIO_HOLD    operator begins scenario change

SCENARIO_HOLD
  -> READY            scenario save succeeds
  -> READY            operator cancels/releases hold
  -> ERROR/CANCEL     admin recovery or work order cancellation policy
```

Disallowed transitions:

- `READY -> new scenario_id` without hold.
- `SCENARIO_HOLD -> RUNNING` by middleware.
- `RUNNING/DONE/ERROR/PAUSED -> SCENARIO_HOLD`.
- `SCENARIO_HOLD -> scenario save` if target scenario is inactive or not registered to the order product.

## Concurrency And Race Rules

### Rule 1: Hold Must Be Atomic

Holding a unit must be a single conditional database update:

```sql
UPDATE units
SET status = 'SCENARIO_HOLD',
    scenario_hold_started_at = :now,
    scenario_hold_by = :username
WHERE id = :unit_id
  AND work_order_id = :order_id
  AND status = 'READY'
```

If no row is updated, return `409 Conflict`. The unit was already claimed by middleware, held by another operator, or is not in a changeable state.

### Rule 2: Middleware Claim Must Be Atomic

All claim endpoints must use the same conditional update pattern:

```sql
UPDATE units
SET status = 'RUNNING',
    started_at = :now
WHERE id = :unit_id
  AND work_order_id = :order_id
  AND status = 'READY'
```

For claim by `(lot_no, unit_no)`, first resolve the pair to `unit_id`/`order_id`, then run the same conditional update. If no row is updated, return `409 Conflict` or the existing 400-equivalent response with a clear message.

This is the final defense when middleware has already read a stale `/ready-units` response before the operator clicks scenario change.

### Rule 3: Dispatch Must Count Hold As Queue Occupancy

`dispatch_service.py` must count both `READY` and `SCENARIO_HOLD` when deciding whether to create a new queued unit:

```python
Unit.status.in_(["READY", "SCENARIO_HOLD"])
```

Do not create a new unit while a held unit exists. The current MES architecture keeps exactly one queued unit per running work order. A held unit still occupies that queue slot.

### Rule 4: Ready Queue Must Expose READY Only

`/api/v1/production/orders/ready-units` must continue filtering `Unit.status == "READY"`. Do not include `SCENARIO_HOLD` in middleware-visible ready units.

### Rule 5: Scenario Save Requires Hold

Unit scenario update must only succeed from `SCENARIO_HOLD`:

```sql
UPDATE units
SET scenario_id = :scenario_id,
    status = 'READY',
    scenario_hold_started_at = NULL,
    scenario_hold_by = NULL
WHERE id = :unit_id
  AND work_order_id = :order_id
  AND status = 'SCENARIO_HOLD'
```

### Rule 6: Bulk Work Order Scenario Override Must Not Cross Held Units

Existing `PATCH /orders/{order_id}/scenario` changes the work order scenario and synchronizes all `READY` units. If any `SCENARIO_HOLD` unit exists for the order, return `409 Conflict`.

Reason: a unit-level scenario change and a work-order-level scenario override are competing writes. Blocking is safer and clearer than silently overwriting.

## Data Model Changes

`Unit.scenario_id` already exists and should remain the source of truth for unit-level scenario selection.

Recommended new nullable metadata fields:

| Field | Type | Purpose |
|---|---|---|
| `scenario_hold_started_at` | `DateTime(timezone=True), nullable=True` | Shows when hold started and supports stuck-hold recovery. |
| `scenario_hold_by` | `String(100), nullable=True` | Shows operator/user who started hold. Use username or user id text. |

These fields require an Alembic migration. They are not required for the middleware hiding mechanism, but they are important for operations when a browser closes or a network interruption occurs.

Do not add `hold_expires_at` in the first implementation unless operations explicitly wants automatic expiry. Automatic expiry can unexpectedly re-expose a unit while an operator is still choosing a scenario.

## API Contracts

### Hold Unit For Scenario Change

```http
POST /api/v1/production/orders/{order_id}/units/{unit_id}/scenario-hold
```

Response:

```json
{
  "message": "Unit held for scenario change",
  "unit_id": 10,
  "status": "SCENARIO_HOLD",
  "scenario_id": 3,
  "scenario_hold_started_at": "2026-06-22T10:15:00+09:00",
  "scenario_hold_by": "operator"
}
```

Validation:

- Work order exists.
- Unit exists and belongs to work order.
- Work order status should be `RUNNING` or `PAUSE`.
- Unit status must be `READY`.
- Conditional update must affect exactly one row.

Errors:

- `404`: work order or unit not found.
- `400`: unit does not belong to work order.
- `409`: unit is no longer READY or already held/claimed.

### Save Held Unit Scenario

```http
PATCH /api/v1/production/orders/{order_id}/units/{unit_id}/scenario
Content-Type: application/json
```

Request:

```json
{
  "scenario_id": 12
}
```

Response:

```json
{
  "message": "Unit scenario changed and released to ready queue",
  "unit_id": 10,
  "status": "READY",
  "scenario_id": 12
}
```

Validation:

- Unit must be `SCENARIO_HOLD`.
- Scenario must exist.
- Scenario must be active.
- Scenario must be registered to the same product as the work order:

```python
scenario.product_id == order.product_id
```

Do not allow `product_id IS NULL` common scenarios in this implementation. The user requirement is product-registered logistics scenario list.

### Release Held Unit Without Changing Scenario

```http
POST /api/v1/production/orders/{order_id}/units/{unit_id}/scenario-release
```

Response:

```json
{
  "message": "Unit scenario hold released",
  "unit_id": 10,
  "status": "READY",
  "scenario_id": 3
}
```

Validation:

- Unit must be `SCENARIO_HOLD`.
- Conditional update must affect exactly one row.

### Existing API Adjustments

#### `/orders/ready-units`

Keep as `READY` only. Held units must be invisible to middleware.

#### `/orders/ready-units/execution-package`

Keep using `unit.scenario or order.scenario`. Add regression tests to prove changed unit scenario is returned.

#### `/middleware/work-info`

Risk: current implementation accepts only `lot_no` and uses `order.scenario`, not `unit.scenario`.

Required decision before release:

- If middleware still calls `/middleware/work-info` to fetch scenario info, extend it with optional `unit_no` and prefer `unit.scenario or order.scenario`.
- If middleware has moved to `/ready-units` plus `/ready-units/execution-package`, document `/middleware/work-info` as work-order-level legacy payload and do not use it for unit override execution.

Do not release this feature until the actual middleware scenario-fetch path is confirmed and covered by a test.

## Frontend Plan

Target file:

- `agents/cell-mes/frontend/app/(main)/production/orders/page.tsx`

Service additions:

- `agents/cell-mes/frontend/services/production.ts`

Add:

```ts
holdUnitScenario(orderId: number, unitId: number)
updateUnitScenario(orderId: number, unitId: number, scenarioId: number)
releaseUnitScenarioHold(orderId: number, unitId: number)
```

### Unit Tracker UI

Show `SCENARIO_HOLD` rows in the existing Unit Tracker table.

Status label:

- `SCENARIO_HOLD`: `시나리오 변경 중`

Actions:

- `READY`: show `시나리오 변경`
- `SCENARIO_HOLD`: show `변경 계속`, `대기열 복귀`
- `RUNNING`, `PAUSED`, `DONE`, `ERROR`: no scenario change action

### Modal Flow

1. Operator clicks `시나리오 변경` on a READY unit.
2. Frontend calls `scenario-hold`.
3. On success, open scenario selection modal.
4. Modal loads `scenarioService.getAll(order.product_id, true)`.
5. Operator selects a scenario and saves.
6. Frontend calls unit scenario update.
7. On success, invalidate `["order-units", order.id]` and close modal.
8. If operator cancels, call `scenario-release` and invalidate `["order-units", order.id]`.

If network fails after hold:

- The held unit remains visible in Unit Tracker after refresh.
- User can click `변경 계속` or `대기열 복귀`.
- `scenario_hold_started_at` and `scenario_hold_by` should be displayed if available.

## Backend Task Breakdown

### Task B1: Add Hold Metadata Migration

Agent: backend

Scope:

- `agents/cell-mes/src/app/models/production.py`
- `agents/cell-mes/alembic/versions/`
- `agents/cell-mes/src/app/schemas/production.py`

Acceptance criteria:

- `Unit` includes `scenario_hold_started_at` and `scenario_hold_by`.
- `UnitRead` exposes both fields.
- Alembic upgrade/downgrade handles the new nullable fields.

### Task B2: Add Atomic Unit Scenario Hold APIs

Agent: backend

Scope:

- `agents/cell-mes/src/app/api/v1/endpoints/production.py`
- `agents/cell-mes/src/app/schemas/production.py`

Acceptance criteria:

- `POST /orders/{order_id}/units/{unit_id}/scenario-hold` works only from READY.
- `PATCH /orders/{order_id}/units/{unit_id}/scenario` works only from SCENARIO_HOLD.
- `POST /orders/{order_id}/units/{unit_id}/scenario-release` works only from SCENARIO_HOLD.
- Target scenario must be active and belong to the work order product.
- All state changes use conditional update semantics.

### Task B3: Make Middleware Claim Atomic

Agent: backend

Scope:

- `agents/cell-mes/src/app/api/v1/endpoints/production.py`

Acceptance criteria:

- Claim by `lot_no/unit_no` and claim by `order_id/unit_id` both conditionally update from READY to RUNNING.
- Claim fails if unit is SCENARIO_HOLD.
- Claim and hold race test passes deterministically.

### Task B4: Update Dispatch Slot Counting

Agent: backend

Scope:

- `agents/cell-mes/src/app/services/dispatch_service.py`

Acceptance criteria:

- Dispatch daemon counts `READY` and `SCENARIO_HOLD` as queued slot occupancy.
- No additional READY unit is generated while a SCENARIO_HOLD unit exists.
- Existing behavior for RUNNING/DONE target count remains unchanged.

### Task B5: Protect Work Order Scenario Override

Agent: backend

Scope:

- `agents/cell-mes/src/app/api/v1/endpoints/production.py`

Acceptance criteria:

- `PATCH /orders/{order_id}/scenario` returns 409 if any SCENARIO_HOLD unit exists for the order.
- Existing PAUSE-only rule remains intact unless explicitly changed later.

### Task B6: Verify Middleware Scenario Payload Path

Agent: backend

Scope:

- `agents/cell-mes/src/app/api/v1/endpoints/production.py`
- `agents/cell-mes/tests/test_api/test_production.py`

Acceptance criteria:

- `/orders/ready-units` returns the changed unit scenario after release.
- `/orders/ready-units/execution-package` returns the changed unit scenario after release.
- If `/middleware/work-info` is still used by middleware for scenario execution, add `unit_no` support and tests.

## Frontend Task Breakdown

### Task F1: Add Production Service Methods And Types

Agent: frontend

Scope:

- `agents/cell-mes/frontend/services/production.ts`
- `agents/cell-mes/frontend/types/index.ts`

Acceptance criteria:

- Frontend has typed methods for hold, update, release.
- Unit type includes `SCENARIO_HOLD`, `scenario_hold_started_at`, and `scenario_hold_by`.

### Task F2: Add Unit Scenario Change UI

Agent: frontend

Scope:

- `agents/cell-mes/frontend/app/(main)/production/orders/page.tsx`

Acceptance criteria:

- READY unit shows `시나리오 변경`.
- SCENARIO_HOLD unit shows `변경 계속` and `대기열 복귀`.
- Modal lists only active scenarios for the order product.
- Cancel releases hold.
- Save updates scenario and returns unit to READY.
- UI invalidates unit query after each operation.

### Task F3: Add Failure Handling

Agent: frontend

Scope:

- `agents/cell-mes/frontend/app/(main)/production/orders/page.tsx`

Acceptance criteria:

- Hold 409 shows a clear message: unit was already claimed or held.
- Save/release failures keep the modal state recoverable.
- Refresh after network interruption shows SCENARIO_HOLD unit with recovery actions.

## Test Plan

### Backend Tests

Add tests in `agents/cell-mes/tests/test_api/test_production.py`.

Required cases:

1. READY unit can be held.
2. RUNNING unit cannot be held.
3. SCENARIO_HOLD unit is not returned by `/orders/ready-units`.
4. SCENARIO_HOLD unit remains returned by `/orders/{order_id}/units`.
5. Held unit blocks dispatch daemon from creating a replacement READY unit.
6. Claim fails for SCENARIO_HOLD.
7. Hold fails after claim has already changed unit to RUNNING.
8. Scenario update fails unless unit is SCENARIO_HOLD.
9. Scenario update rejects inactive scenario.
10. Scenario update rejects scenario for a different product.
11. Scenario update succeeds and returns unit to READY.
12. Released READY unit appears in `/orders/ready-units` with new scenario.
13. `/orders/ready-units/execution-package` returns new scenario.
14. Work-order-level scenario override returns 409 while any unit is SCENARIO_HOLD.

### Frontend Tests

Add or update Vitest tests under `agents/cell-mes/frontend/__tests__/`.

Required cases:

1. READY unit renders scenario change action.
2. SCENARIO_HOLD unit renders continue/release actions.
3. Modal filters scenario list by product.
4. Cancel calls release API.
5. Save calls update API and invalidates unit query.
6. 409 response displays a user-readable conflict message.

## Risk Review

| Risk | Impact | Mitigation |
|---|---|---|
| Dispatch creates replacement unit while one is held | Middleware may execute the wrong unit | Count `SCENARIO_HOLD` as queue slot occupancy. |
| Middleware claims stale ready-unit response | Scenario can change after middleware saw old list | Claim must conditionally update `status == READY`; hold must do the same. |
| Browser/network interruption leaves held unit | Unit can remain hidden from middleware | Show held units in Unit Tracker; add release action and hold metadata. |
| Work-order-level and unit-level scenario changes conflict | Scenario overwritten unexpectedly | Block order-level scenario override while held units exist. |
| Middleware uses legacy work-info endpoint | Unit override not delivered | Confirm middleware path; add `unit_no` support if needed. |

## Implementation Order

1. Backend: add hold metadata fields and migration.
2. Backend: add unit scenario hold/update/release endpoints.
3. Backend: change claim endpoints to conditional updates.
4. Backend: change dispatch slot counting.
5. Backend: add/adjust tests for race and middleware payloads.
6. Frontend: add production service methods and unit types.
7. Frontend: add Unit Tracker actions and modal.
8. Frontend: add recovery UX for held units.
9. Run backend tests:

```bash
cd agents/cell-mes && uv run pytest tests/test_api/test_production.py -v
```

10. Run frontend typecheck/tests:

```bash
cd agents/cell-mes/frontend && npm run typecheck
npm run test:unit
```

## Release Checklist

- [ ] No SCENARIO_HOLD unit appears in middleware ready queue.
- [ ] SCENARIO_HOLD unit appears in MES Unit Tracker.
- [ ] Dispatch does not create a replacement READY unit while hold exists.
- [ ] Middleware claim cannot claim held units.
- [ ] Scenario save returns held unit to READY.
- [ ] Changed scenario is visible in ready-unit payload.
- [ ] Changed scenario is visible in execution-package payload.
- [ ] Work-order-level scenario override is blocked during unit hold.
- [ ] Operator can release a held unit after refresh/network interruption.
- [ ] Middleware scenario-fetch path is confirmed.

