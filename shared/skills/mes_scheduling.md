# MES Scheduling Skill

## Description
Queries and manages production schedules, equipment availability, and scheduling requests. Integrates with the cell-scheduler agent for optimization.

## Supported Intents
- `SCHEDULE_QUERY`: 스케줄 조회, 일정 확인
- `ACTION_REQUEST`: 스케줄링 요청, 일정 생성

## Required Entities
None (defaults to current/upcoming schedule)

## Optional Entities
- `date`: Specific date
- `date_range`: Date range (today, this_week, next_week)
- `equipment_id`: Filter by equipment
- `equipment_ids`: Multiple equipment filter
- `product_id`: Filter by product
- `status`: Schedule status (SCHEDULED, RUNNING, COMPLETED)

## API Endpoints
```
Query:
- GET /api/v1/scheduler/equipment-availability
  params: date_range, equipment_ids
  returns: Equipment availability windows

- GET /api/v1/scheduler/schedule
  params: date, equipment_id
  returns: Current schedule

Action:
- POST /api/v1/scheduler/create-request
  body: { work_orders, constraints, options }
  returns: Scheduling request ID

- GET /api/v1/scheduler/request/{request_id}
  returns: Scheduling result

Secondary:
- GET /api/v1/production/orders?status=READY
  returns: Pending work orders for scheduling

- GET /api/v1/masters/equipments
  returns: Available equipment list
```

## Orchestration Pattern
```
Schedule View:
Parallel:
├── GET /scheduler/equipment-availability
├── GET /scheduler/schedule
└── GET /production/orders?date={date}

Scheduling Request:
1. GET /production/orders?status=READY (pending orders)
2. GET /masters/equipments?is_active=true
3. POST /scheduler/create-request
4. Poll GET /scheduler/request/{id} until complete
```

## Output Types
- `gantt`: Gantt chart view (default for schedule)
- `calendar`: Calendar view
- `list`: Table with schedule items
- `availability_grid`: Equipment availability heatmap

## UI Schema Template (Gantt View)
```json
{
  "layout": "single",
  "components": [
    {
      "type": "ScheduleHeader",
      "props": {
        "date_range": "2024-01-24 ~ 2024-01-26",
        "total_orders": 15,
        "scheduled": 12,
        "utilization": 78.5
      }
    },
    {
      "type": "GanttChart",
      "props": {
        "title": "생산 스케줄",
        "date_range": {
          "start": "2024-01-24T00:00:00",
          "end": "2024-01-26T23:59:59"
        },
        "resources": [
          {"id": "CNC-001", "name": "CNC 밀링 #1", "type": "CNC"},
          {"id": "CNC-002", "name": "CNC 밀링 #2", "type": "CNC"},
          {"id": "ROBOT-001", "name": "용접 로봇 #1", "type": "ROBOT"}
        ],
        "tasks": [
          {
            "id": "task-1",
            "resource_id": "CNC-001",
            "lot_no": "LOT-001",
            "product": "PART-A",
            "operation": "OP020",
            "start": "2024-01-24T08:00:00",
            "end": "2024-01-24T12:00:00",
            "status": "SCHEDULED",
            "color": "#3b82f6"
          }
        ],
        "unavailable": [
          {
            "resource_id": "CNC-002",
            "start": "2024-01-24T12:00:00",
            "end": "2024-01-24T13:00:00",
            "reason": "점심 휴식"
          }
        ]
      }
    },
    {
      "type": "DataTable",
      "props": {
        "title": "스케줄 목록",
        "columns": ["lot_no", "product", "equipment", "start", "end", "status"],
        "data": "{schedule_list}",
        "sortable": true,
        "filterable": true
      }
    }
  ]
}
```

## UI Schema Template (Availability)
```json
{
  "layout": "single",
  "components": [
    {
      "type": "AvailabilityHeatmap",
      "props": {
        "title": "설비 가용성",
        "date_range": "2024-01-24 ~ 2024-01-26",
        "equipment": [
          {
            "id": "CNC-001",
            "name": "CNC 밀링 #1",
            "availability": [
              {"hour": 8, "status": "available"},
              {"hour": 9, "status": "scheduled"},
              {"hour": 10, "status": "scheduled"},
              {"hour": 11, "status": "available"}
            ]
          }
        ],
        "legend": {
          "available": "#22c55e",
          "scheduled": "#3b82f6",
          "unavailable": "#ef4444",
          "maintenance": "#6b7280"
        }
      }
    }
  ]
}
```

## Scheduling Request Schema
```json
{
  "work_orders": [
    {
      "id": "WO-001",
      "lot_no": "LOT-001",
      "product_id": "PART-A",
      "quantity": 100,
      "due_date": "2024-01-26T18:00:00",
      "priority": 1
    }
  ],
  "constraints": {
    "equipment_ids": ["CNC-001", "CNC-002"],
    "start_after": "2024-01-24T08:00:00",
    "respect_due_dates": true,
    "minimize_changeover": true
  },
  "options": {
    "solver_timeout_seconds": 60,
    "optimization_target": "makespan"
  }
}
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "오늘 스케줄 보여줘" | SCHEDULE_QUERY | {date: today} | scheduler/schedule |
| "이번 주 생산 일정" | SCHEDULE_QUERY | {date_range: this_week} | scheduler/schedule |
| "CNC-001 스케줄" | SCHEDULE_QUERY | {equipment_id: CNC-001} | scheduler/schedule?equipment=CNC-001 |
| "설비 가용성 확인" | SCHEDULE_QUERY | {} | scheduler/equipment-availability |
| "대기 작업 스케줄링해줘" | ACTION_REQUEST | {} | create-request flow |

## Integration with Cell-Scheduler
```python
async def request_scheduling(work_orders: List[WorkOrder], constraints: Dict) -> ScheduleResult:
    # 1. Prepare request
    request_data = {
        "work_orders": [wo.to_scheduler_format() for wo in work_orders],
        "operations": get_operations_for_products([wo.product_id for wo in work_orders]),
        "machines": get_available_equipment(constraints.get("equipment_ids")),
        "constraints": {
            "max_horizon_days": 7,
            "consider_tool_changeover": constraints.get("minimize_changeover", True),
            "solver_time_limit_seconds": constraints.get("solver_timeout_seconds", 60)
        }
    }

    # 2. Call scheduler
    result = await scheduler_client.create_schedule(request_data)

    # 3. Convert to MES format
    return convert_scheduler_result(result)
```

## Error Handling
- **No pending orders**: Return message "스케줄링할 작업이 없습니다"
- **No feasible solution**: Return with suggestions (extend horizon, add equipment)
- **Scheduler timeout**: Return partial result with warning
- **Equipment unavailable**: Return error with available alternatives
