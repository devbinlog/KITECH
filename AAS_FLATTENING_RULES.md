# AAS `schedulerInfo` → `spec_data` 평탄화 규칙

AAS의 `idShort == "schedulerInfo"` submodel(설비 1대)을 중첩 JSON으로 평탄화해
cell-mes `equipments.spec_data`에 저장한다. **원본 계층 구조를 보존**한다.

## 규칙

**규칙 1 — Property → `idShort: value`** (`valueType`로 형변환)
- `xs:int/integer`→int · `xs:double/float/decimal`→float · `xs:boolean`→bool · 그 외→str (시간 `"08:00"`도 str)

**규칙 2 — `SubmodelElementList` → 항상 배열 `[]`**

**규칙 3 — `SubmodelElementCollection` → 기본은 중첩 객체 `{}`**, 단 아래면 배열 `[]`
- (a) idShort가 `breaks` / `accessibleMachines` (= `LIST_KEYS`), **또는**
- (b) 모든 자식 idShort가 `^.*_\d+$` 패턴(`break_0`, `machine_2` …) → 키 버리고 값만 모음

**규칙 4 — AAS 메타데이터 폐기** (`valueType`/`semanticId`/`description`/`modelType`/`qualifiers`). `idShort`(→key)·`value`만 남김

**규칙 5 — 빈 컬렉션**: 자식이 없으면 규칙 3(b) 불가 → `LIST_KEYS`로만 list 결정. 따라서 **빈 `breaks`는 `[]`** (not `{}`)

## 엣지케이스
- `breaks` → `[{start,end}, …]` · `accessibleMachines` → `[url, …]` · `capacityByType` → `{타입:수량}`
- AMR은 `calendar`/`machineTypeParams` 없을 수 있음 → 소비처에서 key 부재 허용
- `currentSetupId: ""` 빈 문자열도 보존
- ⚠️ `machineTypeParams`는 **중첩 유지** (최상위로 끌어올리지 말 것 — projector가 `machineTypeParams.{loadingType,amrTransportQty}`로 읽음)

## 참조 구현

```python
import re

LIST_KEYS = {"breaks", "accessibleMachines"}
SEQ = re.compile(r"^(.*)_(\d+)$")

def cast(v, vt):
    if v is None: return None
    if vt in ("xs:int", "xs:integer"): return int(v)
    if vt in ("xs:double", "xs:float", "xs:decimal"): return float(v)
    if vt == "xs:boolean": return str(v).lower() in ("true", "1")
    return v

def parse(el):
    mt, ids = el.get("modelType"), el.get("idShort")
    if mt == "Property":
        return cast(el.get("value"), el.get("valueType"))
    if mt == "SubmodelElementList":
        return [parse(c) for c in el.get("value", [])]
    if mt == "SubmodelElementCollection":
        ch = el.get("value", [])
        is_list = ids in LIST_KEYS or (ch and all(SEQ.match(c.get("idShort", "")) for c in ch))
        return [parse(c) for c in ch] if is_list else {c.get("idShort"): parse(c) for c in ch}
    return el.get("value")

def flatten_scheduler_info(sm):            # sm = schedulerInfo submodel
    return {el.get("idShort"): parse(el) for el in sm.get("submodelElements", [])}
```

## 출력 예시 (VMC_3AXIS_MASS)

```json
{
  "machineType": "VMC_3AXIS_MASS",
  "status": "available",
  "setupChangeTimeMin": 15,
  "currentSetupId": "TS-MASS-001",
  "machineTypeParams": {
    "loadingType": "buffer_exchange", "amrTransportQty": 3,
    "exchangeTimeSec": 45, "loadUnloadTimeSec": 0
  },
  "buffer": { "totalSlots": 6, "materialSlots": 3, "finishedSlots": 3 },
  "calendar": {
    "shiftStart": "08:00", "shiftEnd": "20:00",
    "breaks": [ { "start": "12:00", "end": "13:00" } ]
  }
}
```

> 검증: 위 참조 구현은 `samples/cell-scheduler/input/aas_revised.json`의 4개 설비(MASS/AMR/PALLET/RACK)에 대해
> 형변환·중첩·list/dict·메타데이터 폐기 및 DB 저장값 일치까지 26개 단언 전부 통과.
