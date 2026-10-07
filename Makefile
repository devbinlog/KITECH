# Makefile — agents-workspace 단일 인터페이스 (Mac + Windows)
#
# Windows에서 사용 시:
#   - WSL: 그대로 `make` 사용 가능
#   - PowerShell: `winget install GnuWin32.Make` 또는 `choco install make`
#                 또는 scripts/*.ps1 직접 실행
#
# Mac/Linux: 표준 `make` 그대로

.PHONY: help up down restart ps logs test check seed reset-db lint format \
        backend-test frontend-build frontend-test pre-commit-install

# OS 감지 (Windows에서 make가 동작할 때)
ifeq ($(OS),Windows_NT)
    SHELL := pwsh.exe
    .SHELLFLAGS := -NoProfile -Command
    SCRIPT_EXT := ps1
else
    SHELL := /bin/bash
    SCRIPT_EXT := sh
endif

help: ## 사용 가능한 타겟 목록
	@echo "agents-workspace Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  up                  Start all services (docker compose up -d)"
	@echo "  down                Stop all services"
	@echo "  restart             Restart all services"
	@echo "  ps                  Show service status"
	@echo "  logs                Tail logs (Ctrl+C to exit)"
	@echo "  test                Run backend pytest (cell-mes)"
	@echo "  backend-test        Same as test"
	@echo "  frontend-build      Build frontend"
	@echo "  frontend-test       Run frontend tsc + tests"
	@echo "  check               ruff + tsc + pytest 통합 검증"
	@echo "  lint                ruff check"
	@echo "  format              ruff format"
	@echo "  seed                Re-seed mes.db"
	@echo "  reset-db            Backup + reset mes.db (interactive)"
	@echo "  pre-commit-install  Install pre-commit hooks"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

test backend-test:
	cd agents/cell-mes && uv run pytest

frontend-build:
	cd agents/cell-mes/frontend && npm run build

frontend-test:
	cd agents/cell-mes/frontend && npm run typecheck

lint:
	uv run ruff check agents/ shared/ orchestrator/

format:
	uv run ruff format agents/ shared/ orchestrator/

check:
ifeq ($(OS),Windows_NT)
	./scripts/check.ps1
else
	./scripts/check.sh
endif

seed:
ifeq ($(OS),Windows_NT)
	./scripts/seed-mes-db.ps1
else
	./scripts/seed-mes-db.sh
endif

reset-db:
ifeq ($(OS),Windows_NT)
	./scripts/seed-mes-db.ps1 -ResetOnly
else
	./scripts/seed-mes-db.sh --reset-only
endif

pre-commit-install:
	uv run pre-commit install
