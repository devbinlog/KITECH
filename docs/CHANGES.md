# Agents Workspace 변경 이력 및 운영 가이드

이 문서는 현재 workspace에서 구현된 주요 변경 사항과 운영 방법을 한 곳에서 파악하기 위한 문서이다.

특히 2026-09-04에 추가한 MES Interface DB는 외부 APS 연동의 기준 시스템이므로, 신규 담당자는 이 문서와 아래 문서를 함께 확인한다.

- `agents/mes-interface-db/APS_ACCESS_GUIDE.md`: APS 업체에 전달할 접속 및 View 명세
- `agents/mes-interface-sync/README.md`: sync worker 실행 및 매핑 설정
- `agents/mes-interface-sync/config/interface_views.yaml`: APS View 컬럼 계약
- `agents/cell-mes/docs/mes-interface-db-architecture-plan.md`: 설계 검토와 구현 계획
- `docs/mes-interface-db-implementation-report.html`: PPT 보고서용 HTML
- `agents/cell-mes/docs/CHANGES.md`: Cell-MES 세부 변경 이력

---

## 2026-09-29 - 제품 허용 Cell과 라우팅별 사이클 타임

- 라우팅 설계 화면(`/master/routings`)에서 제품을 선택하고 허용 Cell을 복수 지정한 뒤 `Cell 저장`한다. 빈 목록은 미설정이며 전체 Cell 허용이 아니다.
- 새 관계 테이블 `product_cells(product_id, cell_id)`와 Alembic `012` 추가. 라우팅 revision 기능 및 기존 시간 컬럼 추가는 없음.
- 각 공정에 `표준시간 사용` 또는 `직접 입력` 추가. 모든 시간은 정수 초. 직접 입력값(0 포함)을 우선하고 NULL이면 표준공정 시간을 참조한다.
- Cell 연결과 라우팅은 별도 저장한다. 라우팅 전체 교체로 제품 Cell 연결이 삭제되지 않는다.
- 기존 저장 시간은 보존한다. 이전 데이터가 표준시간에서 복사된 값이라도 자동으로 NULL로 바꾸지 않는다.
- 새 테이블은 다음 성공한 동기화에서 `mes_if.if_product_cells` 자동 View로 제공된다. 기존 동기화 YAML 수정 불필요.
- APS 조회 SQL 및 시간 적용 규칙은 `agents/mes-interface-db/APS_ACCESS_GUIDE.md` 8절에 추가.
- 내부 스케줄러의 공정 시간 조회도 라우팅 우선으로 수정. 허용 Cell의 실제 스케줄링 제약 적용 및 미들웨어 실행 변경은 이번 범위가 아니다.
- 배포: SQLite 백업 후 `docker compose up -d --build --no-deps cell-mes frontend`. `cell-mes` 시작 시 `alembic upgrade head` 수행. 기존 볼륨을 삭제하지 않는다.
- 즉시 동기화: `docker compose exec mes-interface-sync python -m mes_interface_sync.main sync-once`.
- 상세 파일 목록과 사용 규칙은 Cell-MES 변경 이력의 같은 날짜 항목 참고.

## 2026-09-29 - MES Cell별 설비 소속 관리

- MES 기준정보 메뉴에 `Cell 관리` 화면(`/master/cells`) 추가.
- Cell 생성/수정 및 관리자 설비 할당/이동/해제 지원. 연결된 장비가 있는 Cell은 삭제 차단.
- 기존 SQLite `cells`와 `equipments.cell_id`를 활용하며 DB 마이그레이션은 필요하지 않음.
- 다음 성공한 Interface DB 동기화에서 `mes_if.if_cells`와 `mes_if.if_equipments.cell_id`로 제공. APS 측 조인 기준은 `if_equipments.cell_id = if_cells.id`.
- 이 단계 당시 제품별 허용 Cell은 후속 범위였으며, 위의 같은 날짜 후속 구현에서 추가했다. 공정별 개별 설비 연결과 공유 장비 관계는 별도 범위이다.
- 파일별 변경 내용과 API 사용법은 `agents/cell-mes/docs/CHANGES.md`의 같은 날짜 항목 참고.

## 현재 핵심 시스템

### MES Interface DB

목적:

- SQLite 기반 MES 데이터를 외부 APS가 조회할 수 있도록 PostgreSQL Interface DB로 제공한다.
- APS가 MES 원본 SQLite 파일이나 MES 내부 테이블에 직접 접근하지 않게 한다.
- MES 스키마 변경이 있어도 APS 조회 계약은 `mes_if` View와 YAML 매핑으로 최대한 유지한다.
- APS 결과 쓰기는 아직 스키마가 확정되지 않았으므로 1차 구현 범위에서 제외한다.

최종 구조:

```text
MES SQLite
  -> mes-interface-sync worker
  -> PostgreSQL Interface DB
       mes_src       : MES 원본 테이블 미러링
       mes_if        : APS 조회용 read-only View
       aps_if        : APS 결과 수신 예약 영역
       if_admin      : sync batch, schema snapshot, error log
```

Docker Compose 서비스:

| 서비스 | 역할 |
| --- | --- |
| `mes-interface-db` | PostgreSQL Interface DB 컨테이너 |
| `mes-interface-sync` | MES SQLite를 PostgreSQL로 복사하는 배치 worker |

Docker Compose volume:

| Volume | 역할 |
| --- | --- |
| `mes_interface_db_data` | PostgreSQL 데이터 영구 저장소. 컨테이너가 아니라서 `docker ps`에는 보이지 않고 `docker volume ls`에서 확인한다. |

외부 노출:

| 항목 | 값 |
| --- | --- |
| Port | `15433` |
| Database | `mes_interface` |
| APS read-only user | `aps_user` |
| APS schema | `mes_if` |
| 권한 | `mes_if` View 조회 전용 |

비밀번호는 이 문서에 적지 않는다. 실제 값은 `.env`의 `MES_INTERFACE_APS_READER_PASSWORD`를 기준으로 관리한다.

---

## MES Interface DB 사용 방법

### 1. 서비스 기동

```bash
docker compose up -d mes-interface-db mes-interface-sync
```

### 2. 정기 동기화 스케줄

상시 실행 컨테이너는 초 단위 interval이 아니라 고정 시각 기준으로 실행한다.

```text
MES_INTERFACE_SYNC_SCHEDULE=02:00,14:00
MES_INTERFACE_SYNC_TIMEZONE=Asia/Seoul
MES_INTERFACE_SYNC_RUN_ON_START=true
```

- `MES_INTERFACE_SYNC_SCHEDULE`: 매일 실행할 시각 목록이다.
- `MES_INTERFACE_SYNC_TIMEZONE`: 스케줄 기준 timezone이다.
- `MES_INTERFACE_SYNC_RUN_ON_START`: 컨테이너 시작 직후 즉시 1회 동기화할지 결정한다.

### 3. 즉시 동기화

정기 배치를 기다리지 않고 한 번 바로 동기화할 때 사용한다.

```bash
docker compose run --rm mes-interface-sync sync-once
```

### 4. 컨테이너 상태 확인

```bash
docker ps --filter name=mes-interface
```

정상 상태 예시:

```text
mes-interface-db     Up ... (healthy)   0.0.0.0:15433->5432/tcp
mes-interface-sync   Up ...
```

### 5. 최신 동기화 결과 확인

```bash
docker exec agents-workspace_260619-mes-interface-db-1 \
  psql -U if_owner -d mes_interface \
  -c "select status, table_count, row_count, started_at, completed_at, error_message
      from if_admin.sync_batches
      order by started_at desc
      limit 3;"
```

2026-09-04 검증 결과:

| 항목 | 결과 |
| --- | --- |
| 최신 batch status | `SUCCESS` |
| 복사 테이블 수 | 27 |
| 복사 row 수 | 2,747 |
| APS 계정 조회 | `mes_if.if_work_orders` 조회 성공 |

### 5. APS 접속

호스트 PC에서 확인:

```bash
PGPASSWORD='<APS_READER_PASSWORD>' \
psql -h localhost -p 15433 -U aps_user -d mes_interface
```

외부 APS 서버에서 확인:

```bash
PGPASSWORD='<APS_READER_PASSWORD>' \
psql -h <공장_PC_또는_서버_IP> -p 15433 -U aps_user -d mes_interface
```

DBeaver 같은 DB 클라이언트에서도 PostgreSQL 연결로 접속할 수 있다.

```text
Database Type: PostgreSQL
Host: 공장 PC 또는 서버 IP
Port: 15433
Database: mes_interface
User: aps_user
Password: APS reader 비밀번호
```

---

## APS 조회 규칙

APS는 `mes_if` schema의 View만 조회한다.

기본 View 이름 규칙:

```text
MES 원본 테이블: work_orders
APS 조회 View : mes_if.if_work_orders
```

APS가 직접 접근하지 않는 schema:

| Schema | 이유 |
| --- | --- |
| `mes_src` | MES 원본 미러링 영역이며 내부 구조 변경을 그대로 따라간다. |
| `if_admin` | 배치 로그와 오류 로그가 들어 있는 운영 영역이다. |
| `aps_if` | APS 결과 쓰기 예약 영역이며 1차 구현에서는 외부 쓰기 권한을 열지 않았다. |

모든 APS View에는 다음 메타 컬럼이 붙는다.

| 컬럼 | 의미 |
| --- | --- |
| `_if_batch_id` | 해당 row가 복사된 sync batch ID |
| `_if_synced_at` | Interface DB에 동기화된 시각 |
| `_if_source_table` | MES 원본 테이블명 |
| `_if_source_pk` | MES 원본 primary key 값 |

---

## 핵심 APS View

다음 6개 View는 `agents/mes-interface-sync/config/interface_views.yaml`에서 컬럼 계약을 고정한다.

| View | 용도 |
| --- | --- |
| `mes_if.if_work_orders` | 작업지시, LOT, 제품, 수량, 우선순위, 납기 |
| `mes_if.if_process_routings` | 제품별 공정 순서 |
| `mes_if.if_std_processes` | 표준 공정 기준정보 |
| `mes_if.if_equipments` | 설비 기준정보와 상태 |
| `mes_if.if_prod_results` | 생산 실적과 설비 점유 이력 |
| `mes_if.if_downtimes` | 설비 비가동 이력 |

YAML에 명시되지 않은 MES 테이블은 자동으로 `mes_if.if_<원본테이블명>` View를 만든다.

현재 전체 View 목록 확인:

```sql
select table_name
from information_schema.views
where table_schema = 'mes_if'
order by table_name;
```

현재 전체 컬럼 확인:

```sql
select
    table_name,
    string_agg(column_name, ', ' order by ordinal_position) as columns
from information_schema.columns
where table_schema = 'mes_if'
group by table_name
order by table_name;
```

---

## YAML 매핑 방식

YAML 파일:

```text
agents/mes-interface-sync/config/interface_views.yaml
```

핵심 필드:

| 필드 | 의미 |
| --- | --- |
| `views[].name` | APS에 노출할 View 이름 |
| `views[].source_table` | MES 원본 테이블명 |
| `columns[].name` | APS가 조회할 고정 컬럼명 |
| `columns[].source` | 현재 MES 원본 컬럼명 |
| `columns[].source_candidates` | MES 컬럼명 변경에 대비한 후보 컬럼명 |
| `columns[].required` | 없으면 sync를 실패시켜야 하는 필수 컬럼 여부 |
| `columns[].default` | 원본 컬럼이 없을 때 사용할 기본값 |

예시:

```yaml
views:
  - name: if_work_orders
    source_table: work_orders
    columns:
      - name: qty
        source_candidates:
          - qty
          - target_qty
        required: true
      - name: due_date
        source_candidates:
          - due_date
          - delivery_date
          - deadline_at
        required: false
```

이 예시는 MES 원본 컬럼이 `qty`에서 `target_qty`로 바뀌어도 APS는 계속 `qty`라는 컬럼명으로 조회할 수 있게 한다.

---

## 제외 테이블과 민감 컬럼

Interface DB에 복사하지 않는 기본 제외 테이블:

```text
users
middleware_config
alembic_version
```

또한 테이블명에 계정, 인증, 세션, 토큰, 비밀번호, secret 성격의 키워드가 있으면 자동 제외한다.

`mes_src`에는 복사될 수 있지만 `mes_if` View에서 숨기는 민감 컬럼:

| 원본 테이블 | 제외 컬럼 |
| --- | --- |
| `equipments` | `connection_config` |
| `measurement_devices` | `connection_config` |
| `process_routing_files` | `file_path` |
| `dt_file_refs` | `path`, `raw_metadata` |
| `dt_project_refs` | `raw_metadata` |

---

## 구현 파일 맵

| 파일 | 역할 |
| --- | --- |
| `docker-compose.yml` | `mes-interface-db`, `mes-interface-sync`, volume 추가 |
| `.env.example` | Interface DB 환경변수 예시 추가 |
| `.env` | 실제 Interface DB 접속 정보, 비밀번호 포함 |
| `agents/mes-interface-db/init/001_init_schemas.sql` | PostgreSQL schema와 admin table 초기화 |
| `agents/mes-interface-db/init/002_roles.sh` | PostgreSQL role과 권한 초기화 |
| `agents/mes-interface-db/APS_ACCESS_GUIDE.md` | APS 업체용 접속 및 View 명세 |
| `agents/mes-interface-sync/Dockerfile` | sync worker 이미지 |
| `agents/mes-interface-sync/src/mes_interface_sync/config.py` | 환경변수 로딩 |
| `agents/mes-interface-sync/src/mes_interface_sync/schema.py` | SQLite to PostgreSQL 타입 매핑, 자동 View helper |
| `agents/mes-interface-sync/src/mes_interface_sync/sync_service.py` | 스냅샷 생성, 전체 refresh, 로그 기록 |
| `agents/mes-interface-sync/src/mes_interface_sync/view_config.py` | YAML 매핑 파서와 View SQL 생성 |
| `agents/mes-interface-sync/src/mes_interface_sync/main.py` | `run`, `sync-once` CLI |
| `agents/mes-interface-sync/config/interface_views.yaml` | APS View 컬럼 계약 |
| `agents/mes-interface-sync/tests/test_schema.py` | 스키마/환경변수 테스트 |
| `agents/mes-interface-sync/tests/test_view_config.py` | YAML 매핑 테스트 |
| `docs/mes-interface-db-implementation-report.html` | PPT 보고서용 HTML |
| `docs/CHANGES.md` | workspace 통합 변경 이력과 운영 가이드 |

---

## 검증 명령

sync worker 테스트:

```bash
uv run pytest agents/mes-interface-sync/tests
```

2026-09-04 결과:

```text
14 passed
```

Docker Compose 설정 검증:

```bash
docker compose config --quiet
```

2026-09-04 결과:

```text
통과
```

실행 중 컨테이너 확인:

```bash
docker ps --filter name=mes-interface
```

2026-09-04 결과:

```text
agents-workspace_260619-mes-interface-sync-1   Up
agents-workspace_260619-mes-interface-db-1     Up, healthy, 15433->5432
```

---

## 날짜별 구현 히스토리

### 2026-09-07 — MES Interface DB 고정 시각 동기화 적용

변경 목적:

- 기존 `43200`초 interval 방식은 컨테이너 시작 시각에 따라 실제 동기화 시간이 달라진다.
- 운영자가 APS 업체에 데이터 갱신 시각을 명확히 안내할 수 있도록 매일 정해진 시각에 동기화되게 한다.

주요 변경:

- `MES_INTERFACE_SYNC_INTERVAL_SECONDS` 사용을 중단하고 다음 설정으로 교체
  - `MES_INTERFACE_SYNC_SCHEDULE=02:00,14:00`
  - `MES_INTERFACE_SYNC_TIMEZONE=Asia/Seoul`
  - `MES_INTERFACE_SYNC_RUN_ON_START=true`
- `mes-interface-sync`의 상시 실행 루프를 다음 실행 시각 계산 방식으로 변경
- `sync-once` 명령은 수동 즉시 동기화 용도로 유지
- README, 아키텍처 계획 문서, 보고서 HTML, 통합 변경 이력 문서의 스케줄 설명 갱신

운영 영향:

- 컨테이너가 언제 시작되더라도 정기 동기화는 매일 `02:00`, `14:00` 기준으로 실행된다.
- `MES_INTERFACE_SYNC_RUN_ON_START=true`이면 컨테이너 시작 직후에도 1회 동기화한다.
- 긴급 검증이나 APS 요청 시에는 기존처럼 `docker compose run --rm mes-interface-sync sync-once`를 실행한다.

검증:

- `uv run pytest agents/mes-interface-sync/tests`: 19 passed
- `docker compose config --quiet`: 통과
- `docker compose up -d --force-recreate mes-interface-sync`: 재시작 성공
- sync worker 로그에서 시작 직후 동기화 성공과 다음 예약 시각 `2026-09-07T14:00+09:00` 확인
- `if_admin.sync_batches` 최신 batch `SUCCESS`, 27개 테이블, 2,747 row 확인

### 2026-09-04 — MES Interface DB 구현

변경 목적:

- 외부 APS 연동을 위해 SQLite MES 데이터를 PostgreSQL Interface DB로 제공한다.
- APS는 `mes_if` read-only View만 조회하게 한다.
- DB to DB 직접 연결 대신 Interface DB와 sync worker로 경계를 둔다.
- 1차 단계에서는 APS 결과 write-back을 열지 않는다.

주요 변경:

- Docker Compose에 `mes-interface-db` PostgreSQL 컨테이너 추가
- Docker Compose에 `mes-interface-sync` 배치 worker 컨테이너 추가
- PostgreSQL schema 생성
  - `mes_src`
  - `mes_if`
  - `aps_if`
  - `if_admin`
- PostgreSQL role 생성
  - `if_owner`
  - `if_sync_writer`
  - `aps_user`
- `.env.example`과 `.env`에 Interface DB 환경변수 추가
- SQLite snapshot 기반 전체 refresh 구현
- sync batch, table stats, schema snapshot, schema change, error log 저장
- 제외 테이블과 민감 컬럼 정책 구현
- APS용 `APS_ACCESS_GUIDE.md` 작성

검증:

- 최신 sync batch `SUCCESS`
- 27개 테이블, 2,747 row 복사 확인
- APS read-only 계정으로 `mes_if.if_work_orders` 조회 성공

### 2026-09-04 — MES Interface View YAML 매핑 적용

변경 목적:

- MES 원본 컬럼명이 변경되어도 APS가 보는 View 컬럼명을 안정적으로 유지한다.
- 핵심 APS View는 명시적인 계약으로 관리하고, 나머지 테이블은 자동 View로 제공한다.

주요 변경:

- `agents/mes-interface-sync/config/interface_views.yaml` 추가
- YAML 기반 View 생성 모듈 `view_config.py` 추가
- 핵심 View 6개 컬럼 계약 정의
  - `if_work_orders`
  - `if_process_routings`
  - `if_std_processes`
  - `if_equipments`
  - `if_prod_results`
  - `if_downtimes`
- `source_candidates`로 컬럼명 변경 대응
- `required`와 `default`로 필수값 및 fallback 정책 정의
- 기존 View 컬럼 축소 시 PostgreSQL 오류가 나지 않도록 `DROP VIEW IF EXISTS` 후 재생성 방식으로 보정
- APS 권한 부여를 YAML의 실제 View 이름 기준으로 보정

검증:

- `uv run pytest agents/mes-interface-sync/tests`: 14 passed
- 최신 sync batch `SUCCESS`
- YAML 기준 `if_work_orders` 컬럼 순서 확인
- 전체 `mes_if` View 수 27개 확인

### 2026-09-04 — P4R PROCESSING_TIME YAML mapping + AAS action profile 합산 적용

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- P4R preview의 `PROCESS_INFO.PROCESS_OPERATION_INFO[].PROCESSING_TIME`에 라우팅 cycle time뿐 아니라 CNC door/vise, UR tending action 같은 실제 장비 점유 action 시간을 합산한다.
- 모든 시나리오에 일괄 적용하지 않고, YAML에 `p4r_process_mapping`이 명시된 경우에만 활성화한다.

주요 변경:

- Cell1 YAML에 `p4r_process_mapping` 추가
- `scenario_asset_parser.py`에서 P4R process mapping과 step action 추출
- `p4r_action_timing.py`에서 AAS `P4RActionTimingProfile`을 action timing catalog로 변환
- `p4r_adapter.py`에서 라우팅 시간과 action profile 합산
- 계산 trace를 wrapper의 `sources.p4r_processing_time.items`에 기록

검증:

- `uv run pytest tests/services/test_p4r_adapter.py -q`
- 결과: 16 passed

### 2026-09-04 — P4R MACHINE_INSTANCE failure status JSON rule 적용

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- P4R preview payload의 `MACHINE_INSTANCE.FAILURE_STATUS`를 빈 placeholder가 아니라 MES JSON failure rule 기준으로 채운다.
- 미들웨어/AAS raw status를 `FAILURE_TYPE`, `REMAINING_REPAIR_TIME`으로 정규화한다.

주요 변경:

- `agents/cell-mes/config/p4r_failure_rules.json` 추가
- `failure_rules.py` 추가
- `p4r_adapter.py`에서 failure rule 적용
- `P4R_FAILURE_RULES_PATH` 환경변수 추가
- rule 파일 오류 시 built-in default rule set으로 fallback

검증:

- `uv run pytest tests/services/test_p4r_adapter.py -q`
- 결과: 11 passed

### 2026-09-02 — P4R failure rule 저장 방식 JSON 설정으로 정리

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- P4R failure type과 matching rule을 코드에 고정하지 않고 JSON 설정으로 분리한다.
- 과기대/P4R 검증 과정에서 rule이 바뀌어도 구현 영향 범위를 줄인다.

결정:

- `P4R_FAILURE_RULES_PATH`를 통해 JSON rule 파일을 읽는다.
- rule 파일이 없거나 잘못되면 기본 rule set으로 fallback한다.
- Docker에서는 JSON 파일을 volume mount하면 이미지 재빌드 부담을 줄일 수 있다.

### 2026-09-02 — P4R failure status MES 정규화 방식으로 설계 보정

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- P4R failure status를 미들웨어 전용 submodel이 아니라 MES adapter의 의미 변환 결과로 관리한다.
- 미들웨어가 P4R 전용 enum과 복구 시간 정책까지 알 필요가 없게 한다.

결론:

```text
Middleware/AAS raw status
  -> MES JSON failure rule
  -> P4R MACHINE_INSTANCE.FAILURE_STATUS
```

### 2026-09-01 — P4R FEEDER 버퍼 및 PROC_NUM 보정

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- FEEDER의 동시 처리 capacity와 소재/제품 보관 capacity를 분리한다.
- Cell1 라우팅 material stage 번호를 P4R 샘플에 맞춰 1-based로 보정한다.

주요 변경:

- FEEDER loader/unloader slot을 P4R `BUFFER_TYPE`, `BUFFER_INSTANCE`로 표현
- `RobotGateway.Status.loaderCount/unloaderCount`를 현재 WIP 수량으로 반영
- 첫 공정 소비/생산 `PROC_NUM`을 1-based 흐름으로 조정

검증:

- `uv run pytest tests/services/test_p4r_adapter.py -q`
- 결과: 5 passed

### 2026-09-01 — P4R 전용 라우팅 cycle time 적용

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- P4R `PROCESSING_TIME`을 표준공정 공통 시간이 아니라 제품/라우팅별 시간 기준으로 생성한다.

주요 변경:

- `process_routings.cycle_time_sec` 추가
- 라우팅 저장 API에서 기존 cycle time 보존
- P4R adapter가 `process_routings.cycle_time_sec`를 우선 사용하고 없으면 `std_processes.cycle_time_sec`로 fallback
- 스케줄러 projector는 기존 로직 유지

검증:

- 라우팅 API, P4R adapter, scheduler 테스트 50 passed
- TypeScript type check 통과

### 2026-09-01 — Cell1 P4RActionTimingProfile AASX 선반영

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- Cell1 장비들이 제공하는 hardware action mapping과 AASX gateway command를 기준으로 `P4RActionTimingProfile`을 AASX에 먼저 반영한다.

주요 변경:

- `NX5500`, `FEEDER`, `ANT_AMR`, `UR_ROBOT`, `CNC_DIE`에 action timing profile 추가
- UR robot action duration 보정
- `timeOwnership`, `canContributeToRoutingCycleTime` 기준 정리

검증:

- `unzip -t assets.aasx` 통과
- `aasx/data.xml` XML 파싱 통과
- `P4RActionTimingProfile` submodel 5개 확인

### 2026-08-06 — 가상장비 동기화 및 MES 내부 복사 관리 구현

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- 미들웨어 AASX의 실제장비와 가상장비를 Cell-MES가 구분해서 동기화한다.
- MES 내부에서 스케줄링 검토용 가상장비를 복사 생성할 수 있게 한다.

주요 변경:

- `schedulerInfo` 기준으로 장비 메타데이터와 가상장비 여부를 `equipments.spec_data`에 저장
- `DH400`, `NX5500` 계열 가상장비를 AASX에 추가
- Gateway 이름 변형 인식 보강
- `FEEDER`, `UR_ROBOT`, `EQUATOR_01` 타입 매핑 개선
- 설비 현황 화면에 실장비/가상장비 badge와 filter 추가
- DB migration 없이 `spec_data` JSON 기반으로 1차 구현

### 2026-08-04 — P4R JSON 어댑터 1차 구현

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- Cell-MES의 작업지시, 라우팅, 설비, 시나리오 데이터를 P4R JSON preview payload로 변환한다.

요약:

- P4R preview API와 adapter 1차 구현
- MES 기준정보를 P4R 구조에 맞게 변환
- 이후 P4R processing time, feeder buffer, failure status 보정의 기반이 되었다.

### 2026-07-30 — 미들웨어 Unit 상태 조회 및 제어 1차 연동

출처:

- `agents/cell-mes/docs/CHANGES.md`

변경 목적:

- MES가 미들웨어를 통해 Unit 실행 상태를 조회하고 제어하는 1차 연동을 구성한다.

요약:

- Unit 상태 조회와 제어 API 연동
- 미들웨어 연동 설정과 실행 패키지 개념 보강
- 이후 P4R preview와 스케줄링 연동의 실행 상태 기반이 되었다.

### 2026-05-26 ~ 2026-05-28 — 주간 보고용 MES-미들웨어 연동 상세 보완

출처:

- `agents/cell-mes/docs/CHANGES.md`

요약:

- MES와 미들웨어 연동 상세 내용을 주간 보고 관점으로 정리
- 연동 흐름, 상태 처리, 운영 이슈를 문서화

### 2026-05-22 — MES-미들웨어 유닛 실행 패키지 연동 개선

출처:

- `agents/cell-mes/docs/CHANGES.md`

요약:

- MES 유닛 실행 패키지와 미들웨어 실행 흐름을 개선
- 실행 단위와 제어 흐름을 정리

### 2026-05-19 ~ 2026-05-20 — 초기 MES-미들웨어 연동 정리

출처:

- `agents/cell-mes/docs/CHANGES.md`

요약:

- Cell-MES와 미들웨어의 초기 연동 흐름을 정리
- 이후 Unit 상태, P4R adapter, Interface DB 작업의 기반이 되었다.

---

## 운영 리스크와 후속 과제

| 항목 | 현재 상태 | 후속 권장 |
| --- | --- | --- |
| 외부 DB 포트 노출 | `15433`으로 PostgreSQL 공개 가능 | 공유기/방화벽 source IP 제한 또는 VPN 검토 |
| APS 결과 쓰기 | 1차 범위 제외 | APS 결과 스키마 확정 후 `aps_if` staging 설계 |
| MES 스키마 변경 | YAML 후보 컬럼과 schema log로 대응 | breaking change는 `_v2` View 또는 YAML 계약 변경으로 관리 |
| 전체 refresh 성능 | 현재 2,747 row 수준에서 문제 없음 | 데이터 증가 시 증분 동기화 검토 |
| credential 관리 | `.env` 기반 | 운영 전 비밀번호 회전, 보안 채널로 전달 |
| 백업/복구 | PostgreSQL volume 사용 | 운영 전 backup과 restore 테스트 절차 추가 |

---

## 변경 시 기록 규칙

앞으로 기능을 수정하면 이 문서에 날짜별 섹션을 추가한다.

기록 항목:

- 변경 날짜
- 변경 목적
- 변경 파일
- 변경 내용
- 운영 영향
- 검증 명령과 결과
- 남은 리스크 또는 후속 작업
