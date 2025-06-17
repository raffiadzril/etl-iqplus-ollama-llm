# Test Airflow DAG dengan Docker Operators
# Script ini menguji DAG yang menggunakan Docker Operators

Write-Host "🧪 Testing Airflow DAG dengan Docker Operators..." -ForegroundColor Green

$ErrorActionPreference = "Stop"

try {
    # 1. Check Airflow is running
    Write-Host "`n🔍 Checking Airflow services..." -ForegroundColor Yellow
    $airflowStatus = docker-compose ps airflow-webserver
    if ($LASTEXITCODE -ne 0) {
        throw "Airflow webserver is not running. Run start_services.ps1 first!"
    }
    
    # 2. List available DAGs
    Write-Host "`n📋 Listing available DAGs..." -ForegroundColor Yellow
    docker-compose exec -T airflow-webserver airflow dags list
    
    # 3. Test DAG syntax
    Write-Host "`n✅ Testing DAG syntax..." -ForegroundColor Yellow
    $dagTest = docker-compose exec -T airflow-webserver airflow dags test etl_iqplus_docker_operators 2024-01-01
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ DAG syntax test failed!" -ForegroundColor Red
        Write-Host $dagTest -ForegroundColor Red
        exit 1
    }
    
    # 4. Check DAG tasks
    Write-Host "`n📝 Listing DAG tasks..." -ForegroundColor Yellow
    docker-compose exec -T airflow-webserver airflow tasks list etl_iqplus_docker_operators
    
    # 5. Test specific task
    Write-Host "`n🎯 Testing get_target_date task..." -ForegroundColor Yellow
    docker-compose exec -T airflow-webserver airflow tasks test etl_iqplus_docker_operators get_target_date 2024-01-01
    
    # 6. Manual DAG trigger (optional)
    $response = Read-Host "`n🚀 Do you want to trigger the DAG manually? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "⚡ Triggering DAG manually..." -ForegroundColor Yellow
        $runId = "manual_test_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        docker-compose exec -T airflow-webserver airflow dags trigger etl_iqplus_docker_operators --run-id $runId
        
        Write-Host "`n📊 Check DAG run status at: http://localhost:8081" -ForegroundColor Cyan
        Write-Host "   Username: admin" -ForegroundColor Cyan
        Write-Host "   Password: admin" -ForegroundColor Cyan
    }
    
    Write-Host "`n✅ Airflow DAG tests completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ Error testing Airflow DAG: $_" -ForegroundColor Red
    exit 1
}
