$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $root ".run"
$pidFile = Join-Path $runDir "server.pid"
$port = if ($env:ZHCE_PORT) { [int]$env:ZHCE_PORT } else { 8000 }

if (-not (Test-Path $pidFile)) {
    Write-Host "[提示] 未找到 PID 文件，服务可能未通过启动脚本运行。" -ForegroundColor Yellow
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        Write-Host "端口 $port 当前由进程 $($listener.OwningProcess) 监听；为避免误杀，请人工确认后再处理。" -ForegroundColor Yellow
    }
    exit 0
}

$serverPid = (Get-Content $pidFile | Select-Object -First 1).Trim()
if (-not $serverPid) {
    Remove-Item $pidFile -Force
    exit 0
}

$process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
if (-not $process) {
    Write-Host "[提示] PID $serverPid 对应进程已不存在，清理 PID 文件。" -ForegroundColor Yellow
    Remove-Item $pidFile -Force
    exit 0
}

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener -and $listener.OwningProcess -ne [int]$serverPid) {
    Write-Host "[警告] PID 文件与端口监听进程不一致，未执行停止操作。" -ForegroundColor Yellow
    Write-Host "        PID 文件：$serverPid；端口监听：$($listener.OwningProcess)" -ForegroundColor Yellow
    exit 1
}

Stop-Process -Id $serverPid -Force
Start-Sleep -Milliseconds 600
Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "[成功] 已停止筑测云服务（PID=$serverPid）。" -ForegroundColor Green
