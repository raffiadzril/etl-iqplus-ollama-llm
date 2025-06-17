# Quick status check script
Write-Host "🔍 ETL IQPlus Services Status Check" -ForegroundColor Cyan
Write-Host "=" * 40

# Check running containers
Write-Host "`n📦 Running Containers:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n🔗 Service Health:" -ForegroundColor Yellow

# Check each service
$services = @(
    @{name="Extraction Service"; url="http://localhost:5000/health"},
    @{name="Transform Service"; url="http://localhost:5001/health"},
    @{name="Airflow UI"; url="http://localhost:8081"},
    @{name="Ollama"; url="http://localhost:11434"},
    @{name="Chrome Selenium"; url="http://localhost:4444"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.url -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.name) - OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($service.name) - Responded but not 200" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.name) - Not responding" -ForegroundColor Red
    }
}

Write-Host "`n📊 MongoDB Status:" -ForegroundColor Yellow
try {
    $mongoTest = docker exec mongodb mongosh --eval "db.runCommand('ping')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB - OK" -ForegroundColor Green
    } else {
        Write-Host "❌ MongoDB - Not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ MongoDB - Not responding" -ForegroundColor Red
}

Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "   Airflow UI: http://localhost:8081" -ForegroundColor White
Write-Host "   Extraction: http://localhost:5000" -ForegroundColor White  
Write-Host "   Transform:  http://localhost:5001" -ForegroundColor White
