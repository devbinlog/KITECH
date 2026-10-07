# DT Project Product/Routing Integration Plan

작성일: 2026-06-26

## 1. 목적

MES 제품 마스터를 데이터 플랫폼의 DT Project와 연결하고, 라우팅 설계 화면에서 DT Project XML의 workplan 구조를 기준으로 DTP NC 파일을 선택/저장할 수 있게 한다.

핵심 목표는 다음과 같다.

- 제품 추가/수정 시 DTP의 DT Project를 조회하고 선택한다.
- 선택한 DT Project 정보를 MES 제품에 연결한다.
- DT Project XML의 `main_workplan` 및 하위 `workplan` 구조를 파싱한다.
- 라우팅 설계 화면에서 기존 기능을 유지한 채, DT Project가 연결된 제품에 한해 workplan 선택과 DTP NC 선택 기능을 추가한다.
- 선택한 DTP NC 파일은 기존 라우팅 파일 구조와 함께 저장되어야 한다.
- DTP 파일 다운로드는 MES 백엔드 프록시를 통해 처리한다.

## 2. 반드시 지켜야 할 UI/기능 원칙

라우팅 설계의 기존 기능은 제거하거나 단순화하면 안 된다.

기존 라우팅 row에서 유지해야 하는 항목:

- 순서
- 표준공정
- Setup ID
- 비고
- 공정 삭제
- 장비 후보 오버라이드
- `+ 파일 추가`
- 파일 타입 선택: `NC`, `IMAGE`, `DOC`
- 파일 경로 입력
- 로컬 파일 업로드
- 파일별 호환 장비 체크박스
- 파일 삭제
- 라우팅 저장
- 제품 목록 선택
- 저장 전 변경사항 표시

DT 기능은 기존 기능을 대체하지 않고 보강해야 한다.

권장 UI 원칙:

- DT Project가 연결되지 않은 제품은 기존 라우팅 설계 화면과 동일하게 동작한다.
- DT Project가 연결된 제품은 기존 라우팅 화면 상단에 DT Project 요약 패널을 추가한다.
- 각 라우팅 row의 파일 영역에 `DT Workplan` 선택과 `DTP NC 선택` 버튼을 추가한다.
- DTP NC를 선택하면 기존 파일 row 형태로 표시하되, `DTP` badge와 reference 정보를 함께 보여준다.
- 로컬 업로드와 DTP NC 선택은 동시에 공존해야 한다.

## 3. 확인된 DTP API와 데이터 특징

### 3.1 프로젝트 조회

프로젝트 목록:

```text
GET /openapi/v2/project?page=0&size=...
```

프로젝트 리비전 트리:

```text
GET /openapi/v2/project/tree?gid={assetGlobalId}&aid={assetId}
```

확인된 예시:

```text
Asset Global Id: https://digital-thread.re/kitech/kimm_project
Asset Id:        https://digital-thread.re/kitech/kimm_project/prj_001
Element Id:      milling_prj
UUID:            370
```

이 프로젝트는 `project/tree` 응답의 `workPlans` 배열이 비어 있었지만, `xmlStr` 내부에는 workplan 정보가 존재했다. 따라서 `project/tree.workPlans`만 신뢰하면 안 된다.

### 3.2 NC 파일 조회

NC 파일 조회는 다음 API가 안정적이었다.

```text
GET /openapi/v2/asset/find/ref?gid={assetGlobalId}&category=NC&page=0&size=100
```

중요: `gid`만으로 필터링하면 같은 global asset 아래의 다른 project revision 또는 다른 project asset의 NC도 함께 검색될 수 있다.

MES 백엔드는 DTP 응답의 `reflist.keys`를 기준으로 다시 필터링해야 한다.

필터 기준:

```text
DT_GLOBAL_ASSET = product.dt_project.asset_global_id
DT_ASSET        = product.dt_project.asset_id_short
DT_PROJECT      = product.dt_project.element_id
WORKPLAN        = selected_workplan_id
```

주의:

- `DT_ASSET` 값은 full asset id가 아니라 `prj_001`, `project_asset`처럼 short 값으로 내려올 수 있다.
- 따라서 `asset_id`와 별도로 `asset_id_short`를 저장하고 비교해야 한다.

### 3.3 파일 다운로드

DTP NC 파일은 `path`로 다운로드 가능했다.

```text
GET /openapi/v2/files/download/userdata?path={path}
```

확인된 예시:

```text
/userdata/3/merge.tap
/userdata/3/face1.tap
```

다운로드는 프론트에서 DTP를 직접 호출하지 않고 MES 백엔드가 프록시해야 한다.

## 4. Workplan 파싱 규칙

DT Project XML은 ISO14649 기반이며, 다음 구조를 고려해야 한다.

```text
dt_project
└─ main_workplan
   ├─ its_id = wp_001
   ├─ 직접 workingstep/operation/feature 데이터를 가질 수 있음
   └─ its_elements xsi:type="workplan"
      ├─ its_id = wp_002
      └─ 실제 workingstep/operation/feature 데이터를 가질 수 있음
   └─ its_elements xsi:type="workplan"
      ├─ its_id = wp_003
      └─ 실제 workingstep/operation/feature 데이터를 가질 수 있음
```

파싱 규칙:

- `main_workplan` 자체를 workplan 후보로 저장한다.
- `main_workplan > its_elements[xsi:type="workplan"]` 하위 workplan도 모두 저장한다.
- `main_workplan`에 직접 데이터가 있을 수 있다.
- 하위 workplan에 직접 데이터가 있을 수 있다.
- NC reference의 `WORKPLAN` 값은 main workplan 또는 하위 workplan 모두와 매칭될 수 있다.
- `project/tree.workPlans`는 보조 정보로만 사용하고, 최종 source of truth는 `xmlStr` 파싱 결과로 둔다.

## 5. DB 설계

추후 확장을 고려하면 Product 테이블에 DT 관련 컬럼을 직접 늘리는 방식보다 별도 참조 테이블을 두는 방식이 적합하다.

권장 관계:

```text
products
└─ product_dt_project_links
   └─ dt_project_refs
      └─ dt_project_workplans

process_routing_files
└─ dt_file_refs
```

### 5.1 `dt_project_refs`

DTP Project revision 하나를 MES에 캐시/참조하는 테이블.

권장 컬럼:

```text
id
platform                    -- DTP
external_project_id          -- DTP UUID 또는 numeric id
asset_global_id              -- gid
asset_id                     -- full aid
asset_id_short               -- prj_001, project_asset
element_id                   -- milling_prj
element_full_id
category                     -- Project
display_name
description
latest
root_project_id
parent_project_id
schema_version
xml_hash
xml_snapshot                 -- project tree xmlStr snapshot
raw_response                  -- JSON snapshot, optional
synced_at
created_at
updated_at
```

`xml_snapshot` 저장을 권장한다. 라우팅/NC 매핑의 기준이 XML이므로 DTP 원본이 변경되어도 제품 등록 당시 구조를 추적할 수 있어야 한다.

### 5.2 `product_dt_project_links`

제품과 DT Project의 연결 이력을 관리한다.

권장 컬럼:

```text
id
product_id
dt_project_ref_id
relation_type                -- PRIMARY, REFERENCE
is_current
linked_at
linked_by
unlinked_at
unlink_reason
created_at
```

제약:

- 제품 하나에는 `relation_type=PRIMARY`, `is_current=true` 연결이 최대 1개.
- 프로젝트를 변경하면 기존 link를 삭제하지 않고 `is_current=false`, `unlinked_at` 처리한다.
- 새 link를 생성하여 변경 이력을 남긴다.
- SQLite에서는 partial unique index를 사용해 `product_id + relation_type` 기준 current link가 하나만 존재하도록 보장한다.
- 다른 DB로 이전할 가능성을 고려해 application service에서도 current link 중복을 한 번 더 검사한다.

### 5.3 `dt_project_workplans`

DT Project XML에서 파싱한 workplan 목록.

권장 컬럼:

```text
id
dt_project_ref_id
workplan_id                  -- wp_001, wp_002, wp_003
parent_workplan_id
level                        -- 0: main_workplan, 1+: child workplan
sequence
display_name
source_path                  -- XML path 추적용
has_direct_steps
raw_fragment                 -- optional
is_active
deprecated_at
created_at
```

권장 unique key:

```text
dt_project_ref_id + workplan_id + source_path
```

재동기화 시 이 key로 upsert한다. 기존 라우팅이 참조 중인 workplan row는 hard delete하지 않는다.

### 5.4 `dt_file_refs`

DTP 파일, 특히 NC 파일 참조를 저장한다.

권장 컬럼:

```text
id
platform                     -- DTP
external_file_id             -- DTP AssetElement id
asset_global_id
asset_id
asset_id_short
element_id
category                     -- NC, STEP, VM 등
type                         -- file
display_name
content_type
path                         -- /userdata/...
reference_json               -- reflist.keys 전체
workplan_id
workingstep_id               -- 있으면 저장
download_available
synced_at
created_at
updated_at
```

### 5.5 `process_routing_files` 확장

기존 라우팅 파일 테이블은 유지하고 DTP 파일을 선택한 경우만 참조를 추가한다.

추가 권장 컬럼:

```text
source_type                  -- LOCAL_UPLOAD | DTP
dt_file_ref_id               -- nullable FK
```

기존 컬럼 사용:

```text
file_type                    -- NC
file_path                    -- local path 또는 DTP path
original_filename            -- DTP displayName 또는 업로드 원본명
compatible_machines
sort_order
```

이렇게 하면 기존 로컬 업로드 기능을 깨지 않고 DTP 파일 선택 기능을 추가할 수 있다.

### 5.6 `process_routings` 확장 여부

라우팅 row 자체에 workplan을 연결할 필요가 있다.

권장 컬럼:

```text
dt_workplan_id               -- nullable FK to dt_project_workplans
```

이 컬럼은 DT Project가 연결된 제품에서만 사용한다. 기존 제품의 라우팅은 `null`로 유지된다.

정책:

- `process_routings.dt_workplan_id`는 해당 라우팅 row의 기본/선택 workplan이다.
- `dt_file_refs.workplan_id`는 파일이 실제 참조하는 DTP workplan이다.
- 한 라우팅 row에 여러 DTP NC 파일을 허용하더라도 1차 구현에서는 모두 같은 workplan이어야 한다.
- 사용자가 다른 workplan의 NC를 선택하면 row의 `dt_workplan_id`를 해당 workplan으로 자동 변경하거나 확인 후 변경한다.
- 향후 한 row에서 여러 workplan 파일을 허용해야 하면 row-level `dt_workplan_id`는 기본값으로만 사용하고 file-level workplan을 기준으로 검증하도록 확장한다.

### 5.7 DT Project 미연결 제품 처리

DT Project 연결은 선택사항이어야 한다. MES에는 외부 DT Project 없이 운영되는 제품, 임시 제품, 수기 라우팅 제품이 계속 존재할 수 있다.

DB 무결성 원칙:

- `products` 테이블에는 DT Project FK를 직접 필수 컬럼으로 두지 않는다.
- DT Project가 연결되지 않은 제품은 `product_dt_project_links` row가 없어도 정상이다.
- 제품 조회 시 DT Project 정보는 left join 또는 별도 optional 조회로 처리한다.
- `process_routings.dt_workplan_id`는 nullable이어야 한다.
- `process_routing_files.dt_file_ref_id`는 nullable이어야 한다.
- `process_routing_files.source_type`은 기존 데이터 호환을 위해 기본값을 `LOCAL_UPLOAD`로 둔다.
- `dt_project_refs`, `dt_project_workplans`, `dt_file_refs`는 DT 기능을 사용하는 제품/라우팅에서만 생성된다.

이 설계에서는 DT Project 없이 제품을 생성해도 릴레이션 문제가 생기지 않는다. 오히려 Product 테이블에 `dt_project_id NOT NULL` 같은 직접 필수 FK를 두는 방식이 기존 데이터와 운영 흐름을 깨뜨릴 위험이 크다.

권장 조회 규칙:

```text
Product
  current_dt_project: null | DtProjectSummary
  dt_workplans: []
```

DT Project가 없는 제품에서 DTP NC 조회 API를 호출하면 `404`보다는 `409 Conflict` 또는 빈 목록과 명확한 메시지를 반환하는 것이 좋다.

권장 응답:

```json
{
  "items": [],
  "message": "DT Project가 연결되지 않은 제품입니다."
}
```

## 6. 백엔드 API 설계

프론트는 DTP API를 직접 호출하지 않는다. DTP API key 보호, 응답 정규화, XML 파싱, reference 필터링은 MES 백엔드가 담당한다.

### 6.1 설정

환경변수:

```text
DTP_BASE_URL=https://dthread.nexmoa.com
DTP_API_KEY=...
DTP_AUTH_HEADER=Authorization
```

API key는 저장소, 프론트 번들, 브라우저 localStorage에 절대 노출하지 않는다.

### 6.2 DTP Project 조회

```text
GET /api/v1/integrations/dtp/projects?query=&page=0&size=20
```

역할:

- DTP `/openapi/v2/project` 호출
- MES 프론트에서 쓰기 쉬운 DTO로 변환
- `assetGlobalId`, `assetId`, `elementId`, `displayName`, `latest`, `id` 반환

### 6.3 DTP Project 상세/트리 조회

```text
GET /api/v1/integrations/dtp/projects/tree?gid={gid}&aid={aid}
```

역할:

- DTP `/openapi/v2/project/tree` 호출
- `xmlStr` 포함 응답 수신
- `main_workplan` 및 하위 workplan 파싱
- 프로젝트 상세와 workplan preview 반환

### 6.4 제품에 DT Project 연결

제품 생성 시 DT Project 연결은 선택사항이다. 기존처럼 DT Project 없이도 제품을 생성할 수 있어야 한다.

```text
POST /api/v1/masters/products
```

기존 방식 payload:

```json
{
  "code": "PART-A100",
  "name": "알루미늄 브라켓 A형",
  "unit": "EA",
  "product_category": "BRACKET"
}
```

DT Project를 함께 연결하는 확장 payload:

```json
{
  "code": "KIMM-DT-001",
  "name": "KIMM 밀링 프로젝트 제품",
  "unit": "EA",
  "product_category": "PLATE",
  "dt_project": {
    "asset_global_id": "https://digital-thread.re/kitech/kimm_project",
    "asset_id": "https://digital-thread.re/kitech/kimm_project/prj_001",
    "external_project_id": "370"
  }
}
```

처리 규칙:

- `dt_project`가 없으면 기존 제품 생성 로직만 수행한다.
- `dt_project`가 있으면 DTP project tree를 먼저 조회/검증한 뒤, 짧은 DB 트랜잭션 안에서 `products`, `dt_project_refs`, `dt_project_workplans`, `product_dt_project_links`를 저장한다.
- DTP 연동 실패 시 제품 생성까지 함께 실패시킬지, 제품은 생성하고 DT 연결만 실패 처리할지는 정책을 정해야 한다.
- 권장 1차 구현은 명시적으로 DT Project를 선택한 경우 DTP 연동 실패 시 전체 생성 실패로 처리한다. 사용자는 DT 선택을 해제하고 일반 제품으로 다시 저장할 수 있다.

기존 제품에 연결/변경:

```text
PATCH /api/v1/masters/products/{product_id}/dt-project
```

역할:

- DTP project tree 조회
- `dt_project_refs` upsert
- `dt_project_workplans` upsert
- 기존 current link 종료
- 새 `product_dt_project_links` 생성

주의:

- 외부 DTP API 호출을 DB 트랜잭션 내부에서 오래 수행하면 lock 시간이 늘어난다. DTP 조회와 XML 파싱은 트랜잭션 밖에서 먼저 수행하고, DB 저장만 트랜잭션으로 묶는다.
- `dt_project_workplans`는 삭제 후 재생성하면 기존 `process_routings.dt_workplan_id` FK가 깨질 수 있다. 반드시 stable key 기반 upsert를 사용하고, 사라진 workplan은 hard delete보다 `is_active=false` 또는 `deprecated_at` 처리한다.
- 제품의 current DT Project를 변경할 때 기존 라우팅이 이전 DT Project의 DTP NC 파일을 참조하고 있으면 변경을 막거나 영향 분석 확인 모달을 띄운다.

### 6.5 제품의 DT Project 조회

```text
GET /api/v1/masters/products/{product_id}/dt-project
```

반환:

- current DT project
- parsed workplans
- link metadata

### 6.6 제품 기준 DTP NC 조회

```text
GET /api/v1/masters/products/{product_id}/dt-nc-files?workplan_id=wp_002
```

역할:

- 제품 current DT project 조회
- DTP `/openapi/v2/asset/find/ref?gid=...&category=NC` 호출
- `DT_GLOBAL_ASSET`, `DT_ASSET`, `DT_PROJECT`, `WORKPLAN` 기준 필터링
- `dt_file_refs` upsert 가능
- workplan별 NC 목록 반환

### 6.7 DTP 파일 다운로드 프록시

기존 다운로드 API를 확장하거나 별도 API를 둔다.

권장:

```text
GET /api/v1/masters/files/{file_id}/download
```

동작:

- `source_type=LOCAL_UPLOAD`: 기존 MES 업로드 파일 다운로드
- `source_type=DTP`: `dt_file_refs.path`로 DTP `/openapi/v2/files/download/userdata` 호출 후 스트리밍 반환

## 7. 프론트엔드 구현 계획

### 7.1 제품 관리 화면

현재 화면:

- 제품 목록 테이블
- 제품 추가/수정 모달
- 제품 코드, 제품명, 카테고리, 단위

제품 등록 화면은 새 화면으로 교체하지 않는다. 기존 제품 추가/수정 모달을 유지하고, 하단 또는 중간에 `DT 프로젝트 연결` 선택 섹션을 추가한다.

기본 원칙:

- 기본 상태는 `DT Project 미연결`이다.
- 사용자가 `DT 프로젝트 조회`를 누르기 전까지 기존 제품 등록과 동일한 흐름이다.
- DT Project 선택 없이 `저장`을 눌러도 제품 등록은 성공해야 한다.
- DT Project 선택 후에도 `연결 해제`를 누르면 다시 일반 제품으로 저장할 수 있어야 한다.
- 제품 수정 화면에서는 현재 연결된 DT Project가 있으면 요약을 보여주고, 없으면 `미연결` 상태를 보여준다.

기존 제품 추가 모달 유지 항목:

```text
제품 코드 *
제품명 *
제품 카테고리
단위
```

추가 섹션:

- 제품 추가/수정 모달에 `DT 프로젝트` 영역 추가
- `프로젝트 조회` 버튼
- 선택된 프로젝트 요약 표시
- workplan preview 표시

권장 배치:

```text
제품 추가
────────────────────────────────
제품 코드 *
[PROD-001                         ]

제품명 *
[브라켓 A                         ]

제품 카테고리
[선택 안함 ▼]

단위
[EA (개) ▼]

DT 프로젝트 연결                  선택사항
┌────────────────────────────────┐
│ 연결된 DT Project가 없습니다.   │
│ [DT 프로젝트 조회]              │
└────────────────────────────────┘

[취소] [저장]
```

프로젝트 선택 전 상태:

```text
DT 프로젝트 연결        선택사항
연결된 DT Project가 없습니다.
[DT 프로젝트 조회]
```

프로젝트 선택 후 상태:

```text
DT 프로젝트 연결        선택사항
KIMM Project
UUID: 370
Asset Global Id: ...
Asset Id: ...
Element Id: milling_prj
Workplan: wp_001, wp_002, wp_003
[변경] [연결 해제]
```

제품 수정 화면:

```text
제품 수정
────────────────────────────────
제품 코드 *     [KIMM-DT-001]  disabled
제품명 *        [KIMM 밀링 프로젝트 제품]
제품 카테고리   [플레이트 ▼]
단위            [EA (개) ▼]

DT 프로젝트 연결
┌────────────────────────────────┐
│ KIMM Project                   │
│ milling_prj / prj_001          │
│ workplan 3개                   │
│ [변경] [연결 해제]             │
└────────────────────────────────┘

[취소] [저장]
```

`연결 해제` 정책:

- 신규 제품 생성 중 연결 해제: 선택된 DT Project만 form state에서 제거한다.
- 기존 제품 수정 중 연결 해제: 저장 시 current link를 종료한다.
- 연결 해제해도 기존 라우팅의 DTP 파일을 어떻게 처리할지는 별도 확인이 필요하다.
- 1차 구현에서는 DTP 파일이 저장된 라우팅이 있으면 연결 해제를 막고 안내한다.

안내 메시지:

```text
이 제품의 라우팅에 DTP NC 파일이 사용 중입니다.
먼저 라우팅에서 DTP 파일을 제거하거나 로컬 파일로 변경한 뒤 연결을 해제하세요.
```

제품 목록 테이블 추가 컬럼:

```text
DT 프로젝트
Workplan
상태
```

예시:

```text
KIMM Project / 3개 / 연결됨
- / - / 미연결
```

### 7.2 DT Project 조회 모달

기능:

- 검색어 입력
- DTP project 목록 조회
- 프로젝트 선택
- 선택 프로젝트 상세 preview
- workplan 구조 preview
- NC 매핑 preview

목록 컬럼:

```text
프로젝트명
Element Id
Asset Id
Latest
선택
```

상세 preview:

```text
UUID
Asset Global Id
Asset Id
Element Id
Category
Latest
Workplan 구조
NC 매핑 미리보기
```

### 7.3 라우팅 설계 화면

현재 화면의 구조와 기존 기능을 유지한다.

추가:

- 선택 제품 상단에 DT Project 요약 패널 표시
- DT Project 연결 제품인 경우에만 workplan chips 표시
- `DT 공정 불러오기` 버튼은 선택 기능으로 둔다. 자동으로 기존 라우팅을 덮어쓰면 안 된다.

라우팅 row 변경 원칙:

- 기존 1행 구조 유지:

```text
순서 | 표준공정 | Setup ID | 비고 | 삭제
```

- 기존 2행 장비 후보 오버라이드 유지:

```text
장비 후보 오버라이드 (비워두면 표준공정 기본값)
[ ] AMR [ ] RACK [ ] VMC_3AXIS_MASS [ ] VMC_3AXIS_PALLET
```

- 기존 파일 영역 유지:

```text
파일 + 파일 추가
NC | /uploads/nc/... | 원본파일명 | 업로드 | 호환 장비 | 삭제
```

- DT 기능은 파일 영역에 추가:

```text
파일 + 파일 추가                         DT Workplan [wp_002 ▼] [DTP NC 선택]
NC | /userdata/3/merge.tap | merge.tap | DTP | 업로드 | 호환 장비 | 다운로드 | 삭제
reference: DT_ASSET=prj_001, DT_PROJECT=milling_prj, WORKPLAN=wp_002
```

### 7.4 DTP NC 선택 모달

라우팅 row의 `DTP NC 선택` 클릭 시 표시한다.

기능:

- 현재 row의 selected workplan을 상단에 표시
- `DTP 파일` / `로컬 업로드` 탭 표시
- workplan별 NC 파일 그룹 표시
- main workplan과 하위 workplan 모두 표시
- 선택 시 해당 row의 파일 목록에 DTP NC 추가

표시 예:

```text
wp_001 Main Workplan
  이 workplan에 매핑된 NC 파일이 없습니다.

wp_002 Face milling
  merge.tap / nc_001_1 / /userdata/3/merge.tap

wp_003 Finish milling
  face1.tap / nc_001_2 / /userdata/3/face1.tap
```

선택 규칙:

- row의 `DT Workplan`과 같은 workplan의 NC를 우선 보여준다.
- 다른 workplan의 NC도 보이게 할 수 있지만, 선택 시 row의 workplan을 해당 NC의 `WORKPLAN`으로 변경할지 확인해야 한다.
- 첫 구현에서는 선택한 NC의 workplan으로 row workplan을 자동 동기화한다.

## 8. 구현 순서

### Phase 1. 백엔드 DTP 클라이언트와 XML 파서

작업:

- DTP HTTP client 추가
- Project list/tree 조회
- NC list 조회
- userdata download 호출
- DT Project XML workplan parser 추가

수용 기준:

- `kimm_project/prj_001/milling_prj` 프로젝트 tree 조회 가능
- XML에서 `wp_001`, `wp_002`, `wp_003` 파싱 가능
- `category=NC` 조회 후 `prj_001/milling_prj` 기준 NC 2개 필터링 가능
- `/userdata/3/merge.tap`, `/userdata/3/face1.tap` 다운로드 프록시 가능

### Phase 2. DB migration

작업:

- `dt_project_refs`
- `product_dt_project_links`
- `dt_project_workplans`
- `dt_file_refs`
- `process_routings.dt_workplan_id`
- `process_routing_files.source_type`
- `process_routing_files.dt_file_ref_id`

수용 기준:

- 기존 제품/라우팅 데이터 유지
- 기존 로컬 파일 라우팅 동작 유지
- DT 연결 없는 제품의 모든 필드는 nullable 처리
- 기존 `process_routing_files` row는 migration 시 `source_type=LOCAL_UPLOAD`로 backfill
- 기존 API 응답을 사용하는 프론트/테스트가 깨지지 않도록 신규 필드는 optional 또는 기본값 포함
- current DT Project link 중복을 막는 DB index와 service-level 검증 추가

### Phase 3. Product API 확장

작업:

- 제품 생성 시 DT Project 연결 옵션 추가
- 기존 제품에 DT Project 연결/변경 API 추가
- 제품 조회 응답에 current DT Project summary 포함

수용 기준:

- DT Project 없이 제품 생성 가능
- DT Project와 함께 제품 생성 가능
- 프로젝트 변경 시 기존 link 이력 보존
- DT Project 연결 실패 시 제품 생성 실패/일반 제품 저장 중 어떤 정책인지 에러 메시지로 명확히 표시
- 기존 `POST /products` payload는 수정 없이 계속 동작

### Phase 4. Routing API 확장

작업:

- 라우팅 저장 payload에 `dt_workplan_id` 추가
- routing file payload에 `source_type`, `dt_file_ref_id` 추가
- 제품 기준 DTP NC 조회 API 추가
- 기존 file download API에서 DTP proxy 분기 추가

수용 기준:

- 기존 라우팅 저장 payload가 계속 동작
- DTP NC 파일을 기존 files 배열에 함께 저장 가능
- 로컬 업로드와 DTP 파일이 동일 라우팅에서 공존 가능
- `dt_workplan_id`가 없거나 `source_type`이 없던 기존 payload는 기존 로컬 라우팅으로 처리
- DTP 파일의 workplan과 라우팅 row의 workplan이 다르면 저장 전 검증 또는 자동 동기화
- DT Project 변경/연결 해제 시 기존 DTP routing file 참조에 대한 영향 검증 수행

### Phase 5. 제품 관리 UI

작업:

- 제품 추가/수정 모달에 DT Project 영역 추가
- DT Project 조회 모달 추가
- 제품 목록에 DT Project 연결 상태 표시

수용 기준:

- 기존 제품 입력 항목 유지
- DTP Project 검색/선택 가능
- 선택한 프로젝트의 workplan preview 표시
- DT Project 선택 없이 저장 가능
- DT Project 섹션은 선택사항으로 표시
- 기존 제품 수정 화면에서 DT Project가 없어도 오류 없이 표시

### Phase 6. 라우팅 설계 UI

작업:

- 기존 라우팅 설계 화면 유지
- DT Project 요약 패널 추가
- 파일 영역에 `DT Workplan` 선택 추가
- `DTP NC 선택` 모달 추가
- 선택한 DTP NC를 기존 파일 row 형태로 표시

수용 기준:

- Setup ID, 장비 후보 오버라이드, 로컬 업로드, 호환 장비 체크박스가 그대로 동작
- DT Project 연결 제품에서만 DTP NC 선택 가능
- DT Project 미연결 제품은 기존 UI와 동일
- DTP NC 선택 후 라우팅 저장 가능

## 9. 테스트 계획

### 9.1 백엔드 단위 테스트

- DTP Project DTO normalization
- XML workplan parser
- `main_workplan` 직접 데이터 케이스
- 하위 `its_elements[xsi:type="workplan"]` 케이스
- NC reference filtering
- `DT_ASSET` short/full normalization
- DTP download proxy

### 9.2 백엔드 API 테스트

- 제품 생성 without DT Project
- 제품 생성 with DT Project
- 제품 DT Project 변경 이력
- 제품 기준 NC 목록 조회
- 라우팅 저장 with local upload file
- 라우팅 저장 with DTP NC file
- DTP file download

### 9.3 프론트 테스트

- 제품 모달에서 DT Project 선택
- 제품 목록의 DT 연결 상태 표시
- 라우팅 화면 기존 필드 유지
- DTP NC 선택 후 file row 반영
- workplan 변경 시 선택 NC 초기화 또는 경고

### 9.4 수동 검증 시나리오

1. 제품 추가 화면 진입
2. DTP Project 조회
3. `KIMM Project / 370` 선택
4. 제품 저장
5. 라우팅 설계 화면 진입
6. 제품 선택
7. 기존 라우팅 field 확인: Setup ID, 장비 후보, 파일 추가, 업로드
8. Workplan `wp_002` 선택
9. DTP NC `merge.tap` 선택
10. Workplan `wp_003` 선택
11. DTP NC `face1.tap` 선택
12. 라우팅 저장
13. 파일 다운로드 확인

## 10. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| `project/tree.workPlans`가 비어 있음 | workplan UI 누락 | `xmlStr` parser를 source of truth로 사용 |
| `DT_ASSET` 값이 full aid가 아닐 수 있음 | NC 필터링 실패 | `asset_id_short` 저장 및 비교 |
| 같은 gid에 다른 project revision NC가 섞임 | 잘못된 NC 선택 | `DT_GLOBAL_ASSET + DT_ASSET + DT_PROJECT + WORKPLAN` 모두 비교 |
| DTP 파일 path 누락 | 다운로드 실패 | `download_available=false` 표시, 선택 제한 |
| 기존 라우팅 UI 훼손 | 운영 기능 회귀 | 기존 row 구조 보존을 acceptance criteria로 고정 |
| DTP API key 노출 | 보안 사고 | 백엔드 env only, 프론트 직접 호출 금지 |
| 프로젝트 리비전 변경 | 재현성 저하 | 선택 당시 project ref/xml snapshot 저장 |

## 11. 최종 구현 원칙

- Product는 MES 제품 마스터로 유지한다.
- DT Project는 별도 참조 테이블에 저장한다.
- 제품과 DT Project 연결은 이력형 link 테이블로 관리한다.
- Workplan은 DTP XML snapshot에서 파싱해 저장한다.
- NC 파일은 DTP file ref로 저장하고 기존 routing file에서 참조한다.
- 기존 라우팅 기능은 절대 제거하지 않는다.
- DTP 기능은 기존 local upload 기능과 공존해야 한다.
- 프론트는 DTP API key를 알면 안 된다.
- 다운로드는 MES backend proxy를 통해 수행한다.
