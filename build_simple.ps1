# Simple Build Script for ETL IQPlus
Write-Host "Building ETL IQPlus Docker Images..." -ForegroundColor Green

$ErrorActionPreference = "Stop"

try {
    # Build Extraction Service
    Write-Host "Building Extraction Service..." -ForegroundColor Yellow
    Set-Location "services\extraction"
    docker build -t etl-iqplus-extraction:latest .
    Set-Location "..\.."
    
    # Build Transform Service  
    Write-Host "Building Transform Service..." -ForegroundColor Yellow
    Set-Location "services\transform"
    docker build -t etl-iqplus-transform:latest .
    Set-Location "..\.."
    
    # Build Load Service
    Write-Host "Building Load Service..." -ForegroundColor Yellow
    Set-Location "services\load"
    docker build -t etl-iqplus-load:latest .
    Set-Location "..\.."
    
    Write-Host "All images built successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "Build failed: $_" -ForegroundColor Red
    Set-Location "..\.." -ErrorAction SilentlyContinue
    exit 1
}
