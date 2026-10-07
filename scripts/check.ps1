# check.ps1 — Pre-commit / pre-push integrated quality check.
# PowerShell 7+ compatible.
#
# Usage:
#   ./scripts/check.ps1          # full check
#   ./scripts/check.ps1 -Fast    # skip slow tests
[CmdletBinding()]
param(
    [switch]$Fast
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir   = (Resolve-Path (Join-Path $ScriptDir '..')).Path

Push-Location $RootDir
try {
    Write-Host '==[1/4]== Python lint (ruff check) ==' -ForegroundColor Cyan
    uv run ruff check agents/ shared/ orchestrator/
    if ($LASTEXITCODE -ne 0) { throw 'ruff check failed' }

    Write-Host '==[2/4]== Python format (ruff format --check) ==' -ForegroundColor Cyan
    uv run ruff format --check agents/ shared/ orchestrator/
    if ($LASTEXITCODE -ne 0) { throw "ruff format check failed (run 'make format' to fix)" }

    Write-Host '==[3/4]== TypeScript typecheck (frontend) ==' -ForegroundColor Cyan
    $frontendNm = Join-Path $RootDir 'agents\cell-mes\frontend\node_modules'
    if (Test-Path $frontendNm) {
        Push-Location (Join-Path $RootDir 'agents\cell-mes\frontend')
        try {
            npx tsc --noEmit
            if ($LASTEXITCODE -ne 0) { throw 'tsc failed' }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "⚠️  frontend/node_modules not found - run 'cd agents/cell-mes/frontend && npm install' first. Skipping tsc." -ForegroundColor Yellow
    }

    if (-not $Fast) {
        Write-Host '==[4/4]== Backend tests (pytest) ==' -ForegroundColor Cyan
        Push-Location (Join-Path $RootDir 'agents\cell-mes')
        try {
            uv run pytest -q
            if ($LASTEXITCODE -ne 0) { throw 'pytest failed' }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host '==[4/4]== SKIP (-Fast)' -ForegroundColor DarkGray
    }

    Write-Host ''
    Write-Host '✅ All checks passed.' -ForegroundColor Green
} finally {
    Pop-Location
}
