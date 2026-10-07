# MES 서버 시작 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File start-mes.ps1

$env:PYTHONUTF8="1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MES Server Start Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 기존 프로세스 종료
Write-Host "`n[1/5] 기존 포트 사용 프로세스 종료 중..." -ForegroundColor Yellow

$ports = @(3000, 3001, 3002, 3003, 8000, 8001, 8002, 8003)
foreach ($port in $ports) {
    $procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
             Select-Object -ExpandProperty OwningProcess -Unique
    if ($procs) {
        foreach ($procId in $procs) {
            $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
            Write-Host "  Port $port : PID $procId ($procName) 종료" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 2

# 2. Cell-MES Backend 시작
Write-Host "`n[2/6] Cell-MES Backend 시작 (port 8000)..." -ForegroundColor Yellow
$backendPath = "$PSScriptRoot\agents\cell-mes"
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d `"$backendPath`" && uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

Start-Sleep -Seconds 3

# 3. Mock Middleware 시작
Write-Host "[3/6] Mock Middleware 시작 (port 8003)..." -ForegroundColor Yellow
$mockMiddlewarePath = "$PSScriptRoot\agents\cell-mes\mock-middleware"
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d `"$mockMiddlewarePath`" && uv run uvicorn main:app --host 0.0.0.0 --port 8003 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

# 4. Cell-Scheduler 시작
Write-Host "[4/6] Cell-Scheduler 시작 (port 8002)..." -ForegroundColor Yellow
$schedulerPath = "$PSScriptRoot\agents\cell-scheduler"
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d `"$schedulerPath`" && uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8002 --reload" -WindowStyle Normal

Start-Sleep -Seconds 3

# 5. NL Router 시작
Write-Host "[5/6] NL Router 시작 (port 8001)..." -ForegroundColor Yellow
$nlRouterPath = "$PSScriptRoot\agents\nl-router"
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d `"$nlRouterPath`" && uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8001 --reload" -WindowStyle Normal

Start-Sleep -Seconds 3

# 6. Frontend 시작
Write-Host "[6/6] Frontend 시작 (port 3000)..." -ForegroundColor Yellow
$frontendPath = "$PSScriptRoot\agents\cell-mes\frontend"
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d `"$frontendPath`" && npm run dev" -WindowStyle Normal

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  서버 시작 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  MES API:     http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "  Middleware:  http://localhost:8003" -ForegroundColor White
Write-Host "  Scheduler:   http://localhost:8002/api/docs" -ForegroundColor White
Write-Host "  NL Router:   http://localhost:8001/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "  로그인: admin / admin123" -ForegroundColor Cyan
Write-Host ""
