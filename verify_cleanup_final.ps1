# ETL IQPlus - Cleanup Verification
Write-Host "ETL IQPlus - Cleanup Verification" -ForegroundColor Green

$projectRoot = "d:\kuliah\semester 4\Big data\tugas3\ETL-IQPLUS\etl-iqplus"

# Files yang telah dihapus
$removedFiles = @("Dockerfile", "Dockerfile.ollama", "ollama-init.sh", "requirements_test.txt", "dags")

# Files yang harus ada
$requiredFiles = @(
    "docker-compose.yml",
    "README.md", 
    "requirements.txt",
    "deploy_docker_operators.ps1",
    "services\airflow\dags\etl_iqplus_docker_dag.py",
    "services\extraction\Dockerfile",
    "services\transform\Dockerfile",
    "services\load\Dockerfile"
)

Write-Host "`nChecking removed files..." -ForegroundColor Yellow
$cleanupSuccess = $true

foreach ($file in $removedFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        Write-Host "FAILED: $file still exists" -ForegroundColor Red
        $cleanupSuccess = $false
    } else {
        Write-Host "GOOD: $file removed" -ForegroundColor Green
    }
}

Write-Host "`nChecking required files..." -ForegroundColor Yellow
foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        Write-Host "GOOD: $file exists" -ForegroundColor Green
    } else {
        Write-Host "MISSING: $file not found" -ForegroundColor Red
        $cleanupSuccess = $false
    }
}

if ($cleanupSuccess) {
    Write-Host "`nCLEANUP VERIFICATION PASSED!" -ForegroundColor Green
    Write-Host "Project structure is clean and organized" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Run: .\deploy_docker_operators.ps1" -ForegroundColor White
    Write-Host "2. Test: .\test_complete_pipeline.ps1" -ForegroundColor White
} else {
    Write-Host "`nCLEANUP VERIFICATION FAILED!" -ForegroundColor Red
    exit 1
}
