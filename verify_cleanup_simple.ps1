# Verify Cleanup - ETL IQPlus Project Structure
# Script untuk memverifikasi bahwa cleanup telah berhasil

Write-Host "🧹 ETL IQPlus - Cleanup Verification" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

$projectRoot = "d:\kuliah\semester 4\Big data\tugas3\ETL-IQPLUS\etl-iqplus"

# Files yang seharusnya TIDAK ADA lagi (telah dihapus)
$removedFiles = @(
    "Dockerfile",
    "Dockerfile.ollama", 
    "ollama-init.sh",
    "requirements_test.txt",
    "dags"
)

# Files yang seharusnya MASIH ADA (file penting)
$requiredFiles = @(
    "docker-compose.yml",
    "README.md",
    "README_DOCKER_OPERATORS.md", 
    "README_MICROSERVICES.md",
    "CLEANUP_SUMMARY.md",
    "requirements.txt",
    "deploy_docker_operators.ps1",
    "test_complete_pipeline.ps1",
    "services\airflow\dags\etl_iqplus_docker_dag.py",
    "services\extraction\Dockerfile",
    "services\transform\Dockerfile", 
    "services\load\Dockerfile"
)

Write-Host "`n🔍 Checking removed files (must NOT exist)..." -ForegroundColor Yellow

$cleanupSuccess = $true

foreach ($file in $removedFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        Write-Host "❌ FAILED: $file still exists" -ForegroundColor Red
        $cleanupSuccess = $false
    } else {
        Write-Host "✅ GOOD: $file removed" -ForegroundColor Green
    }
}

Write-Host "`n🔍 Checking required files (must exist)..." -ForegroundColor Yellow

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        Write-Host "✅ GOOD: $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ MISSING: $file not found" -ForegroundColor Red
        $cleanupSuccess = $false
    }
}

if ($cleanupSuccess) {
    Write-Host "`n🎉 CLEANUP VERIFICATION PASSED!" -ForegroundColor Green
    Write-Host "   Project structure is clean and organized" -ForegroundColor Green
} else {
    Write-Host "`n❌ CLEANUP VERIFICATION FAILED!" -ForegroundColor Red
    Write-Host "   Some files need attention (see errors above)" -ForegroundColor Red
    exit 1
}

Write-Host "`n💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Run: .\deploy_docker_operators.ps1" -ForegroundColor White
Write-Host "   2. Test: .\test_complete_pipeline.ps1" -ForegroundColor White
Write-Host "   3. Monitor: python monitor_data.py" -ForegroundColor White
