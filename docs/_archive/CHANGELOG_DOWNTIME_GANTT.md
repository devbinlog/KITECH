# Changelog: Downtime Gantt Visualization Feature

## [2026-02-20] - Downtime Gantt Visualization Implemented

### Added

#### 1. Downtime Visualization in SchedulerGanttChart
- **File**: `frontend/src/components/scheduler/SchedulerGanttChart.tsx`
- Hatched pattern (45° red diagonal stripes) for downtime blocks
- Downtime-specific tooltip displaying equipment ID, time period, and reason
- Non-clickable downtime blocks (read-only visualization)
- "다운타임" (Downtime) legend entry in chart footer
- Separate footer counts for work tasks and downtime blocks

#### 2. useDowntimeForGantt Custom Hook
- **File**: `frontend/src/hooks/useScheduler.ts`
- Fetches downtimes for a given date from backend API
- Converts Downtime objects to ScheduledTaskForGantt format with `status="DOWNTIME"`
- Resolves reason names from reason IDs for display
- Handles error cases gracefully

#### 3. Downtime Integration in Scheduler Page
- **File**: `frontend/src/app/(main)/scheduler/page.tsx`
- Merges downtime tasks with work order schedule tasks
- Both datasets display together in same Gantt timeline
- Maintains existing scheduling and filtering logic

#### 4. Gantt Timeline Section in Downtime Page
- **File**: `frontend/src/app/(main)/downtime/page.tsx`
- New full-width timeline showing all equipment downtime
- Date picker for navigating to past/future downtime
- Shows all equipment (even those without scheduled downtime)
- Downtime-only view (no work order tasks)

### Technical Details

**Data Structure**:
Downtime objects converted to `ScheduledTaskForGantt` with:
- `status: "DOWNTIME"` (triggers special rendering)
- `reason`: Resolved reason name
- `quantity: null` (not displayed in tooltip)
- Timestamp fields: `startTime`, `endTime`

**Visual Styling**:
- Red hatched pattern (45° diagonal stripes)
- Non-interactive (no hover highlight, no click navigation)
- Distinct from work order blocks (green/blue)
- Compact tooltip (reason + time period)

**API Integration**:
- Endpoint: `GET /api/v1/downtime?date=YYYY-MM-DD`
- Returns: Array of Downtime objects with machine_id, start_time, end_time, reason_id
- Fetch strategy: Parallel to work order fetch (non-blocking)

### Bug Fixes (Previous Session)

1. **Equipment Status Mapping** (`scheduler_integration.py:180-190`)
   - Added `"RUN": "RUNNING"` and `"STOP": "AVAILABLE"` to status mapping
   - Equipment now shows correct status instead of "OFFLINE"

2. **Downtime → Scheduler occupied_slots** (`scheduler_integration.py:166-204`)
   - Added Downtime table query to `_get_occupied_slots()`
   - Scheduler now respects downtime windows when solving

3. **Progress Overflow Fix** (`production/orders/page.tsx:130-141`)
   - Changed progressMap from sum (`+=`) to `Math.max()`
   - Multi-step routing no longer inflates progress (e.g., 225/150 → 142/150)

### Testing

**Unit Tests**:
- Downtime data conversion (status assignment, reason resolution)
- Date filtering and API error handling
- Legend count calculation

**E2E Tests**:
- Downtime blocks render on scheduler page
- All equipment visible on downtime page
- Tooltip displays correctly on hover
- Non-interactive blocks (no navigation)
- Date picker navigation

**Manual Verification**:
- [x] Downtime displays with correct time range
- [x] Hatched pattern renders correctly
- [x] Tooltip shows reason, no quantity
- [x] Scheduler page integrates downtime seamlessly
- [x] Downtime page shows all equipment
- [x] Date navigation works

### Performance

- Downtime fetch is non-blocking (parallel to work order fetch)
- Array merge is O(n), negligible for typical dataset sizes
- SVG pattern rendering is hardware accelerated
- No additional database queries beyond new downtime API call

### Files Changed

**Modified**:
- `frontend/src/components/scheduler/SchedulerGanttChart.tsx` (+60 lines) - Downtime pattern, tooltip, legend
- `frontend/src/hooks/useScheduler.ts` (+40 lines) - New hook for downtime fetching
- `frontend/src/app/(main)/scheduler/page.tsx` (+5 lines) - Downtime merge
- `frontend/src/app/(main)/downtime/page.tsx` (+80 lines) - Gantt timeline section

### Backward Compatibility

- ✅ Fully backward compatible
- ✅ No database migrations required
- ✅ No API breaking changes
- ✅ Existing tests still pass
- ✅ Frontend-only deployment

### Related Issues

- Resolves: Downtime visibility gap in scheduler timeline
- Improves: Operator awareness of equipment unavailability windows
- Enables: Future downtime analytics and management features

### Next Steps

1. Monitor production for any rendering issues
2. Gather user feedback on downtime visualization
3. Consider downtime editing capability (future enhancement)
4. Explore downtime category color-coding (future enhancement)
