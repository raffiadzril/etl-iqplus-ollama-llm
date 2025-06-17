# ETL IQPlus Microservices Stop Script

Write-Host "🛑 Stopping ETL IQPlus Microservices..." -ForegroundColor Red
Write-Host "=" * 50

# Stop all services
Write-Host "📦 Stopping all containers..." -ForegroundColor Yellow
docker-compose down

# Optional: Remove volumes (data cleanup)
$removeData = Read-Host "`nRemove all data volumes? This will delete all MongoDB data! (y/n)"
if ($removeData -eq "y" -or $removeData -eq "Y") {
    Write-Host "🗑️ Removing data volumes..." -ForegroundColor Red
    docker-compose down -v
    Write-Host "✅ All data has been removed" -ForegroundColor Green
} else {
    Write-Host "💾 Data volumes preserved" -ForegroundColor Green
}

# Optional: Remove images
$removeImages = Read-Host "`nRemove built images? (y/n)"
if ($removeImages -eq "y" -or $removeImages -eq "Y") {
    Write-Host "🗑️ Removing built images..." -ForegroundColor Red
    docker images --filter "reference=*etl-iqplus*" -q | ForEach-Object { docker rmi $_ }
    Write-Host "✅ Built images removed" -ForegroundColor Green
}

Write-Host "`n✅ All services stopped!" -ForegroundColor Green
