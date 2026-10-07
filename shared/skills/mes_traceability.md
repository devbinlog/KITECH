# MES Traceability Skill

## Description
Provides complete traceability for LOT numbers including production history, equipment used, quality data, and process routing. Supports forward and backward tracing.

## Supported Intents
- `TRACEABILITY`: LOT 추적, 이력 조회, 생산 이력
- `PRODUCTION_STATUS`: LOT 기반 생산 현황

## Required Entities
- `lot_no`: LOT number (e.g., LOT-001, LOT_2024_001)

## Optional Entities
- `trace_direction`: forward (downstream) or backward (upstream)
- `include_quality`: Include quality/inspection data (default: true)
- `include_materials`: Include input materials/components

## API Endpoints
```
Primary:
- GET /api/v1/production/traceability/{lot_no}
  returns: Complete traceability record

Secondary (for assembly):
- GET /api/v1/production/orders?lot_no={lot_no}
  returns: Work order details

- GET /api/v1/production/results?work_order_id={id}
  returns: Production results per operation

- GET /api/v1/production/middleware/work-info?lot_no={lot_no}
  returns: Routing and scenario info

- GET /api/v1/masters/equipments/{id}
  returns: Equipment details
```

## Orchestration Pattern
```
Full Traceability:
1. GET /orders?lot_no={lot_no}
   → Extract work_order_id

2. Parallel:
   ├── GET /results?work_order_id={id}
   ├── GET /middleware/work-info?lot_no={lot_no}
   └── GET /masters/products/{product_id}

3. For each result.equipment_id:
   └── GET /masters/equipments/{equipment_id}

4. Aggregate into timeline
```

## Output Types
- `timeline`: Visual timeline of production steps (default)
- `table`: Detailed table with all records
- `tree`: Hierarchical view (for assembly products)

## UI Schema Template (Timeline)
```json
{
  "layout": "single",
  "components": [
    {
      "type": "TraceabilityHeader",
      "props": {
        "lot_no": "LOT-001",
        "product": "PART-A",
        "product_name": "알루미늄 브라켓",
        "status": "DONE",
        "start_time": "2024-01-24T08:00:00",
        "end_time": "2024-01-24T14:30:00",
        "total_qty": 100,
        "ok_qty": 98,
        "ng_qty": 2,
        "yield": 98.0
      }
    },
    {
      "type": "TraceabilityTimeline",
      "props": {
        "title": "생산 이력",
        "steps": [
          {
            "operation": "OP010",
            "operation_name": "소재 투입",
            "equipment_id": "LOADER-01",
            "equipment_name": "자동 로더",
            "start_time": "2024-01-24T08:00:00",
            "end_time": "2024-01-24T08:15:00",
            "status": "DONE",
            "operator": "홍길동",
            "ok_qty": 100,
            "ng_qty": 0
          },
          {
            "operation": "OP020",
            "operation_name": "1차 가공",
            "equipment_id": "CNC-001",
            "equipment_name": "CNC 밀링 #1",
            "start_time": "2024-01-24T08:20:00",
            "end_time": "2024-01-24T10:45:00",
            "status": "DONE",
            "operator": "김철수",
            "ok_qty": 99,
            "ng_qty": 1,
            "parameters": {
              "spindle_rpm": 8500,
              "feed_rate": 500
            }
          },
          {
            "operation": "OP030",
            "operation_name": "검사",
            "equipment_id": "CMM-001",
            "equipment_name": "3차원 측정기",
            "start_time": "2024-01-24T11:00:00",
            "end_time": "2024-01-24T12:00:00",
            "status": "DONE",
            "inspector": "이영희",
            "ok_qty": 98,
            "ng_qty": 1,
            "quality_data": {
              "dimension_check": "PASS",
              "surface_roughness": 1.2
            }
          }
        ]
      }
    },
    {
      "type": "DataTable",
      "props": {
        "title": "상세 이력",
        "columns": ["operation", "equipment", "start", "end", "ok_qty", "ng_qty", "operator"],
        "data": "{detailed_records}",
        "exportable": true
      }
    }
  ]
}
```

## Data Structure
```python
@dataclass
class TraceabilityRecord:
    lot_no: str
    product_id: str
    product_name: str
    work_order_id: str

    # Overall summary
    status: str  # READY, RUNNING, DONE
    total_qty: int
    ok_qty: int
    ng_qty: int
    yield_rate: float

    # Timeline
    start_time: datetime
    end_time: Optional[datetime]

    # Steps
    steps: List[TraceabilityStep]

    # Optional
    input_materials: List[MaterialInfo]
    quality_records: List[QualityRecord]

@dataclass
class TraceabilityStep:
    sequence: int
    operation_id: str
    operation_name: str
    equipment_id: str
    equipment_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    operator: Optional[str]
    ok_qty: int
    ng_qty: int
    parameters: Dict[str, Any]  # Process parameters
    quality_data: Dict[str, Any]  # Inspection results
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "LOT-001 이력 조회" | TRACEABILITY | {lot_no: LOT-001} | traceability/{lot_no} |
| "LOT-001 전체 이력 보여줘" | TRACEABILITY | {lot_no: LOT-001} | Full orchestration |
| "LOT-001 어디까지 진행됐어?" | PRODUCTION_STATUS | {lot_no: LOT-001} | orders + results |
| "LOT-001 품질 데이터" | TRACEABILITY | {lot_no: LOT-001, include_quality: true} | + quality records |

## Aggregation Logic
```python
def build_traceability(lot_no: str) -> TraceabilityRecord:
    # 1. Get work order
    order = get_order_by_lot(lot_no)
    if not order:
        raise NotFoundError(f"LOT {lot_no} not found")

    # 2. Get production results
    results = get_results_by_order(order.id)

    # 3. Get routing/scenario info
    work_info = get_work_info(lot_no)

    # 4. Build timeline from results
    steps = []
    for result in sorted(results, key=lambda r: r.start_time):
        equipment = get_equipment(result.equipment_id)
        operation = get_operation_info(work_info, result.operation_id)

        steps.append(TraceabilityStep(
            sequence=operation.sequence,
            operation_id=result.operation_id,
            operation_name=operation.name,
            equipment_id=result.equipment_id,
            equipment_name=equipment.name,
            start_time=result.start_time,
            end_time=result.end_time,
            status=result.status,
            operator=result.operator,
            ok_qty=result.ok_qty,
            ng_qty=result.ng_qty,
            parameters=result.process_params or {},
            quality_data=result.quality_data or {}
        ))

    # 5. Calculate summary
    total_ok = sum(s.ok_qty for s in steps)
    total_ng = sum(s.ng_qty for s in steps)

    return TraceabilityRecord(
        lot_no=lot_no,
        product_id=order.product_id,
        product_name=get_product_name(order.product_id),
        work_order_id=order.id,
        status=order.status,
        total_qty=order.qty,
        ok_qty=total_ok,
        ng_qty=total_ng,
        yield_rate=(total_ok / (total_ok + total_ng)) * 100 if (total_ok + total_ng) > 0 else 0,
        start_time=min(s.start_time for s in steps) if steps else order.planned_start,
        end_time=max(s.end_time for s in steps if s.end_time) if steps else None,
        steps=steps
    )
```

## Error Handling
- **LOT not found**: Return 404 with message "LOT 번호를 찾을 수 없습니다"
- **No production records**: Return order info with empty steps, message "아직 생산 기록이 없습니다"
- **Partial data**: Return available data with warnings for missing pieces
