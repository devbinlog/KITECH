# MES Producer-Consumer Architecture Task Checklist

## 1. Database Schema Changes
- [x] Create `Unit` table model in `production.py`.
- [x] Add `current_scenario_id` and relationship to `WorkOrder` model.
- [x] Add `unit_id` Foreign Key to `ProdResult` model.
- [x] Update Pydantic schemas in `schemas/production.py`.
- [x] Generate and run Alembic migration script.

## 2. API Endpoints (Middleware Consumer API & Override)
- [x] Create `GET /orders/{lot_no}/units/ready` endpoint (Retrieve items from queue).
- [x] Create `POST /orders/units/{unit_id}/claim` endpoint (State `READY` -> `RUNNING`).
- [x] Create `POST /orders/units/{unit_id}/complete` endpoint (State -> `DONE`).
- [x] Create `PATCH /orders/{order_id}/scenario` endpoint (Dynamic Override).

## 3. Producer Daemon
- [x] Implement `dispatch_service.py` core loop to maintain exactly 1 `READY` unit per `RUNNING` WorkOrder.
- [x] Register the daemon in the application lifecycle (`main.py` or startup event).
- [x] Disable/Remove old Push logic if it exists.

## 4. Frontend UI/UX Evolution
- [x] Create `ChangeScenarioModal` component.
- [x] Add "Scenario Override" action to the row/detail view for `PAUSE` status orders.
- [x] Design and embed the `Unit Queue Monitor` inside `OrderDetailModal`.
- [x] Fetch and map unit data to the unit queue table.

## 5. Global Queue & DDD Refactoring (Phase 2)
- [x] **Refactor Backend APIs:**
  - Update `GET /units/ready` to `GET /orders/ready-units`.
  - Add `{order_id}` path parameter to `/claim` and `/complete` endpoints with cross-validation.
  - Delete physical `stop`/`resume` HTTP calls from `update_work_order_status` (Logical Pause implementation).
  - Explicitly load `scenario` relation in `get_units_for_order` for frontend UI rendering.
- [x] **Refactor Frontend Services:**
  - Update `claimUnit` and `completeUnit` function signatures in `production.ts` to include `orderId` (Note: Skipped because these act as middleware endpoints only).
- [x] **Update Frontend UI/UX:**
  - Rename `OrderDetailModal` queue section to "단위 생산 현황 (Unit Tracker) (Lot-Size 1)".
  - Add "시나리오 (YAML)" column to the Unit table to show the dynamically changing assignments.

## 6. Physical Unit Control (Phase 3)
- [x] **Backend Implementation:**
  - Add `POST /orders/{order_id}/units/{unit_id}/stop` endpoint with `httpx` proxy sync validation.
  - Add `POST /orders/{order_id}/units/{unit_id}/resume` endpoint with proxy validation.
- [x] **Frontend Implementation:**
  - Add `stopUnit` API call to `production.ts`.
  - Add Action Column to Unit Tracker table.
  - Render "정지(Pause)" and "재시작(Resume)" buttons dynamically based on Unit state (`RUNNING`/`PAUSED`).
