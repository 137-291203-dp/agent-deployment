# Agent LLM Deployment System - Startup Script
# This script builds and starts the entire system

Write-Host "🚀 Agent LLM Deployment System - Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down
Write-Host ""

# Build the application
Write-Host "Building application..." -ForegroundColor Yellow
docker compose build web
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build completed" -ForegroundColor Green
Write-Host ""

# Start all services
Write-Host "Starting all services..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Services started" -ForegroundColor Green
Write-Host ""

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "Checking service health..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Application is healthy!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Application may still be starting..." -ForegroundColor Yellow
}
Write-Host ""

# Display service information
Write-Host "🎉 Agent LLM Deployment System is running!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   API:          http://localhost:8000" -ForegroundColor White
Write-Host "   Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health:       http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "📊 Services:" -ForegroundColor Cyan
Write-Host "   PostgreSQL:   Running on port 5432" -ForegroundColor White
Write-Host "   Redis:        Running on port 6379" -ForegroundColor White
Write-Host "   ChromaDB:     Running on port 8001" -ForegroundColor White
Write-Host ""
Write-Host "📝 View logs:" -ForegroundColor Cyan
Write-Host "   docker compose logs -f web" -ForegroundColor White
Write-Host ""
Write-Host "Stop services:" -ForegroundColor Cyan
Write-Host "   docker compose down" -ForegroundColor White
Write-Host ""
