Write-Host "Starting backend service..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload" -WindowStyle Normal -WorkingDirectory "$PSScriptRoot"

Start-Sleep -Seconds 3

Write-Host "Starting frontend service..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm run dev" -WindowStyle Normal -WorkingDirectory "$PSScriptRoot"

Write-Host "Services started successfully!"
Write-Host "Backend service: http://localhost:8001"
Write-Host "Frontend service: http://localhost:3000"
Write-Host "Backend API docs: http://localhost:8001/docs"
