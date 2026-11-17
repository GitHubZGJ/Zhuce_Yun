$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$python = Join-Path $root ".venv\Scripts\python.exe"
$serverPython = Join-Path $root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $serverPython)) { $serverPython = $python }
$runDir = Join-Path $root ".run"
$pidFile = Join-Path $runDir "server.pid"
$logFile = Join-Path $runDir "server.log"
$errFile = Join-Path $runDir "server.err.log"
$port = if ($env:ZHCE_PORT) { [int]$env:ZHCE_PORT } else { 8000 }
$baseUrl = "http://127.0.0.1:$port"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

if (-not (Test-Path $python)) {
    Write-Host "[错误] 未找到 Python 虚拟环境：$python" -ForegroundColor Red
    Write-Host "请先在项目根目录执行：python -m venv .venv 并安装 backend/requirements.txt" -ForegroundColor Yellow
    exit 1
}

if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($listener -and $listener.OwningProcess -eq [int]$oldPid) {
            Write-Host "[提示] 服务已在运行，PID=$oldPid，地址 $baseUrl" -ForegroundColor Green
            exit 0
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$occupied = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($occupied) {
    Write-Host "[错误] 端口 $port 已被进程 $($occupied.OwningProcess) 占用，未启动新服务。" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] 应用数据库迁移..." -ForegroundColor Cyan
Push-Location $backend
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic 迁移失败" }

    Write-Host "[2/3] 检查演示数据..." -ForegroundColor Cyan
    & $python seed.py
    if ($LASTEXITCODE -ne 0) { throw "演示数据初始化失败" }
}
finally {
    Pop-Location
}

Write-Host "[3/3] 启动 FastAPI 服务..." -ForegroundColor Cyan
$process = Start-Process -FilePath $serverPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$port" `
    -WorkingDirectory $backend `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -PassThru -WindowStyle Hidden

$actualPid = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        $actualPid = $listener.OwningProcess
        break
    }
    if ($process.HasExited) { break }
}

if (-not $actualPid) {
    Write-Host "[错误] 服务启动失败，最近日志：" -ForegroundColor Red
    if (Test-Path $errFile) { Get-Content $errFile -Tail 20 }
    if (Test-Path $logFile) { Get-Content $logFile -Tail 20 }
    exit 1
}

Set-Content -Path $pidFile -Value $actualPid -Encoding ascii
Write-Host "[成功] 筑测云已启动：$baseUrl" -ForegroundColor Green
Write-Host "        API 文档：$baseUrl/api/docs" -ForegroundColor Green
Write-Host "        PID=$actualPid（已写入 .run/server.pid）" -ForegroundColor Green
Write-Host "        停止服务：scripts\stop.bat" -ForegroundColor DarkGray
