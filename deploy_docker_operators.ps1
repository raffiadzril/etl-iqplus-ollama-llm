# Deploy ETL IQPlus dengan Docker Operators
# Script lengkap untuk deployment dan testing

Write-Host "🚀 ETL IQPlus Deployment dengan Docker Operators" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

$ErrorActionPreference = "Stop"

function Test-Command {
    param($CommandName)
    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    return $command -ne $null
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$TimeoutSeconds = 120
    )
    
    Write-Host "⏳ Waiting for $ServiceName to be ready..." -ForegroundColor Yellow
    $timeout = [datetime]::Now.AddSeconds($TimeoutSeconds)
    
    while ([datetime]::Now -lt $timeout) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $ServiceName is ready!" -ForegroundColor Green
                return $true
            }
        } catch {
            # Service not ready yet
        }
        Start-Sleep -Seconds 5
    }
    
    Write-Host "❌ $ServiceName failed to start within $TimeoutSeconds seconds" -ForegroundColor Red
    return $false
}

try {
    # 1. Pre-requisites check
    Write-Host "`n🔍 Checking prerequisites..." -ForegroundColor Cyan
    
    if (-not (Test-Command "docker")) {
        throw "Docker is not installed or not in PATH"
    }
    
    if (-not (Test-Command "docker-compose")) {
        throw "Docker Compose is not installed or not in PATH"
    }
    
    Write-Host "✅ Docker and Docker Compose are available" -ForegroundColor Green
    
    # 2. Stop existing services
    Write-Host "`n🛑 Stopping existing services..." -ForegroundColor Yellow
    docker-compose down -v 2>$null
    
    # 3. Build Docker images
    Write-Host "`n📦 Building Docker images..." -ForegroundColor Cyan
    .\build_docker_images.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to build Docker images"
    }
    
    # 4. Start infrastructure services
    Write-Host "`n🏗️ Starting infrastructure services..." -ForegroundColor Cyan
    docker-compose up -d mongodb postgres chrome ollama
    
    # Wait for infrastructure
    Write-Host "`n⏳ Waiting for infrastructure services..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # 5. Start microservices
    Write-Host "`n🚀 Starting microservices..." -ForegroundColor Cyan
    docker-compose up -d extraction-iqplus transform-llm load-service
    
    # Wait for microservices
    if (-not (Wait-ForService "Extraction Service" "http://localhost:5000/health")) {
        throw "Extraction service failed to start"
    }
    
    if (-not (Wait-ForService "Transform Service" "http://localhost:5001/health")) {
        throw "Transform service failed to start"
    }
    
    if (-not (Wait-ForService "Load Service" "http://localhost:5002/health")) {
        throw "Load service failed to start"
    }
    
    # 6. Start Airflow
    Write-Host "`n✈️ Starting Airflow..." -ForegroundColor Cyan
    docker-compose up -d airflow-webserver airflow-scheduler
    
    if (-not (Wait-ForService "Airflow" "http://localhost:8081/health" 180)) {
        Write-Host "⚠️ Airflow might still be starting up..." -ForegroundColor Yellow
    }
    
    # 7. Test Docker Operators
    Write-Host "`n🧪 Testing Docker Operators..." -ForegroundColor Cyan
    python test_docker_operators.py
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Operators test failed"
    }
    
    # 8. Test Airflow DAG
    Write-Host "`n🧪 Testing Airflow DAG..." -ForegroundColor Cyan
    .\test_airflow_dag.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Airflow DAG test failed"
    }
    
    # 9. Show status
    Write-Host "`n📊 Deployment Status:" -ForegroundColor Green
    docker-compose ps
    
    Write-Host "`n🎉 ETL IQPlus dengan Docker Operators berhasil di-deploy!" -ForegroundColor Green
    Write-Host "`n📋 Access Information:" -ForegroundColor Cyan
    Write-Host "   🌐 Airflow UI: http://localhost:8081 (admin/admin)" -ForegroundColor White
        Write-Host "   📊 MongoDB: localhost:27017" -ForegroundColor White
    Write-Host "   🚀 Extraction API: http://localhost:5000" -ForegroundColor White
    Write-Host "   🧠 Transform API: http://localhost:5001" -ForegroundColor White
    Write-Host "   📥 Load API: http://localhost:5002" -ForegroundColor White
    
    Write-Host "`n💡 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Open Airflow UI dan aktifkan DAG 'etl_iqplus_docker_operators'" -ForegroundColor White
    Write-Host "   2. Trigger DAG manually atau tunggu scheduled run" -ForegroundColor White
    Write-Host "   3. Monitor progress melalui Airflow UI" -ForegroundColor White
    Write-Host "   4. Check MongoDB untuk hasil ETL" -ForegroundColor White
    
} catch {
    Write-Host "`n❌ Deployment failed: $_" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "   1. Check Docker is running" -ForegroundColor White
    Write-Host "   2. Check logs: docker-compose logs [service-name]" -ForegroundColor White
    Write-Host "   3. Check services: docker-compose ps" -ForegroundColor White
    Write-Host "   4. Restart: .\stop_services.ps1 && .\deploy_docker_operators.ps1" -ForegroundColor White
    exit 1
}
