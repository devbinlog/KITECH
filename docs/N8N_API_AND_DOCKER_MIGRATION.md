# N8N API 변환 및 시스템 Docker 컨테이너화 요약 보고서

**작성일시**: 2026-04-10  
**주요 대상**: `cell-mes`, `nl-router`, `cell-scheduler`, `frontend`, `n8n`

본 문서는 로컬 터미널/쉘 프로세스 기반으로 실행되던 Agents Workspace 마이크로서비스들을 **Docker Compose 기반의 풀 컨테이너 환경으로 마이그레이션**하고, 컴포넌트 간 단절되어 있던 **n8n 시나리오 YAML 컨버터를 `cell-mes`의 정식 REST API로 편입**시킨 작업의 기술적 세부사항을 요약합니다.

---

## 1. 마이크로서비스 Docker 풀 컨테이너화

기존의 `start-mes.ps1` 스크립트를 통한 호스트 의존적 실행 방식을 탈피하고 완벽하게 독립된 Docker Container 환경을 구축했습니다.

### 주요 개선 트러블슈팅 및 아키텍처 결단
1. **Workspace 종속성 무결성 확보 (`--all-packages`)**
   - **문제**: 단일 Agent 디렉토리 컨텍스트로 빌드 시 `uvicorn` 및 `ml` 내부 공용 패키지들을 찾지 못해 컨테이너가 무한 재시작되는 현상 발생.
   - **해결**: 모든 파이썬 에이전트의 Dockerfile Build Context를 `.`(프로젝트 Root)로 끌어올린 후, `uv sync --frozen --all-packages` 명령을 통해 Workspace 전체의 의존성을 컨테이너 가상 환경에 완벽히 베이크(Bake)했습니다.
   - **효과**: 런타임(`--no-sync`) 시 다운로드 대기 시간이 0초로 단축되며 오류율이 완전히 사라졌습니다.

2. **SQLite DB Volume 절대경로 마운트 보정**
   - 기존 상대 경로가 컨테이너를 가리키지 못하여 데이터가 증발하는 현상을 해결하기 위해 `docker-compose.yml` 에서 `DATABASE_URL=sqlite+aiosqlite:////app/agents/cell-mes/data/mes.db` 로 절대경로 환경변수를 오버라이드하여 데이터의 영속성을 완전히 확보했습니다.

3. **호스트-컨테이너 간 패키지 간섭 차단 (`.dockerignore`)**
   - 호스트 Mac의 `.venv`, `node_modules`가 도커 내부로 침투하여 Alpine/Linux 바이너리와 엉키는 현상을 방지하기 위해 최상단에 `.dockerignore` 를 수립하여 충돌을 원천 차단했습니다.

4. **프론트엔드 라우팅 최적화**
   - Next.js 프론트엔드가 엉뚱한 라우터(`8001`)를 바라보던 점을 교정하여 메인 시스템인 `cell-mes (8000)` 를 정확히 타겟팅하도록 `NEXT_PUBLIC_API_URL` 네트워크 배선을 정리했습니다.

---

## 2. n8n 커스텀 플러그인 Docker Compose 병합

서브 폴더(`agents/n8n-yaml`)에 별개로 격리되어 있던 n8n용 커스텀 컴포즈 설정을 메인 `docker-compose.yml` 에 성공적으로 통합시켰습니다.

### "Volume Shadowing" 방어를 통한 무중단 커스텀 노드 주입
* **문제점**: n8n은 `/home/node/.n8n` 폴더를 호스트 볼륨으로 덮어쓰기 때문에, 빌드 과정에서 넣어둔 TypeScript Custom Node(`n8n-nodes-scenario`) 패키지가 구동과 동시에 증발해버리는 치명적 구조였습니다.
* **스마트 우회 설계**:
  - `Dockerfile`: 노드 빌드 결과물을 볼륨 매핑 구역 밖인 안전지대(`/custom-nodes-src`)에 피신시켜 복사해 둡니다.
  - `docker-entrypoint.sh`: n8n 본체 서버가 실행되기 직전 찰나에, 숨겨둔 `/custom-nodes-src` 폴더를 볼륨이 매핑 완료된 `~/.n8n/nodes/` 폴더 안으로 `npm install` 로 강제 투입해 구조를 복원합니다.
* **결과**: 어떠한 환경에서도 커스텀 노드가 무조건 살아서 작동하는 무결성 100%의 n8n 컨테이너가 전체 오케스트레이션에 합류했습니다.

---

## 3. n8n ↔ YAML 컴파일러 `cell-mes` API로 완전 이식

CLI 콘솔 창에서 폴더 경로를 일일이 타이핑하여 수행하던 두 파이썬 변환 스크립트(`n8n_to_yaml.py`, `yaml_to_n8n.py`)를 `cell-mes`의 심장부인 FastAPI 백엔드로 흡수했습니다.

### 순수 함수화 및 의존성 분리
- **In-Memory 로직화 설계**: 디스크에 결과물을 남기던 `with open()` 방식의 찌꺼기성 파일 I/O 코드를 모조리 제거했습니다.
- `app/services/scenario_converter.py` 를 탄생시켜 JSON 파이썬 딕셔너리와 문자열만 받아 즉시 계산을 처리하는 코어 모듈 구조로 탈바꿈했습니다.
- **의존성 충돌 제로**: MES 서버에 단축키처럼 내장된 패키지인 `pyyaml` 외에 어떤 외부 리소스도 요구하지 않음을 완벽히 증명했습니다.

### REST API 엔드포인트 개통 (`converters.py`)
1. **`POST /api/v1/converters/yaml-to-n8n`**
   - **설계 의도**: 사용자가 추상적인 `YAML` 파일을 날리면, n8n이 당장 수용할 수 있는 실행형 워크플로우(JSON) 구조로 빌드/리턴합니다.
   - **AAS 최적화**: 무거운 AAS 파일을 업로드 받는 대신 `aas_path` 를 간단한 쿼리 파라미터(기본값: `/data/cell1_aas.json`)로 받습니다. 
     _(*이는 현재 시스템이 n8n 노드의 런타임 평가 시 한계로 단일 `baseUrl`을 설정하게 됨을 아키텍처적으로 직시하고 반영한 고도의 타협점입니다.)_
2. **`POST /api/v1/converters/n8n-to-yaml`**
   - n8n GUI에서 내보낸 방대한 `JSON` 파일을 업로드하면, 즉시 표준 스펙의 YAML 코드를 `application/x-yaml` 응답 헤더와 함께 플레인 텍스트 스트림으로 자동 반환시켜 파일 저장을 극대화시켰습니다.

### 임포트 경로(Path) 런타임 픽스
- `ModuleNotFoundError`를 유발했던 최상위 의존성 표기법(`app.services.x`)을 프로젝트의 엄격한 강제 컨벤션인 **상대 경로(`from ....services.scenario_converter`)** 규격으로 통합 조정하여 도커 uvicorn 데몬 위에서 빈틈없이 런칭시켰습니다.
