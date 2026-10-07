# MES KPI Query Skill

## Description
Calculates and retrieves manufacturing KPIs including OEE (Overall Equipment Effectiveness), utilization rate, yield rate, and production efficiency metrics.

## Supported Intents
- `KPI_QUERY`: KPI 조회, 지표 확인
- `ANALYTICS`: 트렌드 분석, 비교 분석
- `COMPARISON`: 설비별/기간별 비교

## Required Entities
None (defaults to today's overall KPI)

## Optional Entities
- `metric`: Specific KPI type (utilization, yield, oee, production, efficiency)
- `date`: Specific date
- `date_range`: Date range for trend (this_week, last_month, last_7_days)
- `group_by`: Grouping dimension (equipment, product, day, shift)
- `equipment_id`: Filter by equipment
- `product_id`: Filter by product

## KPI Definitions
```yaml
utilization (가동률):
  formula: (actual_run_time / available_time) * 100
  unit: "%"
  target: 85

yield (수율/양품률):
  formula: (ok_qty / (ok_qty + ng_qty)) * 100
  unit: "%"
  target: 98

oee (설비종합효율):
  formula: availability * performance * quality
  components:
    availability: (run_time / planned_time) * 100
    performance: (actual_output / theoretical_output) * 100
    quality: (ok_qty / total_qty) * 100
  unit: "%"
  target: 80

production (생산량):
  formula: sum(ok_qty)
  unit: "개"

efficiency (효율):
  formula: (actual_cycle_time / standard_cycle_time) * 100
  unit: "%"
```

## API Endpoints
```
Primary:
- GET /api/v1/analytics/kpis
  params: date, date_range, group_by
  returns: Calculated KPIs

- GET /api/v1/analytics/equipment-utilization
  params: date_range, equipment_ids
  returns: Per-equipment utilization

- GET /api/v1/analytics/trends
  params: metric, date_range, group_by
  returns: Time-series data

Secondary (for calculation):
- GET /api/v1/production/results
- GET /api/v1/scheduler/equipment-availability
```

## Orchestration Pattern
```
Overall KPI Dashboard:
Parallel:
├── GET /analytics/kpis
├── GET /analytics/equipment-utilization
└── GET /production/results (for detailed breakdown)

Trend Analysis:
1. GET /analytics/trends?metric={metric}&date_range={range}
2. GET /analytics/kpis (for current value comparison)

Comparison:
Parallel:
├── GET /analytics/equipment-utilization (all equipment)
└── GET /masters/equipments (for names)
```

## Output Types
- `dashboard`: KPI cards + gauges + trend chart (default)
- `comparison_chart`: Bar/column chart for comparison
- `trend_chart`: Line chart for time-series
- `single_value`: Single KPI value with gauge

## UI Schema Template (Dashboard)
```json
{
  "layout": "dashboard",
  "components": [
    {
      "type": "KPICard",
      "props": {
        "title": "가동률",
        "value": 87.5,
        "unit": "%",
        "target": 85,
        "trend": "+2.3%",
        "trendDirection": "up",
        "icon": "activity",
        "color": "green"
      }
    },
    {
      "type": "KPICard",
      "props": {
        "title": "수율",
        "value": 98.2,
        "unit": "%",
        "target": 98,
        "trend": "-0.1%",
        "trendDirection": "down",
        "icon": "check-circle",
        "color": "amber"
      }
    },
    {
      "type": "GaugeChart",
      "props": {
        "title": "OEE",
        "value": 78.5,
        "max": 100,
        "target": 80,
        "segments": [
          {"max": 60, "color": "red"},
          {"max": 80, "color": "yellow"},
          {"max": 100, "color": "green"}
        ]
      }
    },
    {
      "type": "LineChart",
      "props": {
        "title": "가동률 추이 (최근 7일)",
        "data": "{trend_data}",
        "xKey": "date",
        "yKey": "utilization",
        "targetLine": 85
      }
    }
  ]
}
```

## UI Schema Template (Comparison)
```json
{
  "layout": "single",
  "components": [
    {
      "type": "BarChart",
      "props": {
        "title": "설비별 가동률 비교",
        "data": [
          {"name": "CNC-001", "value": 92.3},
          {"name": "CNC-002", "value": 87.1},
          {"name": "CNC-003", "value": 78.5}
        ],
        "xKey": "name",
        "yKey": "value",
        "targetLine": 85,
        "colorByValue": true,
        "thresholds": {
          "red": 70,
          "yellow": 85,
          "green": 100
        }
      }
    }
  ]
}
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "가동률 보여줘" | KPI_QUERY | {metric: utilization} | analytics/kpis |
| "수율 조회" | KPI_QUERY | {metric: yield} | analytics/kpis |
| "OEE 확인" | KPI_QUERY | {metric: oee} | analytics/kpis |
| "이번 주 가동률 추이" | ANALYTICS | {metric: utilization, date_range: this_week} | analytics/trends |
| "설비별 가동률 비교" | COMPARISON | {metric: utilization, group_by: equipment} | equipment-utilization |
| "제품별 수율 비교" | COMPARISON | {metric: yield, group_by: product} | analytics/kpis |

## Calculation Notes
```python
def calculate_utilization(equipment_id, date_range):
    # Get equipment availability (planned time)
    availability = get_equipment_availability(equipment_id, date_range)
    planned_minutes = availability.total_minutes

    # Get actual production results (run time)
    results = get_production_results(equipment_id, date_range)
    run_minutes = sum(r.cycle_time * r.qty for r in results)

    return (run_minutes / planned_minutes) * 100 if planned_minutes > 0 else 0

def calculate_yield(results):
    ok_qty = sum(r.ok_qty for r in results)
    ng_qty = sum(r.ng_qty for r in results)
    total = ok_qty + ng_qty
    return (ok_qty / total) * 100 if total > 0 else 0

def calculate_oee(equipment_id, date_range):
    availability = calculate_availability(equipment_id, date_range)
    performance = calculate_performance(equipment_id, date_range)
    quality = calculate_yield(get_results(equipment_id, date_range))
    return (availability * performance * quality) / 10000
```

## Error Handling
- **No data for period**: Return 0 or N/A with message "해당 기간 데이터 없음"
- **Division by zero**: Return 0 with appropriate handling
- **Partial data**: Calculate with available data, add warning
