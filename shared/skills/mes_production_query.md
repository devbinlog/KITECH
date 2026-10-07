# MES Production Query Skill

## Description
Queries production status, work orders, and production results from the MES system. Supports daily summaries, filtered views, and real-time status monitoring.

## Supported Intents
- `PRODUCTION_STATUS`: 생산 현황, 작업지시 목록, 생산실적 조회
- `KPI_QUERY`: 생산 관련 KPI (완료율, 양품률)

## Required Entities
None (defaults to today's data)

## Optional Entities
- `date`: Specific date (today, yesterday, 2024-01-24)
- `date_range`: Date range (this_week, last_week, this_month, last_7_days)
- `lot_no`: LOT number filter
- `product_id`: Product ID/code filter
- `status`: Work order status filter (READY, RUNNING, DONE, ERROR)
- `equipment_id`: Equipment filter

## API Endpoints
```
Primary:
- GET /api/v1/production/orders
  params: date, status, product_id, lot_no

- GET /api/v1/production/results
  params: date, work_order_id, equipment_id

Secondary (for aggregated view):
- GET /api/v1/analytics/daily-status
  params: date

- GET /api/v1/masters/equipments
  params: (for equipment names)
```

## Orchestration Pattern
```
Parallel Execution:
├── GET /orders (date filter)
├── GET /results (date filter)
└── GET /equipments (for equipment details)

Sequential (if specific order):
1. GET /orders?lot_no=X
2. GET /results?work_order_id={order.id}
```

## Output Types
- `dashboard`: Multiple KPI cards + table + chart (default for summary)
- `list`: Table with work orders
- `single_value`: Count or specific metric

## UI Schema Template
```json
{
  "layout": "dashboard",
  "components": [
    {
      "type": "KPICard",
      "props": {
        "title": "총 작업지시",
        "value": "{total_orders}",
        "icon": "clipboard"
      }
    },
    {
      "type": "KPICard",
      "props": {
        "title": "완료",
        "value": "{completed}",
        "trend": "{completion_rate}%",
        "trendDirection": "up"
      }
    },
    {
      "type": "PieChart",
      "props": {
        "title": "작업 상태 분포",
        "data": [
          {"name": "완료", "value": "{completed}"},
          {"name": "진행중", "value": "{in_progress}"},
          {"name": "대기", "value": "{pending}"}
        ]
      }
    },
    {
      "type": "DataTable",
      "props": {
        "title": "작업지시 목록",
        "columns": ["lot_no", "product", "status", "ok_qty", "ng_qty"],
        "data": "{orders}"
      }
    }
  ]
}
```

## Aggregation Logic
```python
def aggregate_production_data(orders, results, equipments):
    # Join results with orders
    order_results = {}
    for result in results:
        wo_id = result.work_order_id
        if wo_id not in order_results:
            order_results[wo_id] = []
        order_results[wo_id].append(result)

    # Calculate per-order metrics
    for order in orders:
        results_for_order = order_results.get(order.id, [])
        order.ok_qty = sum(r.ok_qty for r in results_for_order)
        order.ng_qty = sum(r.ng_qty for r in results_for_order)
        order.yield_rate = calculate_yield(order.ok_qty, order.ng_qty)

    # Overall statistics
    return {
        "total_orders": len(orders),
        "completed": count(o for o in orders if o.status == "DONE"),
        "in_progress": count(o for o in orders if o.status == "RUNNING"),
        "pending": count(o for o in orders if o.status == "READY"),
        "total_ok_qty": sum(o.ok_qty for o in orders),
        "total_ng_qty": sum(o.ng_qty for o in orders),
        "yield_rate": calculate_yield(total_ok_qty, total_ng_qty),
        "orders": orders  # For table display
    }
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "오늘 생산 현황 보여줘" | PRODUCTION_STATUS | {date: today} | daily-status |
| "진행중인 작업지시" | PRODUCTION_STATUS | {status: RUNNING} | orders?status=RUNNING |
| "LOT-001 생산실적" | PRODUCTION_STATUS | {lot_no: LOT-001} | orders→results |
| "이번 주 생산량" | KPI_QUERY | {date_range: this_week} | results aggregated |

## Error Handling
- **No orders found**: Return empty list with message "해당 조건의 작업지시가 없습니다"
- **API timeout**: Return partial data with warning
- **Invalid date**: Default to today with warning
