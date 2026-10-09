[CmdletBinding()]
param([switch]$SkipDocker)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$node = (Get-Command node -ErrorAction Stop).Source
$logRoot = Join-Path $env:TEMP 'enfysync-local-dev'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

# Only supporting services run in Docker. Application code runs on the host.
if (-not $SkipDocker) {
    Push-Location $projectRoot
    try {
        $backendContainer = docker ps -a --filter 'name=^ats_backend_dev$' --format '{{.Names}}'
        if ($LASTEXITCODE -ne 0) { throw 'Docker is unavailable. Start Docker Desktop or use -SkipDocker.' }
        if ($backendContainer -eq 'ats_backend_dev') {
            docker rm -f ats_backend_dev
            if ($LASTEXITCODE -ne 0) { throw 'Could not remove the local Docker backend.' }
        }
        docker compose up -d redis api worker
        if ($LASTEXITCODE -ne 0) { throw 'Supporting Docker services failed to start.' }
    } finally { Pop-Location }
}

# Host processes cannot use Docker service names. No migrations or seeds run here.
$env:NODE_ENV = 'development'
$env:ATS_SKIP_BOOTSTRAP = 'true'
$env:REDIS_HOST = '127.0.0.1'
$env:REDIS_PORT = '6379'
$env:PYTHON_PARSER_URL = 'http://127.0.0.1:8000'

function Start-LocalDevServer {
    param([string]$Name, [string]$Directory, [string]$Cli, [string[]]$CliArguments, [int]$Port)
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "$Name port $Port is already in use; leaving the existing process running." -ForegroundColor Yellow
        return
    }
    $workDir = Join-Path $projectRoot $Directory
    $cliPath = Join-Path $workDir $Cli
    if (-not (Test-Path -LiteralPath $cliPath)) { throw "$Name dependencies are missing. Install dependencies in $workDir first." }
    $arguments = @(('"' + $cliPath + '"')) + $CliArguments
    $process = Start-Process -FilePath $node -ArgumentList $arguments -WorkingDirectory $workDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot "$Name.log") -RedirectStandardError (Join-Path $logRoot "$Name.error.log")
    Write-Host "$Name development server launched (PID $($process.Id)), port $Port." -ForegroundColor Green
}

Start-LocalDevServer -Name 'backend' -Directory 'ats_backend' -Cli 'node_modules/@nestjs/cli/bin/nest.js' -CliArguments @('start', '--watch') -Port 5000
Start-LocalDevServer -Name 'frontend' -Directory 'ats_frontend_main' -Cli 'node_modules/next/dist/bin/next' -CliArguments @('dev', '--port', '3000') -Port 3000
Write-Host "Frontend: http://localhost:3000 | Backend: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Startup and live reload logs: $logRoot" -ForegroundColor Cyan
