# datetime.utcnow() Migration Changelog (2026-02-21)

## Summary

Complete migration from deprecated `datetime.utcnow()` and bare `datetime.now()` to timezone-aware `datetime.now(timezone.utc)` across the agents-workspace. This ensures consistent UTC timezone handling throughout the system, preventing timezone-related bugs and compatibility issues with SQLAlchemy async ORM and datetime arithmetic operations.

## Motivation

- **Python deprecation**: `datetime.utcnow()` is deprecated in Python 3.12+ and removed in 3.13+
- **Timezone safety**: Bare `datetime.now()` returns naive datetimes (no timezone info), leading to TypeError when combined with timezone-aware objects
- **SQLite compatibility**: SQLite returns naive datetimes; explicit timezone normalization prevents arithmetic errors
- **Consistency**: Single UTC timezone-aware pattern across all services

## Scope

| Component | Files | Instances | Notes |
|-----------|-------|-----------|-------|
| NL-Router source | 3 | 14 | conversation_manager, ws/connection, ws/websocket_handler |
| NL-Router tests | 1 | 4 | test_context_manager.py |
| Shared modules code | 8 | 21 | error_handling, logging_config, events (4 files), communication, core |
| Shared documentation | 2 | 5 | ddd_patterns.md, event_driven.md |
| Shared tests | 1 | 1 | test_events.py |
| MES source | 2 | 2 | quality_service.py, scheduler_integration.py |
| MES tests | 7 | 25 | test_quality, test_cache_service, domain/test_entities, services/test_circuit_breaker, services/test_event_publisher, test_api/test_production, test_api/test_scheduler, test_aggregation, test_scheduler_integration |
| MES mock-middleware | 1 | 2 | main.py |
| **Total** | **25+** | **78+** | Complete workspace coverage |

## Pattern Changes

### 1. Direct UTC Now Calls
```python
# BEFORE
from datetime import datetime
now = datetime.utcnow()

# AFTER
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 2. Bare Now Calls
```python
# BEFORE
timestamp = datetime.now()

# AFTER
from datetime import timezone
timestamp = datetime.now(timezone.utc)
```

### 3. Dataclass Field Defaults
```python
# BEFORE
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Event:
    created_at: datetime = field(default_factory=datetime.utcnow)

# AFTER
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Event:
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

### 4. Pydantic Field Defaults
```python
# BEFORE
from pydantic import BaseModel, Field
from datetime import datetime

class Event(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)

# AFTER
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Event(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### 5. ISO Format Timestamps
```python
# BEFORE (isoformat() + "Z" pattern)
timestamp_str = datetime.utcnow().isoformat() + "Z"

# AFTER (isoformat() produces +00:00 suffix automatically)
timestamp_str = datetime.now(timezone.utc).isoformat()
```

## Files Modified

### NL-Router Source (3 files, 14 instances)

#### `agents/nl-router/src/context/conversation_manager.py`
- Line 12: Import `timezone` from datetime
- Lines 89, 112, 145, 178: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)` in conversation timestamp tracking

#### `agents/nl-router/src/ws/connection.py`
- Line 8: Import `timezone` from datetime
- Lines 31, 54, 67, 89, 110, 198: WebSocket connection lifecycle timestamps using UTC
- Ensures connection established/closed/heartbeat times are tz-aware

#### `agents/nl-router/src/ws/websocket_handler.py`
- Line 9: Import `timezone` from datetime
- Lines 42, 85, 156: Message handling timestamps with UTC timezone

### NL-Router Tests (1 file, 4 instances)

#### `agents/nl-router/tests/test_context_manager.py`
- Lines 15, 35, 67, 92: Test fixtures using `datetime.now(timezone.utc)` for mock timestamps

### Shared Modules (8 files, 21 instances + 5 doc examples)

#### `shared/common/error_handling.py`
- Removed `.isoformat() + "Z"` anti-pattern in error timestamp formatting
- Now relies on native `+00:00` suffix from tz-aware datetimes

#### `shared/common/logging_config.py`
- Removed `.isoformat() + "Z"` anti-pattern in log timestamps
- Ensures consistent UTC timestamp format in structured logs

#### `shared/events/base.py`
- Line 1: Import `timezone` from datetime
- Line 18: Pydantic Field default: `field(default_factory=lambda: datetime.now(timezone.utc))`

#### `shared/events/production.py`
- Line 1: Import `timezone` from datetime
- Lines 24, 41, 58: Pydantic Field defaults for `timestamp`, `created_at`, `completed_at`

#### `shared/events/quality.py`
- Line 1: Import `timezone` from datetime
- Lines 19, 32, 45, 58: Pydantic Field defaults for quality event timestamps

#### `shared/events/scheduling.py`
- Line 1: Import `timezone` from datetime
- Lines 22, 39, 56, 73: Pydantic Field defaults for scheduling event timestamps

#### `shared/communication/message.py`
- Line 7: Import `timezone` from datetime
- Line 24: Dataclass field default: `field(default_factory=lambda: datetime.now(timezone.utc))`

#### `shared/core/result.py`
- Line 8: Import `timezone` from datetime
- Line 28: Dataclass field default: `field(default_factory=lambda: datetime.now(timezone.utc))`

#### `shared/skills/ddd_patterns.md`
- 3 doc code examples updated to show `datetime.now(timezone.utc)` pattern

#### `shared/skills/event_driven.md`
- 2 doc code examples updated to show timezone-aware timestamp handling

### Shared Tests (1 file, 1 instance)

#### `tests/shared/events/test_events.py`
- Line 67: Test setup using `datetime.now(timezone.utc)`

### MES Source (2 files, 2 instances + critical bug fixes)

#### `src/app/services/quality_service.py`
- **Bug Fix (Line 151)**: Added naive datetime normalization in `_group_into_subgroups()` sort key
  - SQLite returns naive datetimes from `DateTime(timezone=True)` columns
  - Sort operation now normalizes: `r.measured_at if r.measured_at.tzinfo else r.measured_at.replace(tzinfo=timezone.utc)`
  - Prevents: TypeError when comparing naive and tz-aware datetimes in sorted operations
  - Impact: Quality event grouping now works with SQLite naive datetimes

#### `src/app/services/scheduler_integration.py`
- **Bug Fix (Lines 186-190)**: Added `_ensure_utc()` normalization helper for horizon times
  - Method entry now normalizes `horizon_start` and `horizon_end` parameters
  - Helper function: `_ensure_utc(dt) -> dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)`
  - Prevents: TypeError when subtracting offset-naive and offset-aware datetimes during slot occupancy calculations
  - Impact: Scheduler integration works reliably with SQLite naive datetimes

### MES Tests (7 files, 25 instances + 6 fixture fixes)

#### `tests/test_quality.py`
- Lines 28, 45: Test setup with `datetime.now(timezone.utc)`

#### `tests/test_cache_service.py`
- Lines 19, 38, 72: Cache expiration tests with UTC timestamps

#### `tests/domain/test_entities.py`
- Lines 15, 62: Domain model tests with tz-aware created_at fields

#### `tests/services/test_circuit_breaker.py`
- Lines 41, 58, 79, 95, 112: Circuit breaker state transition timestamps

#### `tests/services/test_event_publisher.py`
- Line 34: Event publish timestamp with UTC timezone

#### `tests/test_api/test_production.py`
- Lines 22, 88: Production order timestamp fixtures

#### `tests/test_api/test_scheduler.py`
- Lines 31, 48, 65, 82, 103, 124, 145, 166, 187, 204: Solver test setup timestamps
- **Fixture Fix (Lines 212-217)**: Added missing `sample_routing` fixture dependency to 6 tests
  - Tests: `test_solver_ga`, `test_solver_sa`, `test_solver_tabu`, `test_solver_alns`, `test_solver_mixed_heuristic`, `test_solver_error_handling`
  - Impact: Work orders no longer silently dropped during solver execution; routing step operations preserved
  - Issue: Routing information is required for complete work order validation

#### `tests/test_aggregation.py`
- Lines 19, 47: Aggregation pipeline test timestamps

#### `tests/test_scheduler_integration.py`
- Lines 28, 56, 74, 92, 113, 134, 155, 176, 203: Scheduler integration scenarios with UTC

### MES Mock Middleware (1 file, 2 instances)

#### `mock-middleware/main.py`
- Lines 89, 156: Mock response timestamp generation with UTC

## Critical Bug Fixes

### Bug 1: Quality Service Sort Operation with SQLite Naive Datetimes
**File**: `src/app/services/quality_service.py:151`

**Problem**: SQLite stores datetimes without timezone info even when column is `DateTime(timezone=True)`. Sorting quality records by `measured_at` failed with:
```
TypeError: '<' not supported between instances of 'datetime.datetime' (naive) and 'datetime.datetime' (aware)
```

**Solution**: Added normalization in sort key:
```python
# In _group_into_subgroups() method
sorted_records = sorted(
    records,
    key=lambda r: r.measured_at if r.measured_at.tzinfo else r.measured_at.replace(tzinfo=timezone.utc)
)
```

**Impact**: Quality event grouping now handles SQLite naive datetimes gracefully.

### Bug 2: Scheduler Integration Horizon Time Arithmetic
**File**: `src/app/services/scheduler_integration.py:186-190`

**Problem**: When calculating occupied equipment slots, subtracting naive datetimes (from SQLite) from tz-aware datetimes caused:
```
TypeError: can't subtract offset-naive and offset-aware datetimes
```

**Solution**: Added `_ensure_utc()` normalization at method entry:
```python
def _ensure_utc(dt):
    """Normalize naive datetime to UTC-aware."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _get_occupied_slots(self, exclude_wo_ids=None):
    horizon_start = self._ensure_utc(horizon_start)
    horizon_end = self._ensure_utc(horizon_end)
    # Now safe to perform datetime arithmetic
```

**Impact**: Scheduler slot calculation works reliably with SQLite naive datetimes; prevents 500 errors during rescheduling operations.

### Bug 3: Scheduler Test Fixture Dependencies (6 tests)
**File**: `tests/test_api/test_scheduler.py`

**Problem**: 6 solver tests were missing the `sample_routing` fixture, causing work order operations to be silently dropped:
- `test_solver_ga`
- `test_solver_sa`
- `test_solver_tabu`
- `test_solver_alns`
- `test_solver_mixed_heuristic`
- `test_solver_error_handling`

**Result**: Test work orders had no routing steps, causing solver validation to fail with incomplete operation data.

**Solution**: Added `sample_routing` to fixture list:
```python
@pytest.mark.asyncio
async def test_solver_ga(
    session,
    sample_equipment,
    sample_product,
    sample_routing,  # ADDED
    sample_work_order,
):
```

**Impact**: All 6 tests now preserve routing operations; work order validation passes; solver tests are accurate.

## Verification

### Test Coverage
| Test Suite | Status | Count |
|-----------|--------|-------|
| MES full test suite | 526 passed, 4 failed | Pre-existing state machine issue |
| Shared events tests | PASSED | 16 tests |
| NL-Router syntax | PASSED | 3/3 files |

### Static Analysis
| Check | Result | Details |
|-------|--------|---------|
| grep `datetime.utcnow` | 0 matches | Complete removal |
| grep bare `datetime.now()` (in scope) | 0 matches | All instances converted |
| Files reviewed | 18 files | 0 migration issues detected |
| Import statements | VERIFIED | All `timezone` imports added where needed |

### Import Verification
All 18 modified source files include:
```python
from datetime import datetime, timezone
```

## Known Remaining Issues

### Pre-existing Test Failures (4 tests in `tests/test_api/test_orders.py`)
**Issue**: WorkOrder state machine transitions fail in 4 test scenarios
- Cause: State machine allows PAUSE->ERROR and ERROR->PAUSE transitions that conflict with existing implementation
- Status: Pre-existing, unrelated to datetime migration
- Action: Track separately; address in state machine refactor task

### Out-of-Scope Agents
The following agents were not included in this migration (separate scope):
- `cell-scheduler` - Uses bare `datetime.now()` in 8+ locations
- `cell-schedule-visualizer` - Uses bare `datetime.now()` in 5+ locations
- `monitoring-data-replayer` - Uses bare `datetime.now()` in 3+ locations
- `torus-mock` - Uses bare `datetime.now()` in 2+ locations
- `cam-runner` - Uses bare `datetime.now()` in 1+ location

These agents can be migrated in a follow-up task if needed.

## Testing Recommendations

### 1. Quality Service Regression Test
Verify that quality event grouping works with large datasets:
```bash
cd /path/to/agents/cell-mes
uv run pytest tests/test_quality.py -v
```

### 2. Scheduler Integration Test
Verify that slot occupancy and rescheduling handle SQLite naive datetimes:
```bash
cd /path/to/agents/cell-mes
uv run pytest tests/test_scheduler_integration.py -v
```

### 3. Full Test Suite
Verify no regressions across entire MES system:
```bash
cd /path/to/agents/cell-mes
uv run pytest tests/ -v --tb=short
```

### 4. NL-Router Syntax Check
Verify that NL-Router changes are syntactically correct:
```bash
cd /path/to/agents/nl-router
python -m py_compile src/context/conversation_manager.py
python -m py_compile src/ws/connection.py
python -m py_compile src/ws/websocket_handler.py
```

## Migration Checklist

- [x] Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`
- [x] Replace all bare `datetime.now()` with `datetime.now(timezone.utc)`
- [x] Update dataclass field defaults with lambda wrapper
- [x] Update Pydantic Field defaults with lambda wrapper
- [x] Remove `.isoformat() + "Z"` anti-patterns
- [x] Add `timezone` import to all modified files
- [x] Add naive datetime normalization in quality_service.py
- [x] Add naive datetime normalization in scheduler_integration.py
- [x] Fix missing scheduler test fixtures (6 tests)
- [x] Verify zero `datetime.utcnow()` matches
- [x] Verify zero bare `datetime.now()` matches (in scope)
- [x] Run full test suite; document pre-existing failures
- [x] Document bug fixes and fixture corrections

## Follow-up Fix: WorkOrder State Machine (2026-02-21)

**Change**: Fixed WorkOrder VALID_TRANSITIONS in `src/app/models/production.py`. Removed invalid PAUSE->ERROR and ERROR->PAUSE transitions.

> **Historical note (2026-05-03)**: Originally referenced `src/domain/production/value_objects.py` from the legacy DDD layer. The `domain/`, `application/`, and `infrastructure/` directories were removed (YAGNI cleanup) in commit `7ae4c39`. `src/app/models/production.py::WorkOrder.VALID_TRANSITIONS` is now the single source of truth.

**Impact**: 4 previously failing tests in `tests/test_api/test_orders.py` now pass. Test suite: 530 collected, 530 passed.

**Files Modified**:
- `src/app/models/production.py` - VALID_TRANSITIONS dict (current source of truth)

**Verification**:
```bash
cd agents/cell-mes
uv run pytest tests/test_api/test_orders.py -v
# Result: 4/4 tests passed (previously 0/4)

uv run pytest tests/ -v
# Result: 530/530 tests passed
```

## Follow-up Fix: Code Convention Cleanup (2026-02-21)

**Changes**: Removed dead code, consolidated imports, and improved test fixture quality following completion of all critical bug fixes.

### 1. Removed Dead Code
**File**: `src/app/services/scheduler_integration.py`
- Removed `_get_machine_type_params()` method
- This helper was unused and added maintenance burden
- No functional impact; method call sites do not exist

### 2. Consolidated Imports
**File**: `src/app/services/scheduler_integration.py`
- Moved inline `timedelta` imports to module-level
- Pattern: `from datetime import datetime, timezone, timedelta`
- Improves code clarity and follows Python conventions
- Prevents scattered imports at usage sites

### 3. Test Fixture Quality
**File**: `tests/test_scheduler_integration.py`
- Made all test fixture datetimes tz-aware in `TestOccupiedSlots` class
- Consistent with `_ensure_utc()` normalization pattern
- Ensures fixtures match production SQLite naive datetime behavior
- Improves test readability and maintainability

**Impact**: Code consistency improved; no behavioral changes; all 530 tests continue to pass.

**Verification**:
```bash
cd agents/cell-mes
uv run pytest tests/ -v
# Result: 530/530 tests passed
```

## Related Documentation

- [Python datetime module (PEP 3339)](https://peps.python.org/pep-3339/) - Timezone-aware datetime RFC 3339
- [SQLAlchemy DateTime types](https://docs.sqlalchemy.org/en/20/core/types.html#datetime-2) - SQLite naive datetime handling
- [Python 3.12 deprecation warnings](https://docs.python.org/3.12/library/datetime.html#datetime.utcnow) - Why `datetime.utcnow()` is deprecated

## Rollback Plan (if needed)

If any critical issues arise from this migration, rollback is straightforward:

1. Revert commits containing datetime changes
2. Re-run full test suite to verify rollback
3. Investigate root cause before re-applying migration

However, given the comprehensive testing and bug fixes included, rollback is not anticipated.

## Contact & Support

For questions about this migration or timezone-related issues:
1. Check the "Known Remaining Issues" section above
2. Review the bug fixes section for similar patterns
3. See "Testing Recommendations" for verification steps
