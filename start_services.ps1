# ETL IQPlus Microservices Startup Script
# Run this script to start all services

Write-Host "🚀 Starting ETL IQPlus Microservices..." -ForegroundColor Green
Write-Host "=" * 50

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Check if docker-compose.yml exists
if (!(Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found in current directory" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Building and starting all services..." -ForegroundColor Yellow
Write-Host "This may take a while for the first run..." -ForegroundColor Yellow

# Build and start services
docker-compose up --build -d

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep 30

# Check service status
Write-Host "`n🔍 Checking service status..." -ForegroundColor Cyan

$services = @(
    @{name="mongodb"; port=27017; url="mongodb://localhost:27017"},
    @{name="postgres"; port=5432; url="postgresql://localhost:5432"},
    @{name="selenium-chrome"; port=4444; url="http://localhost:4444"},
    @{name="ollama"; port=11434; url="http://localhost:11434"},
    @{name="extraction-iqplus"; port=5000; url="http://localhost:5000/health"},
    @{name="transform-llm"; port=5001; url="http://localhost:5001/health"},
    @{name="airflow-webserver"; port=8081; url="http://localhost:8081"}
)

foreach ($service in $services) {
    $container = docker ps --filter "name=$($service.name)" --format "table {{.Names}}\t{{.Status}}"
    if ($container -match "Up") {
        Write-Host "✅ $($service.name) is running" -ForegroundColor Green
    } else {
        Write-Host "❌ $($service.name) is not running" -ForegroundColor Red
    }
}

Write-Host "`n🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "   Airflow UI: http://localhost:8081 (admin/admin)" -ForegroundColor White
Write-Host "   Extraction Service: http://localhost:5000" -ForegroundColor White
Write-Host "   Transform Service: http://localhost:5001" -ForegroundColor White
Write-Host "   MongoDB: mongodb://localhost:27017" -ForegroundColor White
Write-Host "   Ollama: http://localhost:11434" -ForegroundColor White

Write-Host "`n🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f [service-name]" -ForegroundColor White
Write-Host "   Stop all: docker-compose down" -ForegroundColor White
Write-Host "   Restart: docker-compose restart [service-name]" -ForegroundColor White
Write-Host "   Test services: python test_services.py" -ForegroundColor White
Write-Host "   Monitor data: python monitor_data.py" -ForegroundColor White

Write-Host "`n🎉 All services should be starting up!" -ForegroundColor Green
Write-Host "Wait a few more minutes for Ollama to download the phi3 model..." -ForegroundColor Yellow

# Optional: Open Airflow in browser
$openBrowser = Read-Host "`nOpen Airflow UI in browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:8081"
}
