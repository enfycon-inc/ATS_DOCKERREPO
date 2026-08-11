# Start Docker Compose services in detached mode
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
docker compose up -d

# Start backend in a new window
# Write-Host "Starting Backend..." -ForegroundColor Cyan
# Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd ats_backend; npm run start:dev"

# Start frontend in a new window
Write-Host "Starting Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd ats_frontend_main; npm run dev"

Write-Host "All services have been launched! (Frontend and Backend will open in separate windows)" -ForegroundColor Green
