# Build Docker Images untuk ETL IQPlus Microservices
# Script ini membangun semua Docker images yang dibutuhkan untuk Docker Operators

Write-Host "🚀 Building Docker Images untuk ETL IQPlus Microservices..." -ForegroundColor Green

# Set error action
$ErrorActionPreference = "Stop"

try {
    # Build Extraction Service
    Write-Host "`n📦 Building Extraction Service..." -ForegroundColor Yellow
    Set-Location "services\extraction"
    docker build -t etl-iqplus-extraction:latest .
    if ($LASTEXITCODE -ne 0) { throw "Failed to build extraction service" }
    
    # Build Transform Service
    Write-Host "`n📦 Building Transform Service..." -ForegroundColor Yellow
    Set-Location "..\transform"
    docker build -t etl-iqplus-transform:latest .
    if ($LASTEXITCODE -ne 0) { throw "Failed to build transform service" }
    
    # Build Load Service
    Write-Host "`n📦 Building Load Service..." -ForegroundColor Yellow
    Set-Location "..\load"
    docker build -t etl-iqplus-load:latest .
    if ($LASTEXITCODE -ne 0) { throw "Failed to build load service" }
    
    # Return to root directory
    Set-Location "..\.."
    
    Write-Host "`n✅ All Docker images built successfully!" -ForegroundColor Green
    
    # List built images
    Write-Host "`n📋 Built Images:" -ForegroundColor Cyan
    docker images | Select-String "etl-iqplus"
    
} catch {
    Write-Host "`n❌ Error building Docker images: $_" -ForegroundColor Red
    Set-Location "..\.." -ErrorAction SilentlyContinue
    exit 1
}
