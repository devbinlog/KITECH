# Recipe 작성 가이드

이 문서는 AM-middleware의 자동화 작업 시나리오(Recipe) YAML 파일 작성 기준입니다.
레시피 파일은 `recipes/` 디렉토리에 위치해야 합니다.

## 1. 기본 구조

```yaml
name: "recipe_name"         # 레시피 고유 이름 (파일명과 별개)
desc: "레시피 설명"           # 선택사항
assets:                      # 사용할 자산 목록
  - id: "NC1"                # 레시피 내에서 사용할 자산 식별자
    name: "NX5500"           # AAS에 등록된 실제 자산 이름
  - id: "AMR"
    name: "DOOSAN_MOMA"
steps:                       # 실행할 스텝 목록
  - id: "1"
    name: "스텝 이름"
    ...
```

### assets

| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | O | 레시피 내에서 사용할 자산 식별자. `acquire`에서 이 값을 사용 |
| `name` | O | AAS에 등록된 실제 자산 이름. 런타임에 id가 이 이름으로 매핑됨 |

> **주의**: `acquire`에서는 반드시 `id` 값을 사용합니다. `name` 값을 직접 사용하면 안 됩니다.

## 2. 스텝 (Step)

각 스텝은 **자원 해제 → 자원 획득 → 액션 실행 → 라우팅** 순서로 실행됩니다.

```yaml
steps:
  - id: "1-1"
    name: "문 상태 확인"
    release: ["{{acq.all}}"]
    acquire:
      main: ["NC1", "NC2"]
      sub1: ["AMR"]
    action: "{{acq.main}}/cncGateway/status/doorState"
    params: {"variable": 100, "value": 4.8}
    routing:
      - when: "'{{res}}' == 'open'"
        then:
          - next: "2"
```

### 필드 정의

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `id` | O | 문자열 | 스텝 고유 ID. 반드시 따옴표로 감쌈: `"1-1"`, `"2"` |
| `name` | O | 문자열 | 스텝 이름 (로그 표시용) |
| `release` | - | 문자열 리스트 | 스텝 시작 전 해제할 자원. `["{{acq.all}}"]` 또는 `["{{acq.main}}"]` |
| `acquire` | - | 딕셔너리 | 점유할 자원. 키는 역할명, 값은 자산 ID 리스트 |
| `action` | - | 문자열 | 실행할 AAS 경로 |
| `params` | - | 딕셔너리 | 액션에 전달할 파라미터 (JSON 형태) |
| `routing` | - | 리스트 | 액션 결과에 따른 분기 규칙 |

### acquire 상세

`acquire`의 키(역할명)는 자유롭게 지정할 수 있으며, `{{acq.역할명}}`으로 참조합니다.
값은 자산 ID의 리스트이며, 리스트 중 사용 가능한 자산이 자동 배정됩니다.

```yaml
acquire:
  main: ["NC1", "NC2"]     # NC1 또는 NC2 중 사용 가능한 것을 main으로 배정
  sub1: ["AMR"]             # AMR을 sub1으로 배정
```

- 배정 결과는 `{{acq.main}}`, `{{acq.sub1}}`로 참조
- 이미 해당 유닛이 점유한 자원은 재진입(re-entry) 허용

### action 경로 형식

```
자산이름/게이트웨이서브모델/카테고리/기능이름
```

예시:
```yaml
# 정식 경로
action: "{{acq.main}}/cncGateway/status/doorState"
action: "{{acq.sub1}}/robotGateway/commands/move"
action: "{{acq.main}}/modbusGateway/commands/clampVise"

# 축약 경로 (게이트웨이 서브모델 생략 - 자동 탐색)
action: "{{acq.main}}/status/doorState"
```

## 3. 라우팅 (Routing)

액션 결과(`{{res}}`)에 따라 다음 동작을 결정합니다.
위에서부터 순서대로 `when` 조건을 검사하여 **최초 매칭** 규칙을 실행합니다.

```yaml
routing:
  - when: "'{{res}}' == 'OK'"       # 조건 1
    then:
      - message: "성공"
      - next: "2"
  - when: "'{{res}}' == 'NG'"       # 조건 2
    then:
      - alarm: "실패"
  - when:                            # else (빈 when = 항상 매칭)
    then:
      - alarm: "예상치 못한 결과: {{res}}"
```

### when 조건 작성 규칙

`when` 조건은 Python 표현식으로 평가됩니다. 다음 규칙을 반드시 지켜야 합니다:

**문자열 비교: 양쪽 모두 작은따옴표로 감싸기**
```yaml
# 올바른 예
- when: "'{{res}}' == 'OK'"
- when: "'{{res}}' == 'closed'"

# 잘못된 예 (NameError 발생)
- when: "{{res}} == OK"        # OK가 변수명으로 해석됨
- when: "{{res}} == closed"    # closed가 변수명으로 해석됨
```

**숫자 비교: 따옴표 없이 사용**
```yaml
- when: "{{res}} > 0"
- when: "{{res}} == 100"
```

**None 비교: 따옴표 없이 사용**
```yaml
- when: "{{res}} == None"
```

**else 조건: when을 비워두기**
```yaml
- when:           # 위의 조건에 모두 해당하지 않을 때
  then:
    - alarm: "예상치 못한 결과"
```

**지원하는 연산자**: `==`, `!=`, `>`, `<`, `>=`, `<=`

> **권장**: 모든 라우팅의 마지막에는 빈 `when`(else) 분기를 두어 예상치 못한 결과를 처리하세요.
> else 분기가 없고 어떤 조건도 매칭되지 않으면 ALARM이 발생합니다.

### then 액션 목록

`then` 안에는 아래 액션들을 순서대로 나열합니다. **한 항목에 하나의 액션만** 작성합니다.

| 액션 | 타입 | 설명 |
|------|------|------|
| `next` | 문자열 | 이동할 다음 스텝 ID. 없으면 레시피 종료 |
| `message` | 문자열 | 정보성 로그 출력 |
| `alarm` | 문자열 | ALARM 상태로 전이하고 실행 중단 |
| `release` | 문자열 리스트 | 자원 점유 해제: `["{{acq.main}}"]` 또는 `["{{acq.all}}"]` |
| `set_val` | 문자열 | `{{var}}` 변수 값 설정 |
| `set_loc` | 문자열 | `{{loc}}` 위치 값 설정 (설정 시 `{{pos}}`는 초기화됨) |
| `set_pos` | 문자열 | `{{pos}}` 세부 위치 값 설정 |
| `max_retry` | 정수 | 현재 스텝의 최대 재시도 횟수. 초과 시 ALARM |
| `wait_retry` | 실수(초) | 조건 미충족 시 대기 후 현재 스텝 재실행 (폴링 패턴). 값은 타임아웃(초) |
| `delay` | 실수(초) | 순수 대기 시간. 대기 후 다음 액션으로 진행 |

> **alarm이 실행되면 이후 액션은 무시됩니다.** alarm은 then의 마지막이 아니어도 즉시 중단합니다.

## 4. 동적 변수

| 변수 | 설명 | 설정 방법 |
|------|------|----------|
| `{{acq.ROLE}}` | 해당 역할로 점유한 자산 이름 | `acquire`에서 자동 배정 |
| `{{acq.all}}` | 현재 점유한 모든 자산 | `release`에서만 사용 |
| `{{res}}` | 직전 액션의 결과값 | `action` 실행 후 자동 설정 |
| `{{var}}` | 범용 변수 | `set_val`로 설정 |
| `{{loc}}` | 위치 변수 | `set_loc`으로 설정 |
| `{{pos}}` | 세부 위치 변수 | `set_pos`으로 설정 |

- 변수 참조 시 공백 허용: `{{ var }}` = `{{var}}`
- 미설정 변수는 빈 문자열로 치환됨

## 5. 재시도 패턴

### max_retry (횟수 제한 재시도)

```yaml
routing:
  - when: "'{{res}}' == 'OK'"
    then:
      - next: "2"
  - when:
    then:
      - message: "실패, 재시도"
      - max_retry: 3            # 3회까지 재시도, 초과 시 ALARM
      - next: "1-1"             # 재시도할 스텝 (자기 자신 또는 다른 스텝)
```

### wait_retry (폴링 패턴)

```yaml
routing:
  - when: "'{{res}}' == 'complete'"
    then:
      - next: "3"
  - when:
    then:
      - message: "아직 완료되지 않음, 대기 후 재확인"
      - wait_retry: 60          # 60초 타임아웃 (0이면 무제한)
```

`wait_retry`는 1초 간격으로 현재 스텝을 재실행하며, 지정한 시간(초)이 경과하면 ALARM이 발생합니다.

## 6. 전체 예시

```yaml
name: "cnc_loading"
desc: "CNC 설비에 소재를 로딩하는 워크플로우"
assets:
  - id: "NC1"
    name: "NX5500"
  - id: "NC2"
    name: "DH400"
  - id: "AMR"
    name: "DOOSAN_MOMA"
steps:
  # --- 1단계: CNC 문 상태 확인 ---
  - id: "1-1"
    name: "문 상태 확인"
    acquire:
      main: ["NC1", "NC2"]       # NC1 또는 NC2 중 가용한 설비를 main으로 배정
      sub1: ["AMR"]              # AMR을 sub1으로 배정
    action: "{{acq.main}}/cncGateway/status/doorState"
    routing:
      - when: "'{{res}}' == 'open'"
        then:
          - message: "문이 열려있습니다."
          - next: "2"
      - when: "'{{res}}' == 'closed'"
        then:
          - message: "문이 닫혀있습니다. 문 열기를 시도합니다."
          - max_retry: 1
          - next: "1-2"
      - when:
        then:
          - alarm: "문 상태를 파악할 수 없습니다."

  # --- 1-2단계: 문 열기 ---
  - id: "1-2"
    name: "문 열기"
    action: "{{acq.main}}/cncGateway/commands/openDoor"
    routing:
      - when: "'{{res}}' == 'OK'"
        then:
          - message: "문을 열었습니다."
          - next: "1-1"          # 다시 문 상태 확인
      - when:
        then:
          - alarm: "문 열기 명령이 실패하였습니다."

  # --- 2단계: 소재 로딩 ---
  - id: "2"
    name: "소재 로딩"
    action: "{{acq.sub1}}/robotGateway/commands/loading"
    params: {"material": "TEST01", "goal": "{{acq.main}}"}
    routing:
      - when: "'{{res}}' == 'OK'"
        then:
          - message: "소재 로딩을 완료하였습니다."
          - release: ["{{acq.all}}"]   # 모든 자원 해제
      - when:
        then:
          - alarm: "소재 로딩에 실패하였습니다."
```

### 자원 해제 후 재획득 패턴

스텝 시작 시 `release`로 기존 자원을 먼저 해제하고 새로 `acquire`할 수 있습니다:

```yaml
  - id: "3"
    name: "다음 설비로 이동"
    release: ["{{acq.all}}"]       # 스텝 시작 전 모든 자원 해제
    acquire:
      main: ["NC1", "NC2"]        # 새로 자원 획득
    action: "{{acq.main}}/cncGateway/commands/start"
    routing:
      - when: "'{{res}}' == 'OK'"
        then:
          - next: "4"
      - when:
        then:
          - alarm: "시작 실패"
```

### 변수 활용 패턴

```yaml
  - id: "1-2"
    name: "슬롯 확인"
    action: "{{acq.sub1}}/robotGateway/queries/availableInputSlot"
    routing:
      - when: "{{res}} == None"
        then:
          - alarm: "비어있는 슬롯 없음"
      - when: "{{res}} > 0"
        then:
          - set_val: "{{res}}"      # 슬롯 번호를 var에 저장
          - next: "1-3"
      - when:
        then:
          - alarm: "결과 값 확인 불가: {{res}}"

  - id: "1-3"
    name: "소재 집기"
    action: "{{acq.sub1}}/robotGateway/commands/pick"
    params: {"location": "RACK", "slotId": "{{var}}"}   # 저장된 슬롯 번호 사용
    routing:
      - when: "'{{res}}' == 'OK'"
        then:
          - set_loc: "{{acq.sub1}}"   # 현재 위치 기록
          - set_pos: "{{var}}"        # 세부 위치 기록
          - next: "1-4"
      - when:
        then:
          - alarm: "소재 집기 실패"
```
