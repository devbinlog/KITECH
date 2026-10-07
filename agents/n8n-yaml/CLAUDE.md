# n8n-project CLAUDE.md

## 프로젝트 개요
AAS(Asset Administration Shell) 기반 제조 시나리오 YAML을 n8n 워크플로우로 변환하고,
n8n에서 수정한 워크플로우를 다시 YAML로 역변환하는 시스템.
Docker Desktop으로 n8n 서버를 실행하며 커스텀 노드를 사용한다.

## 디렉토리 구조
```
n8n-project/
├── CLAUDE.md
├── docker-compose.yml          # n8n 서버 실행 (포트 5678)
├── Dockerfile                  # 커스텀 노드 포함 n8n 이미지
├── docker-entrypoint.sh        # 컨테이너 시작 시 ~/.n8n/nodes/ 에 노드 설치
├── custom-nodes/
│   └── n8n-nodes-scenario/    # TypeScript 커스텀 노드 패키지
│       ├── package.json        # keywords: n8n-community-node-package 필수
│       ├── tsconfig.json
│       ├── index.ts
│       └── nodes/
│           ├── ScenarioConfig/ # 전역 설정 노드 (AAS 로드, lock 초기화)
│           └── ScenarioStep/   # 스텝 실행 노드 (1 YAML step = 1 노드)
├── converters/
│   ├── yaml_to_n8n.py         # YAML → n8n workflow JSON
│   └── n8n_to_yaml.py         # n8n workflow JSON → YAML
├── tests/
│   ├── test_converters.py
│   └── output/                # 변환 결과물 저장 위치
└── data/                      # AAS JSON + 시나리오 YAML 파일들
    ├── aas.json / cell1_aas.json / cell2_aas.json / sample_aas.json
    └── cell1_scenario.yaml / cell2_scenario.yaml / sample2.yaml / response.yaml
```

## 핵심 설계 결정

### 커스텀 노드
- **ScenarioConfig**: 워크플로우 맨 앞에 1번 배치. AAS JSON 파일 로드, assets 맵 초기화, 전역 컨텍스트(lock, acq, var, loc, pos) 생성 후 흘려보냄
- **ScenarioStep**: YAML step 1개 = 노드 1개. acquire/release(lock boolean), 템플릿 변수 해석({{acq.main}}, {{res}} 등), HTTP action 실행, routing 조건 평가, 동적 출력 핀

### lock(boolean) 개념
- 어느 자산이라도 acquire된 상태면 ScenarioContext.lock = true
- acquire/release는 첫/마지막 step뿐 아니라 중간 어느 step에서도 발생 가능
- 전체 컨텍스트가 모든 노드를 흘러다니며 유지됨

### 변환기 규칙
- params는 반드시 flow style로 출력: `{key: value}` (FlowDict 클래스 사용)
- routing의 빈 when(default)은 None으로 처리
- label 필드는 JSON에만 존재, 역변환 시 무시 (라운드트립에 영향 없음)
- YAML 주석(#)은 yaml.safe_load에 의해 손실됨 (불가피)

### Docker 관련 주의사항
- 볼륨(n8n_data)이 /home/node/.n8n 전체를 덮어쓰므로 커스텀 노드는 볼륨 밖에 보관
- /custom-nodes-src/ 에 빌드 결과물 보관
- docker-entrypoint.sh가 컨테이너 시작 시마다 ~/.n8n/nodes/ 에 npm install
- package.json에 keywords: ["n8n-community-node-package"] 와 n8nNodesApiVersion: 1 필수
- n8n-workflow 패키지는 dependencies에 포함 (peerDependencies만으로는 Docker에서 런타임 resolve 실패)

### 변경 사항별 재시작 방법
| 수정 내용 | 필요한 작업 |
|-----------|------------|
| Python 변환기 (.py) | 그냥 다시 실행 |
| TypeScript 노드 (.ts) | docker-compose down → rmi → up --build |
| Dockerfile | docker-compose down → rmi → up --build |
| docker-compose.yml | docker-compose down → up |
| n8n workflow import | 브라우저에서 재import |


## 프로젝트 테스트 방법

1. docker-desktop 설치, pip install pyyaml
2. docker-desktop 실행
3. n8n 서버 빌드 및 실행 : 프로젝트 루트 폴더에서 터미널 열고 
docker-compose up --build
 - Starting n8n... 로그가 보이면 준비 완료
4. http://localhost:5678 접속 후 계정 생성
5. YAML to n8n 워크플로우(json) 변환 : 프로젝트 루트 폴더 경로의 터미널에서
python converters/yaml_to_n8n.py data/response.yaml --aas /data/aas.json -o data/workflow.json
-> 실행 후 data 폴더 내 workflow.json 파일 생성 여부 확인 
6. n8n 접속한 화면에서 우측 상단 점 세개 -> import from file -> workflow.json
7. (선택) 화면 내에서 워크플로우 수정 (기존 노드를 삭제 및 수정하거나 Scenario Step 노드 추가 후 연결)
8. 우측 상단 점 세개 -> download -> 워크플로우가 json 파일로 다운로드됨
9. n8n 워크플로우 to YAML 변환 : 프로젝트 루트 폴더 경로의 터미널에서
python converters/n8n_to_yaml.py data/workflow.json -o data/recovered.yaml
-> 실행 후 data 폴더 내 recovered.yaml 파일 생성 여부 확인
10. 서버 종료 docker-compose down

## 변환기 사용법
```bash
# YAML → n8n JSON
python converters/yaml_to_n8n.py data/cell1_scenario.yaml --aas /data/cell1_aas.json -o workflow.json

# n8n JSON → YAML
python converters/n8n_to_yaml.py workflow.json -o recovered.yaml

# 라운드트립 테스트
python tests/test_converters.py
```

## 미완성 / 추후 개선 사항
- [ ] ScenarioConfig: AAS JSON에서 자산 정보를 자동 파싱하는 기능 (현재는 수동 입력)
- [ ] ScenarioStep acquire UI: 실제 YAML에 정의된 역할 수만큼만 표시 (현재 main/sub1/sub2/sub3 항상 고정 4개 노출)
- [ ] AAS 서버 없이 테스트할 수 있는 mock/dry-run 모드
- [ ] n8n에서 커스텀 노드 정상 인식 확인 (docker-entrypoint 방식으로 수정 완료, 실제 확인 필요)

## 라운드트립 테스트 결과 (2026-03-18)
- cell1_scenario.yaml (28 steps): PASS
- cell2_scenario.yaml (16 steps): PASS
- sample2.yaml (9 steps): PASS
