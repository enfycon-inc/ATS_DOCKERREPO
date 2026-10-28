[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$logRoot = Join-Path $env:TEMP 'enfysync-local-dev'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

Write-Host "`n>>> Starting ATS Local Development Stack..." -ForegroundColor Cyan

# ─── 1. Supporting Docker Services ───────────────────────────────────────
if (-not $SkipDocker) {
    Write-Host "Checking Docker status..." -ForegroundColor Gray
    $dockerProc = Start-Process -FilePath "docker" -ArgumentList "version" -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
    $dockerResponded = $false
    if ($dockerProc) {
        $dockerResponded = $dockerProc.WaitForExit(3000)
        if (-not $dockerResponded) {
            Stop-Process -Id $dockerProc.Id -Force -ErrorAction SilentlyContinue
        }
    }

    if ($dockerResponded -and $dockerProc.ExitCode -eq 0) {
        Push-Location $projectRoot
        try {
            Write-Host "Docker is running. Starting Redis and Python Parser containers..." -ForegroundColor Green
            $backendContainer = docker ps -a --filter 'name=^ats_backend_dev$' --format '{{.Names}}' 2>$null
            if ($backendContainer -eq 'ats_backend_dev') {
                docker rm -f ats_backend_dev | Out-Null
            }
            docker compose up -d redis api worker
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Supporting Docker services started." -ForegroundColor Green
            } else {
                Write-Host "Warning: Docker compose returned exit code $LASTEXITCODE. Continuing with host servers..." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Warning: Could not start Docker services. Continuing with host servers..." -ForegroundColor Yellow
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "Docker Desktop is not responding or not running. Skipping Docker containers (using host mode)." -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping Docker services as requested (-SkipDocker)." -ForegroundColor Gray
}

# ─── 2. Host Environment Variables ──────────────────────────────────────
$env:NODE_ENV = 'development'
$env:ATS_SKIP_BOOTSTRAP = 'true'
$env:REDIS_HOST = '127.0.0.1'
$env:REDIS_PORT = '6379'
$env:PYTHON_PARSER_URL = 'http://127.0.0.1:8000'

# ─── 3. Launch Host Servers (Live Terminal Windows by Default) ───────────
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) { $npmCmd = 'npm' }

function Start-LocalDevServer {
    param([string]$Name, [string]$Directory, [string]$Script, [int]$Port)
    $existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "$Name port $Port is already in use (PID $($existing.OwningProcess[0])); leaving existing process running." -ForegroundColor Yellow
        return
    }
    $workDir = Join-Path $projectRoot $Directory
    if (-not (Test-Path -LiteralPath (Join-Path $workDir "package.json"))) {
        throw "$Name directory '$workDir' does not have package.json."
    }

    if ($Silent) {
        $stdoutLog = Join-Path $logRoot "$Name.log"
        $stderrLog = Join-Path $logRoot "$Name.error.log"
        $process = Start-Process -FilePath $npmCmd -ArgumentList "run", $Script -WorkingDirectory $workDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
        Write-Host "$Name launched in background (PID $($process.Id)) on port $Port." -ForegroundColor Green
    } else {
        # Default: Open dedicated live interactive PowerShell window
        $windowTitle = "ATS $Name (Port $Port)"
        $cmd = "`$host.UI.RawUI.WindowTitle = '$windowTitle'; Write-Host '=========================================' -ForegroundColor Cyan; Write-Host '  $windowTitle' -ForegroundColor Green; Write-Host '  Working Dir: $workDir' -ForegroundColor Gray; Write-Host '  Running:     npm run $Script' -ForegroundColor Gray; Write-Host '=========================================`n' -ForegroundColor Cyan; npm run $Script"
        Start-Process powershell.exe -WorkingDirectory $workDir -ArgumentList "-NoExit", "-Command", $cmd
        Write-Host "Opened live terminal window for $Name on port $Port." -ForegroundColor Green
    }
}

Write-Host "Launching Backend API (NestJS)..." -ForegroundColor Gray
Start-LocalDevServer -Name 'Backend' -Directory 'ats_backend' -Script 'start:dev' -Port 5000

Write-Host "Launching Frontend (Next.js)..." -ForegroundColor Gray
Start-LocalDevServer -Name 'Frontend' -Directory 'ats_frontend_main' -Script 'dev' -Port 3000

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:5000" -ForegroundColor Cyan
Write-Host "  Database:  Aiven Cloud PostgreSQL" -ForegroundColor Cyan
if ($Silent) {
    Write-Host "  Mode:      Silent / Background" -ForegroundColor Gray
    Write-Host "  Logs:      $logRoot" -ForegroundColor Gray
} else {
    Write-Host "  Mode:      Two Live Terminal Windows" -ForegroundColor Green
    Write-Host "  (Close the opened PowerShell windows to stop servers)" -ForegroundColor Gray
}
Write-Host "==================================================`n" -ForegroundColor Cyan
