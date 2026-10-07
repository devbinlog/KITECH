# Production Management Enhancement Design

**Date**: 2026-02-17
**Status**: Approved

## Features

### 1. Work Order Detail Modal
- **File**: `app/(main)/production/orders/page.tsx`
- Click Eye icon on table row → opens detail modal
- Modal shows: WO attributes (lot_no, product, status, priority, equipment, due_date, remarks)
- Progress bar: ok_qty sum / target_qty
- Production results table for that WO (ok_qty, ng_qty, yield, time)
- Status transition buttons inside modal
- Data: `GET /production/results?work_order_id=N` on modal open

### 2. Progress Bar in Orders List
- **File**: `app/(main)/production/orders/page.tsx`
- New "진척" column in orders table
- After page load, fetch results for visible WO IDs → sum ok_qty per WO
- Progress bar: ok_qty_sum / target_qty, color-coded (green 95%+, blue 50-95%, gray <50%)
- DONE status shows checkmark instead of bar

### 3. WO Filter on Results Page
- **File**: `app/(main)/production/results/page.tsx`
- Add filter section with WO dropdown (lot_no display)
- Selection sets `ResultFilters.workOrderId` → API filters results
- "전체" option to reset

## Data Dependencies
- Progress bar requires separate API call: `GET /production/results?work_order_id=N` per WO
- Batch by fetching results for all visible WOs and computing client-side
- Detail modal fetches results on open (single API call)
