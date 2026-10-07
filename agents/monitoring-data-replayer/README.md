# Monitoring Data Replayer Agent

CNC 모니터링 데이터(TDMS, LOG 파일)를 파싱하고 실시간으로 재생하는 에이전트입니다.

## 기능

- **TDMS/LOG 파일 파싱**: nptdms를 사용한 TDMS 바이너리 파싱, TSV 형식 LOG 파싱
- **실시간 리플레이**: 데이터를 실제 시간에 맞춰 재생 (속도 조절 가능)
- **WebSocket 스트리밍**: 실시간으로 클라이언트에 데이터 전송
- **파일 출력**: CSV/JSON 형식으로 저장

## 설치

```bash
cd agents/monitoring-data-replayer
uv sync
```

## 사용법

### Python API

```python
from src import MonitoringDataReplayerAgent
import asyncio

async def main():
    agent = MonitoringDataReplayerAgent()
    
    # 파일 정보 조회
    files = agent.list_files("~/data/tdms/")
    print(files)
    
    info = agent.get_file_info("sample.log")
    print(info)
    
    # 통계 조회
    stats = agent.get_statistics("sample.log")
    print(f"Records: {stats['total_records']}")
    print(f"Cutting ratio: {stats['cutting_ratio']:.1%}")
    
    # 데이터 리플레이 (2배속)
    async for record in agent.replay("sample.log", speed=2.0):
        print(record)

asyncio.run(main())
```

### WebSocket 스트리밍

```python
async def stream_to_websocket():
    agent = MonitoringDataReplayerAgent()
    
    # WebSocket 서버 시작 및 스트리밍
    async for record in agent.replay(
        "sample.log",
        speed=1.0,
        output="websocket",
        websocket_port=8765
    ):
        pass  # Records are broadcast to ws://localhost:8765

asyncio.run(stream_to_websocket())
```

WebSocket 클라이언트 (JavaScript):

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'record') {
        console.log('Spindle RPM:', msg.data.spindle_rpm);
        console.log('Position:', msg.data.position);
    }
};
```

### 파일 출력

```python
async def save_to_file():
    agent = MonitoringDataReplayerAgent()
    
    # CSV로 저장
    async for record in agent.replay(
        "sample.log",
        speed=100.0,  # 100배속
        output="csv"  # sample.output.csv 생성
    ):
        pass
    
    # 또는 커스텀 경로
    async for record in agent.replay(
        "sample.log",
        speed=100.0,
        output="/path/to/output.json"
    ):
        pass

asyncio.run(save_to_file())
```

## 데이터 모델

### MonitoringRecord

| 필드 | 타입 | 원본 컬럼 | 설명 |
|------|------|----------|------|
| timestamp | datetime | time | 타임스탬프 |
| spindle_rpm | float | crpm | 실제 스핀들 RPM |
| cmd_spindle_rpm | float | ccrpm | 명령 스핀들 RPM |
| feedrate | float | cfr | 실제 이송속도 (mm/min) |
| cmd_feedrate | float | ccfr | 명령 이송속도 |
| position | tuple[float, float, float] | cpx, cpy, cpz | X, Y, Z 좌표 |
| gcode_cmd | str | cmdl | 현재 G-code 명령 |
| vibration_rms | float | asprms | 진동 RMS |
| accel_rms | float | aaccrms | 가속도 RMS |
| cutting | bool | cut | 절삭 중 여부 |
| estimated_wear | float | estwear | 예측 공구 마모 |
| estimated_force | float | estforce | 예측 절삭력 |

## 테스트

```bash
uv run pytest -v
```

## 의존성

- nptdms>=1.7.0 - TDMS 파일 파싱
- pandas>=2.0.0 - 데이터 처리
- websockets>=12.0 - WebSocket 서버
- aiofiles>=23.0 - 비동기 파일 I/O
