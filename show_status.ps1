# ETL IQPlus - Final Status Summary
# Menampilkan ringkasan lengkap setelah cleanup

Write-Host "ETL IQPlus - Final Status Summary" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Project info
$projectRoot = "d:\kuliah\semester 4\Big data\tugas3\ETL-IQPLUS\etl-iqplus"
Write-Host "`nProject: ETL IQPlus Financial News Pipeline" -ForegroundColor Cyan
Write-Host "Location: $projectRoot" -ForegroundColor Gray
Write-Host "Cleanup Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Count files and folders
$totalFiles = (Get-ChildItem $projectRoot -File -Recurse | Where-Object { $_.Name -notlike ".*" }).Count
$totalFolders = (Get-ChildItem $projectRoot -Directory -Recurse | Where-Object { $_.Name -notlike ".*" }).Count
$scriptFiles = (Get-ChildItem $projectRoot -Filter "*.ps1").Count
$pythonFiles = (Get-ChildItem $projectRoot -Filter "*.py" -Recurse).Count
$dockerFiles = (Get-ChildItem $projectRoot -Filter "Dockerfile" -Recurse).Count

Write-Host "`nProject Statistics:" -ForegroundColor Yellow
Write-Host "  Total Files: $totalFiles" -ForegroundColor White
Write-Host "  Total Folders: $totalFolders" -ForegroundColor White
Write-Host "  PowerShell Scripts: $scriptFiles" -ForegroundColor White
Write-Host "  Python Scripts: $pythonFiles" -ForegroundColor White
Write-Host "  Docker Files: $dockerFiles" -ForegroundColor White

# Architecture summary
Write-Host "`nArchitecture:" -ForegroundColor Yellow
Write-Host "  Type: Microservices with Docker Operators" -ForegroundColor White
Write-Host "  Services: 7 (MongoDB, PostgreSQL, Chrome, Ollama, Extract, Transform, Load)" -ForegroundColor White
Write-Host "  Orchestration: Apache Airflow" -ForegroundColor White
Write-Host "  Communication: Docker Network + Shared Volume" -ForegroundColor White

# Key features
Write-Host "`nKey Features:" -ForegroundColor Yellow
Write-Host "  - Web scraping with Selenium" -ForegroundColor White
Write-Host "  - LLM sentiment analysis with Ollama" -ForegroundColor White
Write-Host "  - MongoDB data storage" -ForegroundColor White
Write-Host "  - Docker Operators for isolation" -ForegroundColor White
Write-Host "  - Comprehensive testing suite" -ForegroundColor White
Write-Host "  - Automated deployment scripts" -ForegroundColor White

# Quick start commands
Write-Host "`nQuick Start Commands:" -ForegroundColor Yellow
Write-Host "  Deploy All:    .\deploy_docker_operators.ps1" -ForegroundColor Cyan
Write-Host "  Full Test:     .\test_complete_pipeline.ps1" -ForegroundColor Cyan
Write-Host "  Build Images:  .\build_docker_images.ps1" -ForegroundColor Cyan
Write-Host "  Start Services: .\start_services.ps1" -ForegroundColor Cyan
Write-Host "  Monitor Data:  python monitor_data.py" -ForegroundColor Cyan

# Access URLs
Write-Host "`nAccess Points:" -ForegroundColor Yellow
Write-Host "  Airflow UI:    http://localhost:8081 (admin/admin)" -ForegroundColor Cyan
Write-Host "  MongoDB:       localhost:27017" -ForegroundColor Cyan
Write-Host "  Extract API:   http://localhost:5000" -ForegroundColor Cyan
Write-Host "  Transform API: http://localhost:5001" -ForegroundColor Cyan
Write-Host "  Load API:      http://localhost:5002" -ForegroundColor Cyan

# Documentation
Write-Host "`nDocumentation:" -ForegroundColor Yellow
Write-Host "  Main Guide:        README.md" -ForegroundColor White
Write-Host "  Docker Operators:  README_DOCKER_OPERATORS.md" -ForegroundColor White
Write-Host "  Microservices:     README_MICROSERVICES.md" -ForegroundColor White
Write-Host "  Cleanup Summary:   CLEANUP_SUMMARY.md" -ForegroundColor White

# Project status
Write-Host "`nProject Status:" -ForegroundColor Green
Write-Host "  Structure: Clean and Organized" -ForegroundColor Green
Write-Host "  Dependencies: Properly Separated" -ForegroundColor Green
Write-Host "  Testing: Comprehensive Suite Available" -ForegroundColor Green
Write-Host "  Documentation: Complete and Updated" -ForegroundColor Green
Write-Host "  Deployment: Fully Automated" -ForegroundColor Green

Write-Host "`nProject is ready for deployment and testing!" -ForegroundColor Green
