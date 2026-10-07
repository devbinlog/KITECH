# /start-mes - Start MES Services

Start all Cell-MES related services for development.

## Usage

```
/start-mes
```

## Services Started

| Service | Port | Description |
|---------|------|-------------|
| Cell-MES Backend | 8000 | FastAPI backend |
| Cell-MES Frontend | 3000 | Next.js frontend |
| Cell-Scheduler | 8002 | Scheduling service |
| NL-Router | 8001 | Natural language router |

## Execution

Use the project's start script:

```powershell
.\start-mes.ps1
```

Or start services individually:

```bash
# Backend (from agents/cell-mes directory)
cd agents/cell-mes
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from agents/cell-mes/frontend directory)
cd agents/cell-mes/frontend
npm run dev

# Scheduler (from agents/cell-scheduler directory)
cd agents/cell-scheduler
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8002 --reload

# NL-Router (from agents/nl-router directory)
cd agents/nl-router
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Endpoints After Start

- MES Frontend: http://localhost:3000
- MES API Docs: http://localhost:8000/api/docs
- Scheduler API: http://localhost:8002/api/docs
- NL-Router API: http://localhost:8001/api/docs

## Prerequisites

1. Python 3.11+ with uv installed
2. Node.js 18+ for frontend
3. PostgreSQL database running (for Cell-MES)