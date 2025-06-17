# Complete Pipeline Test untuk ETL IQPlus Docker Operators
# Script ini menjalankan full end-to-end test dengan validasi lengkap

Write-Host "🧪 ETL IQPlus Complete Pipeline Test" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundWrite-Host "`n🏁 Complete pipeline test finished!" -ForegroundColor Greenolor Green

$ErrorActionPreference = "Continue"  # Continue on errors untuk reporting

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Details = ""
    )
    
    $status = if ($Success) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($Success) { "Green" } else { "Red" }
    
    Write-Host "[$status] $TestName" -ForegroundColor $color
    if ($Details) {
        Write-Host "    $Details" -ForegroundColor Gray
    }
}

function Test-ServiceEndpoint {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Initialize test results
$TestResults = @{
    "Prerequisites" = $false
    "DockerImages" = $false
    "ServiceDeployment" = $false
    "ServiceHealth" = $false
    "DockerOperators" = $false
    "AirflowDAG" = $false
    "EndToEndPipeline" = $false
    "DataValidation" = $false
}

try {
    Write-Host "`n📋 Test Plan:" -ForegroundColor Cyan
    Write-Host "   1. Prerequisites Check" -ForegroundColor White
    Write-Host "   2. Docker Images Build" -ForegroundColor White
    Write-Host "   3. Service Deployment" -ForegroundColor White
    Write-Host "   4. Service Health Check" -ForegroundColor White
    Write-Host "   5. Docker Operators Test" -ForegroundColor White
    Write-Host "   6. Airflow DAG Test" -ForegroundColor White
    Write-Host "   7. End-to-End Pipeline" -ForegroundColor White
    Write-Host "   8. Data Validation" -ForegroundColor White
    
    # Test 1: Prerequisites
    Write-Host "`n🔍 TEST 1: Prerequisites Check" -ForegroundColor Yellow
    
    $dockerOk = Get-Command docker -ErrorAction SilentlyContinue
    $composeOk = Get-Command docker-compose -ErrorAction SilentlyContinue
    $pythonOk = Get-Command python -ErrorAction SilentlyContinue
    
    if ($dockerOk -and $composeOk -and $pythonOk) {
        $TestResults["Prerequisites"] = $true
        Write-TestResult "Prerequisites" $true "Docker, Docker Compose, Python available"
    } else {
        Write-TestResult "Prerequisites" $false "Missing: Docker, Docker Compose, or Python"
        throw "Prerequisites not met"
    }
    
    # Test 2: Docker Images
    Write-Host "`n📦 TEST 2: Docker Images Build" -ForegroundColor Yellow
    
    .\build_docker_images.ps1
    if ($LASTEXITCODE -eq 0) {
        $TestResults["DockerImages"] = $true
        Write-TestResult "Docker Images Build" $true "All images built successfully"
    } else {
        Write-TestResult "Docker Images Build" $false "Build failed"
    }
    
    # Test 3: Service Deployment
    Write-Host "`n🚀 TEST 3: Service Deployment" -ForegroundColor Yellow
    
    # Stop existing services first
    docker-compose down -v 2>$null
    
    # Start services
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        $TestResults["ServiceDeployment"] = $true
        Write-TestResult "Service Deployment" $true "All services started"
        
        # Wait for services to initialize
        Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Gray
        Start-Sleep -Seconds 60
    } else {
        Write-TestResult "Service Deployment" $false "Failed to start services"
    }
    
    # Test 4: Service Health Check
    Write-Host "`n🏥 TEST 4: Service Health Check" -ForegroundColor Yellow
    
    $healthChecks = @{
        "MongoDB" = "http://localhost:27017"
        "Extraction Service" = "http://localhost:5000/health"
        "Transform Service" = "http://localhost:5001/health"
        "Load Service" = "http://localhost:5002/health"
        "Airflow" = "http://localhost:8081/health"
    }
    
    $allHealthy = $true
    foreach ($service in $healthChecks.Keys) {
        $url = $healthChecks[$service]
        $healthy = Test-ServiceEndpoint $service $url
        Write-TestResult $service $healthy $url
        if (-not $healthy) { $allHealthy = $false }
    }
    
    $TestResults["ServiceHealth"] = $allHealthy
    
    # Test 5: Docker Operators
    Write-Host "`n🐳 TEST 5: Docker Operators Test" -ForegroundColor Yellow
    
    python test_docker_operators.py
    if ($LASTEXITCODE -eq 0) {
        $TestResults["DockerOperators"] = $true
        Write-TestResult "Docker Operators" $true "Individual containers working"
    } else {
        Write-TestResult "Docker Operators" $false "Container tests failed"
    }
    
    # Test 6: Airflow DAG
    Write-Host "`n✈️ TEST 6: Airflow DAG Test" -ForegroundColor Yellow
    
    .\test_airflow_dag.ps1
    if ($LASTEXITCODE -eq 0) {
        $TestResults["AirflowDAG"] = $true
        Write-TestResult "Airflow DAG" $true "DAG syntax and tasks validated"
    } else {
        Write-TestResult "Airflow DAG" $false "DAG validation failed"
    }
    
    # Test 7: End-to-End Pipeline
    Write-Host "`n🔄 TEST 7: End-to-End Pipeline" -ForegroundColor Yellow
    
    python test_end_to_end.py
    if ($LASTEXITCODE -eq 0) {
        $TestResults["EndToEndPipeline"] = $true
        Write-TestResult "End-to-End Pipeline" $true "Full pipeline executed"
    } else {
        Write-TestResult "End-to-End Pipeline" $false "Pipeline execution failed"
    }
    
    # Test 8: Data Validation
    Write-Host "`n📊 TEST 8: Data Validation" -ForegroundColor Yellow
    
    python monitor_data.py
    if ($LASTEXITCODE -eq 0) {
        $TestResults["DataValidation"] = $true
        Write-TestResult "Data Validation" $true "Data in MongoDB verified"
    } else {
        Write-TestResult "Data Validation" $false "Data validation failed"
    }
    
    # Generate Test Report
    Write-Host "`n📋 TEST REPORT" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    $passedTests = 0
    $totalTests = $TestResults.Count
    
    foreach ($test in $TestResults.Keys) {
        $success = $TestResults[$test]
        Write-TestResult $test $success
        if ($success) { $passedTests++ }
    }
    
    $successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)
    
    Write-Host "`n📊 SUMMARY:" -ForegroundColor White
    Write-Host "   Tests Passed: $passedTests / $totalTests" -ForegroundColor White
    Write-Host "   Success Rate: $successRate%" -ForegroundColor White
    
    if ($successRate -ge 80) {
        Write-Host "`n🎉 PIPELINE TEST SUCCESSFUL!" -ForegroundColor Green
        Write-Host "   Your ETL IQPlus Docker Operators setup is working!" -ForegroundColor Green
    } elseif ($successRate -ge 60) {
        Write-Host "`n⚠️ PIPELINE TEST PARTIALLY SUCCESSFUL" -ForegroundColor Yellow
        Write-Host "   Some components need attention, but core functionality works" -ForegroundColor Yellow
    } else {
        Write-Host "`n❌ PIPELINE TEST FAILED" -ForegroundColor Red
        Write-Host "   Multiple components need fixing" -ForegroundColor Red
    }
    
    # Save detailed report
    $reportFile = "pipeline_test_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $report = @{
        "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        "test_results" = $TestResults
        "summary" = @{
            "total_tests" = $totalTests
            "passed_tests" = $passedTests
            "success_rate" = $successRate
            "status" = if ($successRate -ge 80) { "SUCCESS" } elseif ($successRate -ge 60) { "PARTIAL" } else { "FAILED" }
        }
    }
    
    $report | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportFile -Encoding UTF8
    Write-Host "`n📄 Detailed report saved to: $reportFile" -ForegroundColor Gray
    
    # Next Steps
    Write-Host "`n💡 NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "   🌐 Access Airflow UI: http://localhost:8081 (admin/admin)" -ForegroundColor White
    Write-Host "   📊 Monitor pipeline: python monitor_data.py" -ForegroundColor White
    Write-Host "   📝 Check logs: docker-compose logs [service-name]" -ForegroundColor White
    Write-Host "   🔄 Trigger manual DAG: Go to Airflow UI > etl_iqplus_docker_operators > Trigger" -ForegroundColor White
    
    if ($successRate -lt 80) {
        Write-Host "`n🔧 TROUBLESHOOTING:" -ForegroundColor Yellow
        Write-Host "   1. Check failed tests above" -ForegroundColor White
        Write-Host "   2. Review service logs: docker-compose logs" -ForegroundColor White
        Write-Host "   3. Restart services: .\stop_services.ps1; .\start_services.ps1" -ForegroundColor White
        Write-Host "   4. Check Docker resources: docker system df" -ForegroundColor White
    }
    
} catch {
    Write-Host "`n❌ Complete pipeline test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🏁 Complete pipeline test finished!" -ForegroundColor Green
