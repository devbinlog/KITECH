$ports = @(8000, 8001, 8002, 8003, 3000, 3001)
foreach ($port in $ports) {
    $procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($procs) {
        foreach ($procId in $procs) {
            Write-Host "Killing process $procId on port $port"
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 2

$dbPath = "agents\cell-mes\data\mes.db"
if (Test-Path $dbPath) {
    Write-Host "Deleting $dbPath"
    Remove-Item -Path $dbPath -Force
}

cd agents\cell-mes
Write-Host "Running Alembic Migrations..."
uv run alembic upgrade head

Write-Host "Running Seed Data..."
uv run python -m src.seed_data
cd ..
Write-Host "Database reset complete."
