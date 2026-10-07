# MES Equipment Status Skill

## Description
Queries equipment status, real-time monitoring data, and equipment availability from the MES system. Supports single equipment lookup and grid view of all equipment.

## Supported Intents
- `EQUIPMENT_STATUS`: 설비 상태, 모니터링, 가동/비가동 확인

## Required Entities
None (returns all equipment by default)

## Optional Entities
- `equipment_id`: Specific equipment ID (e.g., CNC-001, ROBOT-002)
- `equipment_type`: Equipment type filter (CNC, ROBOT, PLC, CONVEYOR)
- `status`: Equipment status filter (RUN, IDLE, ERROR, MAINTENANCE)
- `line_id`: Production line filter

## API Endpoints
```
Primary:
- GET /api/v1/masters/equipments
  params: equipment_type, line_id, is_active

- GET /api/v1/masters/equipments/{id}
  returns: Equipment details

- GET /api/v1/masters/equipments/{id}/status
  returns: Real-time status from middleware

Secondary:
- GET /api/v1/production/middleware/work-info
  params: equipment_id (for current work)
```

## Orchestration Pattern
```
Single Equipment:
1. GET /equipments/{id} (basic info)
2. Parallel:
   ├── GET /equipments/{id}/status (real-time)
   └── GET /middleware/work-info?equipment_id={id} (current job)

All Equipment Grid:
1. GET /equipments (list all)
2. Parallel for each:
   └── GET /equipments/{id}/status (optional, heavy)
```

## Output Types
- `status_grid`: Grid of equipment cards (default for multiple)
- `equipment_detail`: Single equipment detailed view
- `list`: Table with equipment status

## UI Schema Template (Grid View)
```json
{
  "layout": "grid",
  "columns": 4,
  "components": [
    {
      "type": "EquipmentStatusCard",
      "props": {
        "id": "{equipment_id}",
        "name": "{equipment_name}",
        "type": "{equipment_type}",
        "status": "RUN|IDLE|ERROR|MAINTENANCE",
        "metrics": {
          "spindle_rpm": 8500,
          "load_percent": 45,
          "temperature": 42
        },
        "currentJob": "{lot_no}",
        "lastUpdated": "2024-01-24T10:30:00"
      }
    }
  ]
}
```

## UI Schema Template (Single Equipment)
```json
{
  "layout": "single",
  "components": [
    {
      "type": "EquipmentDetailCard",
      "props": {
        "id": "{equipment_id}",
        "name": "{equipment_name}",
        "type": "{equipment_type}",
        "status": "RUN",
        "location": "{line_id}",
        "specs": {
          "manufacturer": "FANUC",
          "model": "RoboDrill α-D21MiA5"
        },
        "realtime": {
          "spindle_rpm": 8500,
          "feed_rate": 500,
          "load_percent": 45,
          "temperature": 42,
          "coolant_level": 85
        },
        "currentWork": {
          "lot_no": "LOT-001",
          "product": "PART-A",
          "operation": "OP020",
          "progress": 67
        },
        "lastUpdated": "2024-01-24T10:30:00"
      }
    },
    {
      "type": "LineChart",
      "props": {
        "title": "부하율 추이 (최근 1시간)",
        "data": "{load_history}",
        "xKey": "time",
        "yKey": "load_percent"
      }
    }
  ]
}
```

## Status Color Mapping
```json
{
  "RUN": "#22c55e",      // green - 가동중
  "IDLE": "#f59e0b",     // amber - 대기
  "ERROR": "#ef4444",    // red - 에러
  "MAINTENANCE": "#6b7280", // gray - 보수중
  "OFFLINE": "#374151"   // dark gray - 미연결
}
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "CNC-001 상태 어때?" | EQUIPMENT_STATUS | {equipment_id: CNC-001} | equipments/{id} + status |
| "설비 상태 조회" | EQUIPMENT_STATUS | {} | equipments (all) |
| "CNC 설비 목록" | EQUIPMENT_STATUS | {equipment_type: CNC} | equipments?type=CNC |
| "에러 상태인 설비" | EQUIPMENT_STATUS | {status: ERROR} | equipments (filter) |
| "1라인 설비 현황" | EQUIPMENT_STATUS | {line_id: LINE-1} | equipments?line_id=LINE-1 |

## Real-time Integration
For live updates, consider WebSocket subscription:
```json
{
  "action": "subscribe",
  "channel": "equipment_status",
  "equipment_ids": ["CNC-001", "CNC-002"]
}
```

## Error Handling
- **Equipment not found**: Return error with suggestions for similar IDs
- **Middleware offline**: Return cached status with warning "실시간 데이터 없음"
- **Partial failure**: Return available equipment, mark failed ones as "UNKNOWN"
