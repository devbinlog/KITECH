# Cell1 P4R JSON Cycle Time Implementation Plan

## 목적

Cell-MES의 LOT 기준 P4R JSON 생성 API를 개선한다. 핵심은 P4R `PROCESS_INFO.PROCESS_OPERATION_INFO[].PROCESSING_TIME`을 단순 표준공정 시간(`std_processes.cycle_time_sec`)이 아니라, 제품별 공정 라우팅(`process_routings`)과 NC 파일 분석 결과를 기준으로 생성하는 것이다.

기존 논의에서는 AAS `P4RActionTimingProfile`에 `machining=120` 같은 고정값을 넣는 방안도 검토했지만, CNC 가공시간은 장비 고정값이 아니라 제품, 라우팅, NC 파일에 따라 달라진다. 따라서 실제 machining 시간은 AASX가 아니라 MES 라우팅/NC 파일 메타데이터에 둔다.

## 최종 원칙

| 영역 | 책임 |
| --- | --- |
| `std_processes` | 표준공정의 기본 템플릿 시간. 예: `MILL` 기본 120초 |
| `process_routings` | 제품별/라우팅별 최종 cycle time. NC 가공시간과 공정 내부 setup/tending 시간을 포함할 수 있는 P4R `PROCESSING_TIME`의 주 출처 |
| `process_routing_files` | NC 파일별 분석 시간과 파일 역할 |
| AAS `DtSimulationProfile` | 장비 타입, capacity, MTTR/MTBF 같은 정적 기준정보 |
| AAS `P4RActionTimingProfile` | 장비 고유 동작 시간. 문/바이스/그리퍼 같은 action의 라우팅 시간 산정 근거 |
| 미들웨어/AAS runtime 상태 | 장비 연결, gateway status, unit alarm 같은 raw 상태 |
| P4R Adapter | MES + YAML + AAS raw 상태를 조합해 최종 P4R JSON 생성 |

가장 중요한 결정은 다음과 같다.

```text
기본값: P4R PROCESSING_TIME = process_routings.cycle_time_sec 우선
명시 매핑: PROCESSING_TIME = YAML op_id action profile 합계 또는 routing cycle time + action profile 합계
```

AAS action timing은 machining 시간을 대체하지 않는다. 대신 door/vise/robot tending처럼 특정 공정 내부에서 실제로 장비를 점유하는 동작은 라우팅 cycle time의 구성요소가 될 수 있다. 현재 구현은 기존 영향 최소화를 위해 YAML에 `p4r_process_mapping`이 명시된 경우에만 AAS `P4RActionTimingProfile`을 읽어 `PROCESSING_TIME`에 반영한다. 매핑이 없으면 기존처럼 `process_routings.cycle_time_sec`를 읽고, 값이 없으면 `std_processes.cycle_time_sec`로 fallback한다.

## 기준 데이터

| 항목 | 값 |
| --- | --- |
| 대표 LOT | `LOT-20260730-001` |
| 제품 | `PLAT-A002` |
| 제품명 | `드릴 지그 플레이트(cell1)` |
| 시나리오 | `cell1 가공시나리오` |
| 시나리오 파일 | `cell-mes/data/scenario_cell1_m20.yaml` |
| Cell1 자산 | `NX5500`, `FEEDER`, `ANT_AMR`, `UR_ROBOT`, `CNC_DIE` |
| 현재 MES 라우팅 | `LOAD -> MILL -> UNLOAD` |
| 현재 표준공정 시간 | `LOAD=30`, `MILL=120`, `UNLOAD=45` |

현재 DB 구조에서는 `MILL`을 여러 제품이 공유하면 모두 `std_processes.cycle_time_sec=120`을 사용한다. 개선 후에는 각 제품의 `process_routings` row가 별도 cycle time을 가진다.

## DB 모델 변경

### `process_routings` 추가 컬럼

제품별 공정 단계의 최종 cycle time을 저장한다.

| 컬럼 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `cycle_time_sec` | `Integer` | `std_process.cycle_time_sec` 복사 | P4R `PROCESSING_TIME`에 사용할 제품별 라우팅 시간 |
| `cycle_time_source` | `String(30)` | `STD_PROCESS` | 시간이 어디서 왔는지 |
| `cycle_time_confidence` | `Float` | `0.5` | 시간 추정 신뢰도 |
| `cycle_time_updated_at` | `DateTime(timezone=True)` | `now()` | 마지막 갱신 시각 |
| `cycle_time_aggregation` | `String(30)` | `PRIMARY_FILE` 또는 `SUM_FILES` | NC 파일 여러 개일 때 라우팅 시간 계산 방식 |
| `cycle_time_breakdown` | `JSON` | `null` | NC, 공정 내부 action, 보정시간 등 최종 cycle time 구성요소 |

`cycle_time_source` 후보:

| 값 | 의미 |
| --- | --- |
| `STD_PROCESS` | 표준공정 기본값을 복사한 상태 |
| `MANUAL` | 사용자가 직접 입력 |
| `NC_ANALYSIS` | NC 파일 분석 결과 |
| `HISTORY_AVG` | 과거 실적 평균 |
| `EXTERNAL` | 외부 시스템에서 받은 값 |

### `PROCESSING_TIME` 산정 범위

과기대 답변 자료 기준으로 P4R `PROCESS_INFO`는 YAML의 모든 step을 그대로 옮기는 영역이 아니라, 일정 시간 동안 진행되는 작업 단위를 표현한다. 따라서 로봇 동작이라고 해서 무조건 제외하지 않는다. 해당 동작이 어떤 P4R 영역에 속하는지에 따라 다르게 처리한다.

| 동작 유형 | P4R 반영 위치 | 판단 기준 |
| --- | --- | --- |
| AMR 이동, 설비 간 pick/place, 소재/제품 반송 | `MATERIAL_HANDLING_INFO.LOADING_TIME`, `UNLOADING_TIME` | 소재가 공정 장비 사이를 이동하는 물류/handling 작업 |
| CNC 내부 소재 투입, 제품 반출, door/vise 제어 | 해당 라우팅의 `PROCESSING_TIME`에 포함 가능 | CNC 또는 공정 장비를 점유한 상태에서 공정 준비/해제에 필요한 작업 |
| NC 실제 가공 | `MILL` 라우팅의 `PROCESSING_TIME` | 제품/NC 파일에 따라 달라지는 핵심 가공 작업 |
| QCM 검사 | 검사 라우팅의 `PROCESSING_TIME` | 품질 장비에서 일정 시간 진행되는 검사 작업 |
| query/polling, `wait_retry` | 직접 합산하지 않음 | 상태 확인 또는 timeout 상한이며 실제 작업시간이 아님 |

즉 최종 공식은 다음처럼 정의한다.

```text
process_routings.cycle_time_sec
= 공정 내부 setup/tending 시간
+ NC/검사/조립 등 실제 작업 시간
+ 필요 시 보정 시간
```

`MATERIAL_HANDLING_INFO`의 loading/unloading 시간과 `PROCESS_INFO.PROCESSING_TIME`을 동시에 같은 동작에 넣으면 중복 계산이 된다. 따라서 action별로 `PROCESS_INTERNAL`, `MATERIAL_HANDLING`, `STATE_CHECK`, `TRIGGER` 같은 분류를 두고, 하나의 시간은 한 영역에만 귀속한다.

`cycle_time_breakdown` 예시:

```json
{
  "routing_id": 55,
  "total_sec": 417,
  "components": [
    {"type": "NC_ANALYSIS", "source": "O0012.nc", "duration_sec": 342},
    {"type": "PROCESS_INTERNAL", "asset": "NX5500", "action": "open_door", "duration_sec": 5},
    {"type": "PROCESS_INTERNAL", "asset": "NX5500", "action": "open_vise", "duration_sec": 5},
    {"type": "PROCESS_INTERNAL", "asset": "UR_ROBOT", "action": "detect", "duration_sec": 10},
    {"type": "PROCESS_INTERNAL", "asset": "UR_ROBOT", "action": "pick_slot", "duration_sec": 15},
    {"type": "PROCESS_INTERNAL", "asset": "UR_ROBOT", "action": "place", "duration_sec": 15},
    {"type": "PROCESS_INTERNAL", "asset": "NX5500", "action": "close_vise", "duration_sec": 5},
    {"type": "PROCESS_INTERNAL", "asset": "NX5500", "action": "close_door", "duration_sec": 5},
    {"type": "PROCESS_INTERNAL", "asset": "UR_ROBOT", "action": "cycle_start", "duration_sec": 20},
    {"type": "ADJUSTMENT", "reason": "safety_margin", "duration_sec": 10}
  ],
  "excluded": [
    {"type": "MATERIAL_HANDLING", "asset": "ANT_AMR", "action": "move", "reason": "handled_by_MATERIAL_HANDLING_INFO"},
    {"type": "PROCESS_INTERNAL", "asset": "UR_ROBOT", "action": "home", "duration_sec": 15, "reason": "not_required_for_nominal_routing_cycle"},
    {"type": "STATE_CHECK", "asset": "NX5500", "action": "is_M20", "reason": "polling_or_timeout"}
  ]
}
```

### `process_routing_files` 추가 컬럼

NC 파일별 분석 결과를 저장한다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `file_role` | `String(30)` | `PRIMARY`, `SETUP`, `ROUGHING`, `FINISHING`, `DRILLING` 등 |
| `sequence_no` | `Integer` | 한 라우팅 안에서 NC 파일 실행 순서 |
| `estimated_cycle_time_sec` | `Integer` | 해당 NC 파일 단위 분석 시간 |
| `analysis_source` | `String(30)` | `PARSER`, `SIMULATOR`, `MANUAL` |
| `analysis_status` | `String(30)` | `PENDING`, `DONE`, `FAILED` |
| `analysis_error` | `Text` | 분석 실패 사유 |
| `analyzed_at` | `DateTime(timezone=True)` | 분석 시각 |

## 라우팅 생성 정책

제품 라우팅을 만들 때는 `std_processes.cycle_time_sec`를 `process_routings.cycle_time_sec`에 복사한다.

예시:

| 제품 | 라우팅 | 표준공정 | 최초 라우팅 시간 |
| --- | --- | --- | --- |
| `PLAT-A002` | `LOAD` | `LOAD=30` | 30 |
| `PLAT-A002` | `MILL` | `MILL=120` | 120 |
| `PLAT-A002` | `UNLOAD` | `UNLOAD=45` | 45 |

이 시점의 `cycle_time_source`는 `STD_PROCESS`다. 이후 NC 파일을 업로드하거나 사용자가 직접 수정하면 라우팅 row의 cycle time만 바뀐다. 표준공정의 기본값은 다른 제품의 템플릿으로 유지한다.

## NC 파일 업로드 정책

NC 파일을 라우팅에 업로드하면 다음 흐름으로 처리한다.

1. `process_routing_files`에 파일 메타데이터를 저장한다.
2. NC 분석 모듈이 예상 가공시간을 계산한다.
3. 파일 row의 `estimated_cycle_time_sec`, `analysis_status`, `analyzed_at`을 업데이트한다.
4. 해당 라우팅의 `cycle_time_sec`를 재계산한다.
5. 해당 라우팅의 `cycle_time_source`를 `NC_ANALYSIS`로 바꾼다.

NC 분석 모듈은 단계적으로 구현한다.

| 단계 | 내용 |
| --- | --- |
| 1차 | 파일별 시간 수동 입력 또는 mock analyzer |
| 2차 | G-code feed rate, rapid move, spindle command 기반 간이 계산 |
| 3차 | 장비별 acceleration, tool change, dwell, probing, controller 특성 반영 |
| 4차 | 실제 CNC 실적 데이터와 보정 계수 적용 |

## 동일 표준공정 다중 사용

같은 제품 안에 `MILL` 라우팅이 여러 개 있을 수 있다. 이 경우 각 `process_routings.id`가 독립적인 cycle time을 가진다.

예시:

| 라우팅 | 표준공정 | 역할 | cycle time |
| --- | --- | --- | --- |
| `routing_id=55` | `MILL` | 상면 가공 | 240 |
| `routing_id=58` | `MILL` | 측면 가공 | 420 |
| `routing_id=61` | `MILL` | 홀 가공 | 180 |

P4R `PROCESS_OPERATION_INFO_ID`는 표준공정 코드가 아니라 라우팅 인스턴스를 구분할 수 있어야 한다.

권장 ID:

```text
POI_{PRODUCT_CODE}_{ROUTING_ID}
```

Cell1 예시:

```text
POI_PLAT-A002_54
POI_PLAT-A002_55
POI_PLAT-A002_56
```

## 한 라우팅에 NC 파일 여러 개

하나의 `MILL` 라우팅에 NC 파일이 여러 개 붙을 수 있다. 이 경우 aggregation 정책이 필요하다.

| 정책 | 설명 | 사용 예 |
| --- | --- | --- |
| `SUM_FILES` | 모든 NC 파일 시간을 합산 | 순차 실행되는 여러 가공 파일 |
| `PRIMARY_FILE` | 대표 파일 하나만 사용 | 대체 파일/버전 관리 |
| `MAX_FILES` | 가장 긴 파일을 사용 | 병렬 후보 중 worst case |
| `MANUAL` | 라우팅 시간을 직접 유지 | 분석값을 참고만 할 때 |

1차 구현 권장값은 `SUM_FILES`다. Cell-MES에서 한 라우팅에 여러 NC 파일이 붙었다면 순차 실행 가능성이 높기 때문이다. 다만 파일 role이 `ALTERNATIVE` 또는 `BACKUP`으로 들어오면 합산 대상에서 제외할 수 있게 설계한다.

## AASX 추가 방향

### `P4RActionTimingProfile`

AAS에는 장비 고유 동작 시간을 넣는다. 여기에는 machining 고정시간을 넣지 않지만, door/vise/robot tending처럼 공정 내부 시간 산정에 필요한 action timing은 넣을 수 있다. 이 값은 YAML `p4r_process_mapping`이 있는 P4R preview에서 `PROCESSING_TIME` 산정에 사용하고, 장기적으로는 라우팅별 `cycle_time_sec` 산정/검증 근거로도 사용할 수 있다.

Cell1 기준 후보:

| 자산 | action | 기본 시간 | source | 시간 귀속 후보 |
| --- | --- | --- | --- | --- |
| `NX5500` | `open_door` | 5 | YAML delay | `PROCESS_INTERNAL` |
| `NX5500` | `close_door` | 5 | YAML delay | `PROCESS_INTERNAL` |
| `NX5500` | `open_vise` | 5 | YAML delay | `PROCESS_INTERNAL` |
| `NX5500` | `close_vise` | 5 | YAML delay | `PROCESS_INTERNAL` |
| `NX5500` | `cycle_start` | 0 | trigger | `TRIGGER` |
| `NX5500` | `excute_main_program` | 0 | command | `PROGRAM_SELECT` |
| `FEEDER` | `load` | 45 | `DtSimulationProfile.loading_time_sec` | `MATERIAL_HANDLING` 또는 `LOAD_PROCESS` 결정 필요 |
| `FEEDER` | `unload` | 45 | `DtSimulationProfile.unloading_time_sec` | `MATERIAL_HANDLING` 또는 `UNLOAD_PROCESS` 결정 필요 |
| `ANT_AMR` | `pick` | TBD | action mapping/실측 필요 | `MATERIAL_HANDLING` |
| `ANT_AMR` | `place` | TBD | action mapping/실측 필요 | `MATERIAL_HANDLING` |
| `UR_ROBOT` | `DETECT` | 10 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `PICK_SLOT` | 15 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `PICK` | 15 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `PLACE` | 15 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `GRIPPER_OPEN` | 2 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `GRIPPER_CLOSE` | 2 | AASX 초기값 | `PROCESS_INTERNAL` |
| `UR_ROBOT` | `HOME` | 15 | AASX 초기값 | `PROCESS_INTERNAL`, 기본 라우팅 기여 후보 아님 |
| `UR_ROBOT` | `CYCLE_START` | 20 | AASX 초기값 | `PROCESS_INTERNAL` |
| `CNC_DIE` | `occupy` | 0 | state change | `STATE_CHANGE` |
| `CNC_DIE` | `release` | 0 | state change | `STATE_CHANGE` |

`FEEDER`의 경우 MES `LOAD=30`과 AAS `loading_time_sec=45`가 다를 수 있다. Cell1 구현에서는 YAML mapping이 `LOAD/UNLOAD`를 `ACTION_PROFILE`로 지정하면 AAS action profile 합계가 `PROCESSING_TIME`에 들어간다. 해당 action이 `MATERIAL_HANDLING_INFO`에도 반영되는 경우 중복 계산이 되므로, AAS profile의 `canContributeToRoutingCycleTime`과 시간 귀속 분류를 함께 검토해야 한다.

### FEEDER buffer 표현

소재 공급기의 `DtSimulationProfile.capacity=1`은 장비가 동시에 수행할 수 있는 처리 capacity로 유지한다. 소재 10개, 제품 10개 수용 능력은 같은 값을 10으로 바꾸는 것이 아니라 P4R `BUFFER_TYPE`으로 별도 표현한다.

| FEEDER AAS 원천 | P4R 위치 | 의미 |
| --- | --- | --- |
| `DtSimulationProfile.capacity = 1` | `MACHINE_TYPE.CAPACITY` | FEEDER 동시 처리 능력 |
| `schedulerInfo.loaderSlots = 10` | `BUFFER_TYPE BT_FEEDER_IN.CAPACITY` | 원소재 투입 슬롯 수 |
| `schedulerInfo.unloaderSlots = 10` | `BUFFER_TYPE BT_FEEDER_OUT.CAPACITY` | 제품 회수 슬롯 수 |
| `RobotGateway.Status.loaderCount` | `BUFFER_INSTANCE FEEDER_IN.WORK_IN_PROCESS_NUM` | 현재 원소재 슬롯 점유 수량 |
| `RobotGateway.Status.unloaderCount` | `BUFFER_INSTANCE FEEDER_OUT.WORK_IN_PROCESS_NUM` | 현재 제품 회수 슬롯 점유 수량 |

`FEEDER_IN`은 아직 특정 공정을 완료한 WIP가 아니므로 `FINISHED_OPERATION_INFO_ID`를 빈 값으로 둔다. `FEEDER_OUT`은 회수된 제품이 있을 때 마지막 `UNLOAD` operation id를 연결한다.

### Failure status 판단 정책

1차 구현에서는 미들웨어가 `P4RRuntimeStatus` submodel을 직접 갱신하지 않는다. 미들웨어는 기존처럼 장비 gateway `IsConnected`, `Status`, LOT/unit `ALARM` 메시지를 raw 상태로 제공하고, MES P4R adapter가 이 값을 P4R용 failure 의미로 정규화한다.

이 방식은 P4R 변환 책임을 MES에 모으고, 미들웨어가 P4R 전용 enum이나 repair time 정책을 알지 않아도 되게 한다. AAS `P4RRuntimeStatus`는 나중에 외부 시스템과 표준화된 runtime snapshot을 공유해야 할 때 선택적으로 추가한다.

| 항목 | 설명 | P4R 매핑 |
| --- | --- | --- |
| `failureType` | MES가 raw 상태/메시지를 규칙으로 해석한 P4R용 고장 유형. 정상은 `NONE` | `MACHINE_INSTANCE.FAILURE_STATUS[].FAILURE_TYPE` |
| `remainingRepairTime` | `failureType`별 기본 복구 시간 또는 향후 장애 시작시각 기반 잔여 시간 | `MACHINE_INSTANCE.FAILURE_STATUS[].REMAINING_REPAIR_TIME` |
| `currentOperationInfoId` | 현재 수행 중인 P4R operation id. failure 판단과 별도 단계에서 매핑 | `MACHINE_INSTANCE.WORK_IN_PROCESS_STATUS[].PROCESS_OPERATION_INFO_ID` |
| `elapsedProcessingTimeSec` | 현재 operation에서 이미 진행된 시간. failure 판단과 별도 단계에서 매핑 | `MACHINE_INSTANCE.WORK_IN_PROCESS_STATUS[].PROCESSED_TIME` |

Failure rule 우선순위:

| 우선순위 | 원천 신호 | 표준 `failureType` | 기본 `remainingRepairTime` | 비고 |
| ---: | --- | --- | ---: | --- |
| 1 | gateway `IsConnected=false` | `DISCONNECTED` | 0 또는 300 | 연결 끊김은 실제 수리시간을 알 수 없으므로 설정값으로 조정 |
| 2 | `GatewayNoResponse`, `응답 없음`, timeout | `NO_RESPONSE` | 300 | 장비/게이트웨이 무응답 |
| 3 | CNC `alarm`, `error`, `status=ALARM/ERROR/FAULT` | `CNC_ALARM` | 600 | CNC 장비 알람 |
| 4 | Robot `status=ERROR`, `result=FAILURE`, error field 존재 | `ROBOT_ERROR` | 300 | 로봇 명령 실패 또는 로봇 상태 오류 |
| 5 | FEEDER/AMR/BUFFER raw status 오류 | `{RESOURCE_TYPE}_ERROR` | 300 | 예: `FEEDER_ERROR`, `AMR_ERROR` |
| 6 | unit `ALARM` + `step timeout` | `PROCESS_TIMEOUT` | 300 | 장비 고장이 아닐 수 있으므로 raw 근거를 wrapper에 남김 |
| 7 | unit `ALARM` + 자원 대기/교착 | `RESOURCE_BLOCKED` | 0 | 설비 고장보다 운용 흐름 문제로 분류 |
| 8 | 알 수 없는 error/alarm | `UNKNOWN_ERROR` | 300 | fallback |
| 9 | 정상 | `NONE` | 0 | 기본값 |

Raw 메시지는 P4R payload 내부에 넣지 않는다. 대신 preview wrapper의 `sources.p4r_failure_interpretations`에 남긴다.

```json
{
  "asset": "NX5500",
  "failureType": "CNC_ALARM",
  "remainingRepairTime": "600",
  "matchedRule": "cnc_alarm_status",
  "rawStatus": {"status": "ALARM"},
  "rawMessage": "..."
}
```

#### Failure rule 저장 방식

Failure rule은 JSON 설정 파일로 관리한다. 아직 과기대/P4R 검증 과정에서 변경 가능성이 높고, P4R adapter의 변환 정책에 가까우므로 파일 기반으로 두는 편이 단순하다.

권장 파일:

```text
agents/cell-mes/config/p4r_failure_rules.json
```

권장 환경변수:

```text
P4R_FAILURE_RULES_PATH=/app/agents/cell-mes/config/p4r_failure_rules.json
```

예시:

```json
{
  "version": "1.0",
  "default": {
    "failureType": "NONE",
    "remainingRepairTime": 0
  },
  "rules": [
    {
      "id": "disconnected",
      "priority": 10,
      "when": {
        "isConnected": false
      },
      "result": {
        "failureType": "DISCONNECTED",
        "remainingRepairTime": 300
      }
    },
    {
      "id": "cnc_alarm",
      "priority": 30,
      "resourceTypes": ["CNC"],
      "whenAny": [
        {"statusIn": ["ALARM", "ERROR", "FAULT"]},
        {"hasField": "alarm"},
        {"hasField": "error"}
      ],
      "result": {
        "failureType": "CNC_ALARM",
        "remainingRepairTime": 600
      }
    }
  ]
}
```

JSON 파일 방식은 Docker volume mount로 교체할 수 있으므로 rule 조정 때 이미지 재빌드 부담이 작다. 단, rule schema 검증과 fallback 기본값은 코드에 반드시 둔다.

검토 결과 이 방식의 구현 blocker는 없다. 다만 다음 안전장치를 반드시 둔다.

| 리스크 | 보완책 |
| --- | --- |
| 메시지 문구 변경으로 오분류 | 구조화된 `status`, `error`, `alarm`, `result`, `IsConnected`를 먼저 보고 메시지는 보조 keyword로만 사용 |
| 공정 알람을 장비 고장으로 오해 | unit alarm은 `acq_map`, 현재 step asset, gateway 오류 문구가 있을 때만 장비 failure로 승격 |
| 오래된 `last_data`가 남아 오탐 | P4R 생성 시 가능하면 live `/api/aas/view`를 우선 사용하고, 정상 상태가 관측되면 `NONE`으로 되돌림 |
| `remainingRepairTime`이 진짜 잔여 시간이 아님 | 1차는 failure type별 예상 복구 시간으로 사용. 장애 시작시각 저장 후 잔여 시간 계산으로 확장 |
| P4R 허용 enum 미확정 | enum/repair time table을 코드 상수 또는 설정으로 분리해 변경 가능하게 유지 |

중요: `PROCESSED_TIME`은 실시간 상태값이며 `PROCESS_INFO`에 넣는 시간이 아니다. `PROCESS_INFO.PROCESSING_TIME`은 계획/예상 총 소요시간이고, `WORK_IN_PROCESS_STATUS.PROCESSED_TIME`은 현재 진행된 시간이다.

## YAML 정책

시나리오 YAML은 P4R process time의 주 출처로 사용하지 않는다. YAML은 실행 절차와 자산/action mapping을 제공한다.

YAML에서 사용할 정보:

| YAML 정보 | 사용처 |
| --- | --- |
| `assets[].name` | P4R `MACHINE_INSTANCE`, `MM_INSTANCE`, buffer 매핑 |
| `steps[].action` | AAS action timing 매칭, process/handling 구분 참고 |
| `steps[].op_id` | MES 라우팅과 매핑되었을 때만 process group trace로 사용 |
| `steps[].delay` | 장비 action 기본 시간 후보 |
| `steps[].wait_retry` | timeout 정책. 가공시간으로 직접 사용하지 않음 |

YAML `op_id`를 MES 라우팅 id로 직접 쓰면 YAML이 복잡해질 수 있다. 따라서 권장안은 별도 mapping 테이블 또는 mapping YAML을 두는 것이다.

예시:

```yaml
p4r_mapping:
  OP-B01:
    routing_id: 54
  OP-B02:
    routing_id: 55
    phase: setup
  OP-B03:
    routing_id: 55
    phase: machining
  OP-B04:
    routing_id: 56
```

이렇게 하면 기존 시나리오의 `OP-B01` 같은 실행 그룹 ID를 유지하면서 MES 라우팅과 연결할 수 있다.

## P4R 생성 흐름

1. `lot_no`로 `WorkOrder`를 조회한다.
2. `WorkOrder.product_id`로 `ProcessRouting` 목록을 조회한다.
3. 시나리오 YAML에서 `assets`, `op_id`, `p4r_process_mapping`, step action을 읽는다.
4. AASX에서 resource type, capacity, `P4RActionTimingProfile`, gateway raw status를 읽는다.
5. 매핑이 없는 라우팅은 `cycle_time_sec -> std_process.cycle_time_sec -> 0` 순서로 `PROCESSING_TIME`을 채운다.
6. 매핑이 있는 라우팅은 `time_mode`에 따라 action profile 합계 또는 routing cycle time + action profile 합계로 `PROCESSING_TIME`을 계산한다.
7. 계산 근거와 제외 action은 wrapper의 `sources.p4r_processing_time.items`에 trace로 남긴다.
8. `MACHINE_INSTANCE.FAILURE_STATUS`는 JSON failure rule로 raw 상태/메시지를 해석해 채운다.
9. FEEDER는 `schedulerInfo.loaderSlots/unloaderSlots`로 투입/회수 `BUFFER_TYPE`을 만들고, `RobotGateway.Status.loaderCount/unloaderCount`로 현재 수량을 채운다.
10. `MACHINE_INSTANCE.WORK_IN_PROCESS_STATUS[].PROCESSED_TIME`은 별도 operation runtime 매핑 단계에서 읽고 없으면 `"0"`으로 둔다.

## 생성 모드

### 시나리오 YAML이 있는 제품

YAML로 실제 자산/action 흐름을 보강한다. `p4r_process_mapping`이 있으면 해당 라우팅만 action profile 계산을 적용한다.

Cell1:

| 라우팅 | YAML group | P4R operation | PROCESSING_TIME |
| --- | --- | --- | --- |
| `LOAD` | `OP-B01` | `POI_PLAT-A002_54` | action profile 합계 |
| `MILL` | `OP-B02` + `OP-B03` | `POI_PLAT-A002_55` | `process_routings[55].cycle_time_sec` + action profile 합계 |
| `UNLOAD` | `OP-B04` | `POI_PLAT-A002_56` | action profile 합계 |

### 시나리오 YAML이 없는 제품

현재 정책에서는 작업지시에 시나리오가 없으면 P4R preview를 생성하지 않고 에러로 돌려준다. 시나리오는 P4R 자산 선택과 action trace의 기준이기 때문이다.

| 항목 | 생성 방식 |
| --- | --- |
| 상태 | 처리 |
| --- | --- |
| `WorkOrder.scenario` 없음 | 에러 |
| scenario 파일 읽기 실패 | warning 후 빈 scenario 기준으로 진행하되 자산 매칭 warning 발생 |
| scenario 있음, `p4r_process_mapping` 없음 | 기존처럼 라우팅 cycle time 사용 |

## Cell1 예상 P4R PROCESS_INFO

현재 DB 기준 기본값은 다음과 같다. NC 파일 분석 전에는 표준공정에서 복사된 값과 동일하다.

```json
[
  {
    "PROCESS_INFO_ID": "PI_PLAT-A002_CELL1",
    "PROCESS_OPERATION_INFO": [
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_54",
        "PROCESS_TYPE": "LOAD",
        "MACHINE_TYPE_ID": "ROBOT",
        "PROCESSING_TIME": "30",
        "PROC_NUM": "1"
      },
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_55",
        "PROCESS_TYPE": "MILL",
        "MACHINE_TYPE_ID": "CNC",
        "PROCESSING_TIME": "120",
        "PROC_NUM": "1"
      },
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_56",
        "PROCESS_TYPE": "UNLOAD",
        "MACHINE_TYPE_ID": "AMR",
        "PROCESSING_TIME": "45",
        "PROC_NUM": "1"
      }
    ]
  }
]
```

NC 파일 분석 후 예시는 다음처럼 바뀐다.

```json
[
  {
    "PROCESS_INFO_ID": "PI_PLAT-A002_CELL1",
    "PROCESS_OPERATION_INFO": [
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_54",
        "PROCESS_TYPE": "LOAD",
        "PROCESSING_TIME": "30"
      },
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_55",
        "PROCESS_TYPE": "MILL",
        "PROCESSING_TIME": "417"
      },
      {
        "PROCESS_OPERATION_INFO_ID": "POI_PLAT-A002_56",
        "PROCESS_TYPE": "UNLOAD",
        "PROCESSING_TIME": "45"
      }
    ]
  }
]
```

여기서 417초는 예시값이며, `process_routing_files`의 NC 파일 분석 결과와 공정 내부 action timing을 합산해 `process_routings.cycle_time_sec`에 반영한 값이다.

Cell1 `MILL` 라우팅의 최종 cycle time은 NC 파일 시간만으로 제한하지 않는다. CNC door/vise 동작, UR의 CNC 내부 소재 투입/제품 반출처럼 `MILL` 공정 중 CNC를 점유하는 작업은 `PROCESS_INTERNAL` timing component로 포함할 수 있다. 반대로 ANT AMR의 설비 간 이동과 같은 물류성 시간은 `MATERIAL_HANDLING_INFO`로 분리하는 것이 기본 정책이다.

## 기존 P4R API와 달라지는 점

| 항목 | 기존 | 개선 후 |
| --- | --- | --- |
| process time 출처 | `std_processes.cycle_time_sec` | `process_routings.cycle_time_sec` 우선 |
| 제품별 시간 차이 | 표현 어려움 | 같은 `MILL`이어도 제품/라우팅별 시간 분리 |
| NC 파일 반영 | 없음 | 파일 분석 후 라우팅 cycle time 업데이트 |
| 한 라우팅 다중 NC | 없음 | aggregation 정책으로 계산 |
| YAML 의존성 | 일부 process 정보 보강 | YAML은 action/resource 보강, 시간은 MES 기준 |
| AAS timing | 없음 또는 고정 machining 후보 | 장비 고유 action timing을 라우팅 시간 산정 근거로 사용 |
| failure status | 기본값 `"0"`/`NONE` | 미들웨어/AAS raw status와 unit alarm을 JSON failure rule로 정규화 |
| `PROCESSED_TIME` | 기본 `"0"` | 현재 operation 진행시간 |
| handling/process 경계 | 미정 | 설비 간 이송은 `MATERIAL_HANDLING_INFO`, 공정 내부 tending은 라우팅 `PROCESSING_TIME` 후보 |

## 구현 대상 코드

| 파일 | 변경 내용 |
| --- | --- |
| `src/app/models/master.py` | `ProcessRouting`, `ProcessRoutingFile` 컬럼 추가 |
| migration 파일 | DB 컬럼 추가 및 기존 라우팅 backfill |
| routing 생성/수정 API | `cycle_time_sec` 입력/수정 지원 |
| NC 파일 업로드 API | 분석 상태/예상시간 저장 |
| NC analyzer service | 파일별 예상 가공시간 계산 |
| `p4r_adapter.py` | `PROCESSING_TIME` 출처를 라우팅 cycle time으로 변경, JSON failure rule 적용 |
| `config/p4r_failure_rules.json` | P4R failure type/repair time 매칭 rule 관리 |
| failure rule loader | JSON rule 로딩, schema 검증, fallback 제공 |
| `aas_view_client.py` | AAS raw status, schedulerInfo, `P4RActionTimingProfile` 조회 |
| `scenario_asset_parser.py` | YAML op_id/action mapping 보강 |
| timing classifier | action을 `PROCESS_INTERNAL`, `MATERIAL_HANDLING`, `STATE_CHECK`, `TRIGGER`로 분류 |
| 테스트 | fallback, NC 분석, 다중 파일, YAML 없음 케이스 |

## 단계별 구현 계획

### 0단계: AASX action timing 선반영

Cell1 장비 5개(`NX5500`, `FEEDER`, `ANT_AMR`, `UR_ROBOT`, `CNC_DIE`) AASX에 `P4RActionTimingProfile`을 추가한다. YAML `p4r_process_mapping`이 있는 경우 P4R adapter가 이 값을 읽어 preview `PROCESSING_TIME` 산정에 사용한다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| Cell1 submodel 추가 | 5개 장비에 `P4RActionTimingProfile` reference와 submodel 생성 |
| command catalog 일치 | AASX command shortId와 action timing entry 매칭 |
| UR 동작 시간 등록 | `DETECT=10`, `PICK_SLOT/PICK/PLACE=15`, `GRIPPER_OPEN/CLOSE=2`, `HOME=15`, `CYCLE_START=20` |
| 시간 귀속 분류 | `PROCESS_INTERNAL`, `MATERIAL_HANDLING`, `TRIGGER`, `PROGRAM_SELECT`, `STATE_CHANGE` 등 분류 저장 |
| 영향 제한 | `p4r_process_mapping`이 있는 P4R preview에만 계산 영향 발생. MES sync, scheduler는 미변경 |

### 1단계: DB 스키마 확장

`process_routings`에 제품별 cycle time 컬럼을 추가한다. 기존 데이터는 `std_processes.cycle_time_sec`로 backfill한다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| DB migration 성공 | 기존 라우팅 row에 cycle time 채워짐 |
| ORM 반영 | `ProcessRouting.cycle_time_sec` 접근 가능 |
| breakdown 저장 | `cycle_time_breakdown`에 산정 근거 저장 가능 |
| fallback 유지 | 값이 비어도 기존 std_process 시간 사용 |

### 2단계: P4R Adapter 변경

`_build_process_info()`에서 mapping 유무에 따라 다음 우선순위로 계산한다.

```text
mapping 없음:
  routing.cycle_time_sec -> routing.std_process.cycle_time_sec -> 0

mapping 있음:
  ACTION_PROFILE = AAS action duration 합계
  ROUTING_CYCLE_PLUS_ACTION_PROFILE = routing/std cycle time + AAS action duration 합계
```

완료 기준:

| 체크 | 내용 |
| --- | --- |
| 기존 API 응답 유지 | `preview` schema 깨지지 않음 |
| Cell1 PROCESSING_TIME | mapping 기준으로 LOAD/UNLOAD는 action profile 합계, MILL은 routing cycle + action profile 합계 생성 |
| 라우팅 시간 수정 시 | P4R 응답 즉시 변경 |

### 3단계: NC 파일 분석 메타데이터 추가

`process_routing_files`에 분석 결과 컬럼을 추가하고 파일 업로드/등록 흐름에서 분석 상태를 저장한다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| 파일 row 저장 | role, sequence, 분석 상태 저장 |
| 분석 성공 | `estimated_cycle_time_sec` 저장 |
| 분석 실패 | `analysis_status=FAILED`, error 저장 |

### 4단계: 라우팅 cycle time 재계산

NC 파일 분석이 끝나면 라우팅의 최종 cycle time을 업데이트한다.

계산 우선순위:

```text
manual override가 있으면 유지
아니면 aggregation 정책으로 NC 파일 시간 계산
필요하면 공정 내부 setup/tending action timing을 더하고 breakdown에 기록
분석 가능한 파일이 없으면 기존 routing cycle time 유지
```

완료 기준:

| 체크 | 내용 |
| --- | --- |
| 단일 NC | 파일 시간으로 routing time 업데이트 |
| 다중 NC | `SUM_FILES` 합산 |
| 공정 내부 action | door/vise/UR CNC tending 같은 구성요소를 라우팅 시간에 반영 가능 |
| 대체 파일 | 합산 제외 가능 |
| P4R 연동 | 업데이트된 routing time이 PROCESSING_TIME에 반영 |

### 5단계: MES 기반 failure status 정규화

미들웨어/AAS raw status와 LOT/unit alarm 메시지를 MES P4R adapter가 해석해 `FAILURE_TYPE`, `REMAINING_REPAIR_TIME`을 만든다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| rule 분류 | `DISCONNECTED`, `NO_RESPONSE`, `CNC_ALARM`, `ROBOT_ERROR`, `PROCESS_TIMEOUT`, `RESOURCE_BLOCKED`, `UNKNOWN_ERROR`, `NONE` 분류 |
| rule 저장 | `P4R_FAILURE_RULES_PATH`의 JSON 파일에서 rule 로딩 |
| schema 검증 | 잘못된 rule 파일이면 기본 rule set으로 fallback하고 warning 반환 |
| repair time | failure type별 기본값 적용 |
| trace | raw message와 matched rule을 wrapper `sources`에 기록 |
| fallback | raw 상태가 없거나 정상일 때 `NONE`, `0` |
| WIP status | `PROCESS_OPERATION_INFO_ID`, `PROCESSED_TIME`은 별도 operation runtime 매핑 단계로 분리 |

### 6단계: AAS action timing profile 추가

AASX에 `P4RActionTimingProfile`을 추가하되 제품별 machining 시간은 넣지 않는다. 장비 고유 action 시간과 시간 귀속 후보를 넣고, 라우팅 cycle time 산정/검증에 사용할 수 있게 한다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| NX5500 door/vise | action timing 등록 |
| FEEDER load/unload | action timing 등록 |
| ANT AMR pick/place | 실측 전까지 TBD로 등록 |
| UR robot motion | `PICK`, `PLACE`, `DETECT`, `PICK_SLOT`, `CYCLE_START`, `HOME` 등 초기 duration 등록 |
| P4R 중복 방지 | 같은 시간을 `MATERIAL_HANDLING_INFO`와 `PROCESSING_TIME`에 중복 반영하지 않음 |

### 7단계: YAML 없는 제품 fallback

제품에 시나리오 YAML이 없어도 라우팅 기준으로 P4R JSON을 생성한다.

완료 기준:

| 체크 | 내용 |
| --- | --- |
| YAML 없음 | API 성공 |
| PROCESS_INFO | routing sequence 기준 생성 |
| source 표시 | wrapper `sources`에 `scenario_found=false` 표시 |

## 리스크와 결정 필요 사항

| 주제 | 결정 필요 |
| --- | --- |
| `LOAD`/`UNLOAD` 시간 정의 | MES 라우팅 시간과 AAS handling time 중 어떤 값을 P4R process time으로 볼지 |
| 로봇 동작 귀속 | 설비 간 이송은 handling, 공정 장비 내부 tending은 process time 후보로 분류 |
| NC 분석 정확도 | 초기에는 수동/간이 분석으로 시작할지 |
| 다중 NC aggregation | 기본 `SUM_FILES`로 충분한지 |
| manual override | 사용자가 입력한 시간을 NC 분석값이 덮어써도 되는지 |
| YAML op_id 매핑 | 별도 mapping table로 둘지 YAML 확장으로 둘지 |
| `PROCESS_OPERATION_INFO_ID` 규칙 | 라우팅 id 기반으로 확정할지 |

## 결론

최종 구조는 다음이 가장 자연스럽다.

```text
std_processes = 기본 템플릿
process_routings = 제품별 최종 공정 시간
process_routing_files = NC 파일별 분석 시간
AASX = 장비 고유 action timing + runtime 상태
P4R JSON = process_routings.cycle_time_sec 기준으로 생성
```

이렇게 하면 NC 파일이 없을 때는 표준공정 기본값으로 P4R JSON을 만들 수 있고, NC 파일과 공정 내부 action timing이 있으면 실제 제품/라우팅별 작업시간을 반영할 수 있다. 같은 `MILL` 표준공정을 여러 제품이 공유하거나 한 제품 안에서 여러 번 사용하더라도 각 라우팅 row가 독립 시간을 가지므로 P4R `PROCESSING_TIME`이 현실에 맞게 달라진다.

가장 중요한 경계는 로봇/handling 시간을 무조건 제외하지 않는다는 점이다. 설비 간 반송은 `MATERIAL_HANDLING_INFO`로, 공정 장비 내부에서 공정 완료를 위해 필요한 tending은 해당 라우팅의 `PROCESSING_TIME` 구성요소로 귀속한다.
