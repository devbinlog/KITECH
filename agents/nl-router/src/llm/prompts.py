"""Prompt templates for LLM-based NL understanding"""

INTENT_CLASSIFICATION_PROMPT = """You are an MES (Manufacturing Execution System) assistant.
Classify the user's query into one of these intents:

## Available Intents:
- PRODUCTION_STATUS: 생산 현황, 작업지시 목록, 생산실적 요약 조회
- PRODUCTION_DETAIL: 특정 LOT이나 작업지시의 상세 정보 조회
- EQUIPMENT_STATUS: 설비 상태, 실시간 모니터링
- EQUIPMENT_LIST: 설비 목록 조회
- SCHEDULE_QUERY: 스케줄, 일정 조회
- SCHEDULE_REQUEST: 스케줄링 요청
- MASTER_DATA_QUERY: 제품, 공정, 시나리오 마스터 데이터 조회
- KPI_QUERY: KPI, 가동률, 수율 등 지표 조회
- ANALYTICS: 트렌드, 분석, 추이 조회
- COMPARISON: 비교 분석 (설비별, 제품별)
- TRACEABILITY: LOT 추적, 생산 이력 조회
- ACTION_REQUEST: 작업지시 생성, 설비 동기화 등 액션 요청
- UNKNOWN: 위 카테고리에 해당하지 않는 질문

## Entity Extraction:
Also extract relevant entities from the query:
- date: 날짜 (오늘, 어제, 2024-01-24 등)
- date_range: 기간 (이번 주, 지난 달, 최근 7일 등)
- equipment_id: 설비 ID (CNC-001, ROBOT-001 등)
- equipment_type: 설비 타입 (CNC, ROBOT, PLC)
- product_id/product_code: 제품 ID/코드
- lot_no: LOT 번호 (LOT-001, LOT-2024-001 등)
- status: 상태 (진행중, 완료, 대기, 에러)
- metric: 지표 (가동률, 수율, 생산량)
- group_by: 그룹핑 기준 (설비별, 제품별, 일별)

## User Query:
{query}

## Previous Context (if any):
{context}

## Response Format:
Respond in JSON format:
```json
{{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {{
    "entity_type": "extracted_value"
  }},
  "sub_intent": "optional_sub_intent",
  "reasoning": "분류 근거를 간단히 설명",
  "requires_clarification": false,
  "suggested_questions": []
}}
```

Important:
- Set requires_clarification=true if the query is ambiguous
- Include suggested_questions if clarification is needed
- confidence should reflect how certain you are about the classification
"""

ENTITY_EXTRACTION_PROMPT = """Extract entities from the following MES-related query.

## Entity Types to Extract:
- date: 특정 날짜 (normalize to YYYY-MM-DD or keywords like "today", "yesterday")
- date_range: 기간 (normalize to: this_week, last_week, this_month, last_month, last_7_days, last_30_days)
- equipment_id: 설비 ID (keep as-is)
- equipment_type: 설비 타입 (normalize to: CNC, ROBOT, PLC)
- lot_no: LOT 번호 (keep as-is)
- status: 상태 (normalize to: READY, RUNNING, DONE, ERROR)
- metric: 지표 (normalize to: utilization, yield, production, completion)
- group_by: 그룹핑 (normalize to: equipment, product, day)
- quantity: 수량 (extract as number)

## Query:
{query}

## Response Format:
```json
{{
  "entities": [
    {{
      "type": "entity_type",
      "value": "extracted_value",
      "raw_text": "original text",
      "normalized": "normalized_value_if_different"
    }}
  ]
}}
```

Extract all relevant entities. If no entities found, return empty entities array.
"""

UI_SCHEMA_GENERATION_PROMPT = """Based on the query result data, generate a UI schema for rendering.

## Available Component Types:
- KPICard: Single metric display (title, value, trend, icon)
- DataTable: Tabular data (columns, rows, sortable)
- LineChart: Time series data (x-axis, y-values, series)
- BarChart: Categorical comparison (categories, values)
- PieChart: Distribution (segments, values)
- GanttChart: Schedule visualization (tasks, timeline)
- StatusCards: Grid of status indicators (items with status)
- TraceabilityTimeline: Sequential events (events with timestamps)

## Query:
{query}

## Data:
{data}

## Output Type Hint:
{output_type}

## Response Format:
```json
{{
  "layout": "dashboard|single|grid",
  "title": "Dynamic title based on query",
  "components": [
    {{
      "type": "ComponentType",
      "props": {{
        "title": "Component title",
        ...component_specific_props
      }},
      "position": {{"row": 0, "col": 0, "width": 1, "height": 1}}
    }}
  ]
}}
```

Generate appropriate components based on the data structure and output type hint.
"""

NATURAL_RESPONSE_PROMPT = """Generate a natural Korean response for the MES query result.

## Query:
{query}

## Data Summary:
{data_summary}

## Guidelines:
- Be concise but informative
- Use Korean naturally
- Highlight key metrics
- Mention any issues or alerts
- Keep it under 3 sentences

## Response:
"""
