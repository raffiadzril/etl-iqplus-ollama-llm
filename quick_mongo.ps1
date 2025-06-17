# Quick MongoDB Commands - ETL IQPlus
# Shortcut commands untuk operasi MongoDB yang sering digunakan

Write-Host "🗄️ MongoDB Quick Commands - ETL IQPlus" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Quick status check
Write-Host ""
Write-Host "📊 QUICK STATUS:" -ForegroundColor Yellow
docker exec mongodb mongosh --eval "
use iqplus_db;
print('📄 Raw News: ' + db.raw_news.countDocuments());
print('🤖 Processed News: ' + db.processed_news.countDocuments());
print('💾 Final News: ' + db.final_news.countDocuments());
print('📊 Analytics: ' + db.news_analytics.countDocuments());
"

Write-Host ""
Write-Host "🚀 AVAILABLE COMMANDS:" -ForegroundColor Green
Write-Host "1. .\monitor_mongodb.ps1 -Action status          # Full database status"
Write-Host "2. .\monitor_mongodb.ps1 -Action processed       # View processed news"
Write-Host "3. .\monitor_mongodb.ps1 -Action analytics       # View analytics summary"
Write-Host "4. .\monitor_mongodb.ps1 -Action sentiment       # Sentiment distribution"
Write-Host "5. .\monitor_mongodb.ps1 -Action tickers         # Top tickers analysis"
Write-Host "6. .\extract_files.ps1 -Action list             # List all files"
Write-Host "7. .\extract_files.ps1 -Action latest           # Latest extraction output"
Write-Host "8. .\extract_files.ps1 -Action extract          # Extract files to local"

Write-Host ""
Write-Host "🔍 SEARCH EXAMPLES:" -ForegroundColor Cyan
Write-Host ".\monitor_mongodb.ps1 -Action search -Ticker TLKM"
Write-Host ".\monitor_mongodb.ps1 -Action search -Sentiment positive -Limit 10"
Write-Host ".\monitor_mongodb.ps1 -Action search -Date 2025-06-12"

Write-Host ""
Write-Host "📁 FILE OPERATIONS:" -ForegroundColor Magenta
Write-Host ".\extract_files.ps1 -Action view -FileName <filename>"
Write-Host ".\extract_files.ps1 -Action extract -Container extraction"
Write-Host ".\extract_files.ps1 -Action logs -Container transform"

Write-Host ""
Write-Host "💡 For detailed help, run:" -ForegroundColor Yellow
Write-Host "   .\monitor_mongodb.ps1 -Action help"
Write-Host "   .\extract_files.ps1 -Action help"
