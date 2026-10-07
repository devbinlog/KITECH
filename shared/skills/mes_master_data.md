# MES Master Data Skill

## Description
Queries master data including products, processes, scenarios, equipment specifications, and BOM (Bill of Materials). Provides reference data for other skills.

## Supported Intents
- `MASTER_DATA_QUERY`: 마스터 데이터 조회, 제품 정보, 공정 정보

## Required Entities
At least one of:
- `product_id`: Product ID/code
- `process_id`: Process ID
- `scenario_id`: Scenario ID
- `equipment_id`: Equipment ID
- `data_type`: Type of master data (product, process, scenario, equipment, bom)

## Optional Entities
- `include_routing`: Include process routing (default: false)
- `include_bom`: Include BOM details (default: false)

## API Endpoints
```
Products:
- GET /api/v1/masters/products
  returns: Product list

- GET /api/v1/masters/products/{product_id}
  returns: Product details

Processes:
- GET /api/v1/masters/processes
  returns: Process list

- GET /api/v1/masters/processes/{process_id}
  returns: Process details with operations

Scenarios:
- GET /api/v1/masters/scenarios
  returns: Scenario list

- GET /api/v1/masters/scenarios/{scenario_id}
  returns: Scenario details (routing)

Equipment:
- GET /api/v1/masters/equipments
  returns: Equipment list

- GET /api/v1/masters/equipments/{equipment_id}
  returns: Equipment specifications
```

## Output Types
- `detail`: Single item detailed view
- `list`: Table with items
- `tree`: Hierarchical view (for BOM/routing)

## UI Schema Template (Product Detail)
```json
{
  "layout": "detail",
  "components": [
    {
      "type": "MasterDataHeader",
      "props": {
        "type": "product",
        "id": "PART-A",
        "name": "알루미늄 브라켓",
        "status": "ACTIVE"
      }
    },
    {
      "type": "PropertyGrid",
      "props": {
        "title": "제품 정보",
        "properties": [
          {"label": "제품코드", "value": "PART-A"},
          {"label": "제품명", "value": "알루미늄 브라켓"},
          {"label": "단위", "value": "EA"},
          {"label": "표준 사이클타임", "value": "45분"},
          {"label": "생성일", "value": "2024-01-15"},
          {"label": "상태", "value": "ACTIVE"}
        ]
      }
    },
    {
      "type": "RoutingDiagram",
      "props": {
        "title": "공정 흐름",
        "operations": [
          {"seq": 10, "name": "소재 투입", "equipment_type": "LOADER"},
          {"seq": 20, "name": "1차 가공", "equipment_type": "CNC"},
          {"seq": 30, "name": "2차 가공", "equipment_type": "CNC"},
          {"seq": 40, "name": "검사", "equipment_type": "CMM"}
        ]
      }
    }
  ]
}
```

## UI Schema Template (List)
```json
{
  "layout": "list",
  "components": [
    {
      "type": "DataTable",
      "props": {
        "title": "제품 목록",
        "columns": [
          {"key": "product_id", "label": "제품코드", "sortable": true},
          {"key": "name", "label": "제품명", "sortable": true},
          {"key": "unit", "label": "단위"},
          {"key": "cycle_time", "label": "사이클타임"},
          {"key": "status", "label": "상태", "filterable": true}
        ],
        "data": "{products}",
        "searchable": true,
        "pagination": true,
        "pageSize": 20
      }
    }
  ]
}
```

## UI Schema Template (Equipment)
```json
{
  "layout": "detail",
  "components": [
    {
      "type": "EquipmentSpec",
      "props": {
        "id": "CNC-001",
        "name": "CNC 밀링 #1",
        "type": "CNC",
        "manufacturer": "FANUC",
        "model": "RoboDrill α-D21MiA5",
        "location": "LINE-1",
        "status": "ACTIVE",
        "specifications": {
          "max_rpm": 10000,
          "axis": "5-axis",
          "table_size": "500x400mm",
          "tool_capacity": 21
        },
        "capabilities": ["milling", "drilling", "tapping"],
        "maintenance": {
          "last_date": "2024-01-10",
          "next_date": "2024-02-10",
          "interval_days": 30
        }
      }
    }
  ]
}
```

## Data Types
```python
@dataclass
class Product:
    id: str
    code: str
    name: str
    unit: str
    cycle_time_minutes: float
    status: str  # ACTIVE, INACTIVE
    created_at: datetime
    routing: Optional[List[Operation]]
    bom: Optional[List[BOMItem]]

@dataclass
class Process:
    id: str
    code: str
    name: str
    description: str
    operations: List[Operation]

@dataclass
class Operation:
    id: str
    sequence: int
    name: str
    equipment_types: List[str]
    duration_minutes: float
    setup_time_minutes: float

@dataclass
class Scenario:
    id: str
    product_id: str
    name: str
    routing: List[RoutingStep]  # Process + equipment assignment

@dataclass
class Equipment:
    id: str
    code: str
    name: str
    type: str
    manufacturer: str
    model: str
    location: str
    status: str
    specifications: Dict[str, Any]
    capabilities: List[str]
```

## Sample Queries
| Query | Intent | Entities | API Calls |
|-------|--------|----------|-----------|
| "제품 목록" | MASTER_DATA_QUERY | {data_type: product} | masters/products |
| "PART-A 제품 정보" | MASTER_DATA_QUERY | {product_id: PART-A} | masters/products/PART-A |
| "공정 목록 조회" | MASTER_DATA_QUERY | {data_type: process} | masters/processes |
| "CNC-001 사양" | MASTER_DATA_QUERY | {equipment_id: CNC-001} | masters/equipments/CNC-001 |
| "PART-A 공정 흐름" | MASTER_DATA_QUERY | {product_id: PART-A, include_routing: true} | products + scenarios |

## Orchestration Pattern
```
Product with Routing:
1. GET /masters/products/{id}
2. GET /masters/scenarios?product_id={id}
3. For each operation:
   └── GET /masters/processes/{process_id} (optional details)

Equipment List with Capabilities:
1. GET /masters/equipments
2. Group by type for display

Full Master Data Export:
Parallel:
├── GET /masters/products
├── GET /masters/processes
├── GET /masters/scenarios
└── GET /masters/equipments
```

## Error Handling
- **Not found**: Return 404 with message "해당 데이터를 찾을 수 없습니다"
- **Invalid ID format**: Return error with valid format example
- **Empty list**: Return empty with message "등록된 {type}이 없습니다"
