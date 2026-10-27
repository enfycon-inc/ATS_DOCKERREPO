[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$localEnvPath = Join-Path $projectRoot 'local18.env'
$localCompose = Join-Path $projectRoot 'docker-compose.local-app.yml'
$logsDir = Join-Path $projectRoot '.local-dev-logs'
$backendDir = Join-Path $projectRoot 'ats_backend'
$frontendDir = Join-Path $projectRoot 'ats_frontend_main'

if (Test-Path -LiteralPath $localEnvPath -PathType Container) {
    throw "'$localEnvPath' is a directory, but the launcher needs a credentials file at that path. Rename or remove this empty directory, then rerun the launcher to restore/copy the existing credentials file. The database was not changed."
}

if (-not (Test-Path -LiteralPath $localEnvPath -PathType Leaf)) {
    $legacyEnvPath = Join-Path (Join-Path $env:LOCALAPPDATA 'ATS_DOCKERREPO\local-postgres-replica') 'local18.env'
    if (Test-Path -LiteralPath $legacyEnvPath -PathType Leaf) {
        try {
            Copy-Item -LiteralPath $legacyEnvPath -Destination $localEnvPath -ErrorAction Stop
        } catch {
            throw "Cannot read the existing local replica credentials. Grant this Windows account read access to '$legacyEnvPath', then rerun this script. No database password was changed."
        }
    } elseif (Test-Path -LiteralPath $legacyEnvPath -PathType Container) {
        throw "The previous credentials path '$legacyEnvPath' is a directory, not a file. Restore the original ATS_LOCAL_REPLICA18_PASSWORD in a project-root local18.env file before starting the existing database."
    } else {
        throw "Local replica credentials were not found at '$localEnvPath' or the previous location '$legacyEnvPath'. Restore the existing ATS_LOCAL_REPLICA18_PASSWORD before starting the already-initialized database."
    }
}
try {
    $localEnv = Get-Content -LiteralPath $localEnvPath -Raw -ErrorAction Stop | ConvertFrom-StringData
} catch {
    throw "Cannot read '$localEnvPath'. Check that it is a regular file and that your Windows account has read access. The database was not changed."
}
$dbPassword = $localEnv['ATS_LOCAL_REPLICA18_PASSWORD'].Trim('"')
if (-not $dbPassword) { throw 'Local replica password is missing.' }
$dbState = docker inspect --format '{{.State.Health.Status}}' ats_local_replica_postgres 2>$null
if ($LASTEXITCODE -ne 0 -or $dbState -ne 'healthy') { throw 'The local PostgreSQL replica is not healthy.' }
$schemaExists = docker exec ats_local_replica_postgres psql -U ats_local_replica -d ats_replica -X -A -t -c "SELECT 1 FROM information_schema.schemata WHERE schema_name='keycloak'" 2>$null
if ($schemaExists -ne '1') {
    docker exec ats_local_replica_postgres psql -U ats_local_replica -d ats_replica -v ON_ERROR_STOP=1 -c 'CREATE SCHEMA keycloak AUTHORIZATION ats_local_replica' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Keycloak schema.' }
}

$networkName = 'ats_local_app'
if (-not (docker network ls --format '{{.Name}}' | Where-Object { $_ -eq $networkName })) {
    docker network create $networkName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local application network.' }
}
$networkAliases = docker inspect --format '{{json .NetworkSettings.Networks}}' ats_local_replica_postgres 2>$null
if (-not $networkAliases -or $networkAliases -notmatch '"ats_local_app"\s*:') {
    docker network connect --alias local-postgres $networkName ats_local_replica_postgres
    if ($LASTEXITCODE -ne 0) { throw 'Could not connect the local replica to the local application network.' }
}

Push-Location $projectRoot
try {
    docker compose --env-file $localEnvPath -f $localCompose up -d local-redis parser worker keycloak
    if ($LASTEXITCODE -ne 0) { throw 'Isolated local Redis, parser, worker, or Keycloak failed to start.' }
} finally { Pop-Location }

$keycloakReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $realmMetadata = Invoke-RestMethod -Uri 'http://127.0.0.1:18080/realms/enfycon-ats/.well-known/openid-configuration' -TimeoutSec 3
        if ($realmMetadata.issuer -eq 'http://localhost:18080/realms/enfycon-ats') { $keycloakReady = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $keycloakReady) { throw 'Local Keycloak did not load the enfycon-ats realm.' }

$env:DATABASE_URL = 'postgresql://ats_local_replica:' + [uri]::EscapeDataString($dbPassword) + '@127.0.0.1:55433/ats_replica?schema=ats&options=-csearch_path%3Dats,mass_mail,public'
$env:AUTH_PROVIDER = 'keycloak'
$localClientSecret = [string](docker exec ats_local_replica_postgres psql -U ats_local_replica -d ats_replica -X -A -t -c "SELECT secret FROM keycloak.client WHERE client_id='enfycon-ats'" 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $localClientSecret.Trim()) { throw 'The local Keycloak client secret was not found in the restored database.' }
$env:KEYCLOAK_CLIENT_SECRET = $localClientSecret.Trim()
$env:KEYCLOAK_ISSUER = 'http://localhost:18080/realms/enfycon-ats'
$env:KEYCLOAK_INTERNAL_URL = 'http://localhost:18080'
$env:REDIS_HOST = '127.0.0.1'
$env:REDIS_PORT = '16379'
$env:PYTHON_PARSER_URL = 'http://127.0.0.1:18000'
$env:LOCAL_DISABLE_OUTBOUND_EMAILS = 'true'
$env:BREVO_APIKEY = ''
$env:ATS_SKIP_BOOTSTRAP = 'true'
$env:NODE_ENV = 'development'

$backendPort = 5000
$frontendPort = 3001
function Stop-ThisProjectServer([int]$Port, [string]$AppDirectory, [string]$StartMarker) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) { return }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
    $ancestors = @()
    while ($process) {
        $ancestors += $process
        if (-not $process.ParentProcessId) { break }
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)" -ErrorAction SilentlyContinue
    }
    $markerProcess = $ancestors | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine.Contains($AppDirectory) -and $_.CommandLine.Contains($StartMarker) } | Select-Object -First 1
    if (-not $markerProcess) { throw "Port $Port belongs to another process; leaving it untouched." }
    & taskkill.exe /PID $markerProcess.ProcessId /T /F | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not restart this repository's local server on port $Port." }
    Start-Sleep -Seconds 1
}
Stop-ThisProjectServer -Port $frontendPort -AppDirectory $frontendDir -StartMarker 'next\dist\bin\next'
Stop-ThisProjectServer -Port $backendPort -AppDirectory $backendDir -StartMarker 'nest.js'
if (Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue) { throw "Local frontend port $frontendPort remains occupied." }
if (Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue) { throw "Local backend port $backendPort remains occupied." }
$env:AUTH_URL = "http://deb.localhost:$frontendPort"
$env:NEXTAUTH_URL = "http://deb.localhost:$frontendPort"
$env:NEXT_PUBLIC_SITE_URL = "http://deb.localhost:$frontendPort"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:$backendPort"
$env:INTERNAL_API_URL = "http://127.0.0.1:$backendPort"

New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
if (-not (Test-Path (Join-Path $backendDir 'node_modules/@nestjs/cli/bin/nest.js'))) { throw 'ATS backend dependencies are missing.' }
if (-not (Test-Path (Join-Path $frontendDir 'node_modules/next/dist/bin/next'))) { throw 'ATS frontend dependencies are missing.' }

$backend = Start-Process -FilePath (Get-Command node).Source -ArgumentList @((Join-Path $backendDir 'node_modules/@nestjs/cli/bin/nest.js'), 'start', '--watch') -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsDir 'backend.log') -RedirectStandardError (Join-Path $logsDir 'backend.error.log')
$frontend = Start-Process -FilePath (Get-Command node).Source -ArgumentList @((Join-Path $frontendDir 'node_modules/next/dist/bin/next'), 'dev', '--port', "$frontendPort") -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsDir 'frontend.log') -RedirectStandardError (Join-Path $logsDir 'frontend.error.log')

Write-Host 'Local ATS environment started:' -ForegroundColor Green
Write-Host "  Frontend: http://localhost:$frontendPort"
Write-Host '  Backend:  http://localhost:5000'
Write-Host '  Keycloak: http://localhost:18080 (realm: enfycon-ats)'
Write-Host '  Database: 127.0.0.1:55433 / ats_replica (ATS: ats + mass_mail; local Keycloak: keycloak)'
Write-Host '  Isolated local Redis: 127.0.0.1:16379; parser: 127.0.0.1:18000; outbound email sending disabled'
Write-Host "  Logs: $logsDir"
Write-Host "  Backend PID: $($backend.Id); frontend PID: $($frontend.Id)"
Write-Host 'No migrations or seed scripts were run.'
