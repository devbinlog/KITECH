# MES Interface Sync

MES SQLite DB를 PostgreSQL Interface DB로 전체 refresh 방식으로 복사하는 sync worker이다.

APS 업체에 전달할 접속 방법과 View 명세는 `../mes-interface-db/APS_ACCESS_GUIDE.md`를 기준으로 한다.

## 실행 모드

상시 실행:

```bash
docker compose up -d mes-interface-db mes-interface-sync
```

즉시 1회 동기화:

```bash
docker compose run --rm mes-interface-sync sync-once
```

실사용 전에 `.env`에 다음 값을 반드시 설정한다.

```text
MES_INTERFACE_DB_ADMIN_PASSWORD
MES_INTERFACE_SYNC_USER
MES_INTERFACE_SYNC_PASSWORD
MES_INTERFACE_APS_READER_USER
MES_INTERFACE_APS_READER_PASSWORD
MES_INTERFACE_SYNC_SCHEDULE
MES_INTERFACE_SYNC_TIMEZONE
MES_INTERFACE_SYNC_RUN_ON_START
```

기본 계정명:

```text
MES_INTERFACE_SYNC_USER=if_sync_writer
MES_INTERFACE_APS_READER_USER=aps_user
```

APS 업체에 전달하는 DB 접속 ID는 `MES_INTERFACE_APS_READER_USER` 값이다.

PostgreSQL init script는 DB volume이 처음 생성될 때만 실행된다. fallback 비밀번호로 한 번이라도 `mes-interface-db`를 띄운 뒤 실제 비밀번호로 바꾸려면, 기존 `mes_interface_db_data` volume을 제거하고 다시 초기화하거나 DB 안에서 role password를 직접 변경해야 한다.

## 동기화 스케줄

정기 동기화는 초 단위 interval이 아니라 고정 시각 목록으로 실행한다.

```text
MES_INTERFACE_SYNC_SCHEDULE=02:00,14:00
MES_INTERFACE_SYNC_TIMEZONE=Asia/Seoul
MES_INTERFACE_SYNC_RUN_ON_START=true
```

- `MES_INTERFACE_SYNC_SCHEDULE`: 매일 실행할 시각 목록이다. `HH:MM` 형식으로 쉼표 구분한다.
- `MES_INTERFACE_SYNC_TIMEZONE`: 스케줄 기준 timezone이다.
- `MES_INTERFACE_SYNC_RUN_ON_START`: 컨테이너 시작 직후 즉시 1회 동기화할지 결정한다.

운영 중 긴급 검증이 필요하면 정기 스케줄을 기다리지 않고 `sync-once`를 사용한다.

## 동기화 대상

- `mes_src.<원본테이블명>`: MES 원본 테이블 미러링
- `mes_if.if_<원본테이블명>`: APS 조회용 read-only View
- `if_admin.*`: 동기화 배치, 테이블별 통계, 오류, 스키마 변경 로그

## View 매핑 설정

APS 연동에 중요한 핵심 View의 컬럼 계약은 `config/interface_views.yaml`에서 관리한다.

- `views[].name`: APS에 노출할 View 이름
- `views[].source_table`: MES 원본 테이블명
- `columns[].name`: APS가 조회할 고정 컬럼명
- `columns[].source`: 현재 MES 원본 컬럼명
- `columns[].source_candidates`: MES 컬럼명이 변경될 때 호환할 후보 컬럼명
- `columns[].required`: 동기화 성공에 반드시 필요한 컬럼 여부
- `columns[].default`: 원본 컬럼이 없을 때 사용할 기본값

YAML에 정의되지 않은 MES 테이블은 자동으로 `mes_if.if_<원본테이블명>` View를 생성한다.

## 제외 규칙

기본 제외 테이블:

```text
users
middleware_config
alembic_version
```

테이블명에 계정, 인증, 세션, 토큰, 비밀번호, secret 성격의 키워드가 포함되어도 제외한다.

## 민감 컬럼

다음 컬럼은 `mes_src`에는 복사하지만 `mes_if` View에서는 제외한다.

| 테이블 | 컬럼 |
| --- | --- |
| `equipments` | `connection_config` |
| `measurement_devices` | `connection_config` |
| `process_routing_files` | `file_path` |
| `dt_file_refs` | `path`, `raw_metadata` |
| `dt_project_refs` | `raw_metadata` |
