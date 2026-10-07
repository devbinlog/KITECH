# seed-mes-db.ps1 — Re-create cell-mes SQLite DB from latest migrations + fixtures.
# PowerShell 7+ compatible.
#
# Usage:
#   ./scripts/seed-mes-db.ps1              # default — reset & seed
#   ./scripts/seed-mes-db.ps1 -ResetOnly   # only delete DB
#   ./scripts/seed-mes-db.ps1 -NoReset     # skip reset, only seed
[CmdletBinding()]
param(
    [switch]$ResetOnly,
    [switch]$NoReset
)

$ErrorActionPreference = 'Stop'

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir    = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$DbPath     = Join-Path $RootDir 'agents\cell-mes\data\mes.db'
$ArchiveDir = Join-Path $RootDir 'agents\cell-mes\data\_archive'

$Reset = -not $NoReset
$Seed  = -not $ResetOnly

if (-not (Test-Path $ArchiveDir)) {
    New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null
}

if ($Reset -and (Test-Path $DbPath)) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backup = Join-Path $ArchiveDir "mes.db.bak.$ts"
    Write-Host "[seed-mes-db] backing up existing DB -> $backup"
    Copy-Item -Path $DbPath -Destination $backup -Force
    Remove-Item -Path $DbPath -Force
}

if ($Seed) {
    Write-Host '[seed-mes-db] running alembic migrations...'
    Push-Location (Join-Path $RootDir 'agents\cell-mes')
    try {
        uv run alembic upgrade head
        if (-not $?) { throw 'alembic upgrade failed' }

        $seedScript = Join-Path (Get-Location) 'tests\fixtures\seed.py'
        if (Test-Path $seedScript) {
            Write-Host '[seed-mes-db] applying seed fixtures...'
            uv run python $seedScript
            if (-not $?) { throw 'seed.py failed' }
        } else {
            Write-Host '[seed-mes-db] no seed.py - skipping fixtures'
        }
    } finally {
        Pop-Location
    }
}

Write-Host "[seed-mes-db] done. DB at $DbPath"
