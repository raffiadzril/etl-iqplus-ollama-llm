# MongoDB Monitor Script untuk ETL IQPlus
# Script untuk monitoring MongoDB dan melihat hasil extraction

param(
    [string]$Action = "status",
    [string]$Collection = "all",
    [int]$Limit = 5,
    [string]$Ticker = "",
    [string]$Sentiment = "",
    [string]$Date = ""
)

$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput($ForegroundColor, $Message) {
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Title($Title) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Show-Usage {
    Write-Title "MongoDB Monitor - ETL IQPlus"
    Write-Host ""
    Write-ColorOutput Green "USAGE:"
    Write-Host "  .\monitor_mongodb.ps1 -Action <action> [options]"
    Write-Host ""
    Write-ColorOutput Green "ACTIONS:"
    Write-Host "  status          - Show database status and counts"
    Write-Host "  raw             - Show raw news data"
    Write-Host "  processed       - Show processed news with sentiment"
    Write-Host "  analytics       - Show analytics summary"
    Write-Host "  sentiment       - Show sentiment distribution"
    Write-Host "  tickers         - Show top tickers"
    Write-Host "  search          - Search news by criteria"
    Write-Host "  export          - Export data to files"
    Write-Host "  files           - Show extraction files"
    Write-Host ""
    Write-ColorOutput Green "OPTIONS:"
    Write-Host "  -Collection     - Specify collection (raw, processed, analytics)"
    Write-Host "  -Limit          - Number of records to show (default: 5)"
    Write-Host "  -Ticker         - Filter by ticker symbol (e.g., TLKM)"
    Write-Host "  -Sentiment      - Filter by sentiment (positive, negative, neutral)"
    Write-Host "  -Date           - Filter by date (yyyy-MM-dd)"
    Write-Host ""
    Write-ColorOutput Green "EXAMPLES:"
    Write-Host "  .\monitor_mongodb.ps1 -Action status"
    Write-Host "  .\monitor_mongodb.ps1 -Action processed -Limit 10"
    Write-Host "  .\monitor_mongodb.ps1 -Action search -Ticker TLKM -Sentiment positive"
    Write-Host "  .\monitor_mongodb.ps1 -Action files"
}

function Test-MongoConnection {
    Write-ColorOutput Yellow "🔄 Checking MongoDB connection..."
    $result = docker exec mongodb mongosh --eval "db.adminCommand('ping').ok" iqplus_db 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ MongoDB is connected"
        return $true
    } else {
        Write-ColorOutput Red "❌ MongoDB connection failed"
        return $false
    }
}

function Show-DatabaseStatus {
    Write-Title "DATABASE STATUS"
    
    if (-not (Test-MongoConnection)) {
        return
    }

    Write-ColorOutput Yellow "📊 Database Statistics:"
    docker exec mongodb mongosh --eval "
        var stats = db.stats();
        print('Database Size: ' + (stats.dataSize / 1024 / 1024).toFixed(2) + ' MB');
        print('Storage Size: ' + (stats.storageSize / 1024 / 1024).toFixed(2) + ' MB');
        print('Collections: ' + stats.collections);
        print('Objects: ' + stats.objects);
    " iqplus_db

    Write-Host ""
    Write-ColorOutput Yellow "📈 Collection Counts:"
    docker exec mongodb mongosh --eval "
        print('📄 raw_news: ' + db.raw_news.countDocuments());
        print('🤖 processed_news: ' + db.processed_news.countDocuments());
        print('💾 final_news: ' + db.final_news.countDocuments());
        print('📊 news_analytics: ' + db.news_analytics.countDocuments());
    " iqplus_db

    Write-Host ""
    Write-ColorOutput Yellow "⏰ Latest Updates:"
    docker exec mongodb mongosh --eval "
        var latest = db.processed_news.findOne({}, {}, {sort: {processed_at: -1}});
        if(latest) {
            print('Latest processed: ' + latest.processed_at);
            print('Latest headline: ' + latest.headline.substring(0, 80) + '...');
        }
        var analytics = db.news_analytics.findOne({}, {}, {sort: {generated_at: -1}});
        if(analytics) {
            print('Latest analytics: ' + analytics.generated_at);
        }
    " iqplus_db
}

function Show-RawNews {
    Write-Title "RAW NEWS DATA"
    
    $query = "{}"
    if ($Date) {
        $query = "{extracted_at: {\`$regex: '$Date'}}"
    }

    Write-ColorOutput Yellow "📄 Showing $Limit raw news records..."
    docker exec mongodb mongosh --eval "
        db.raw_news.find($query).sort({extracted_at: -1}).limit($Limit).forEach(function(doc) {
            print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            print('📰 ' + doc.headline);
            print('🔗 ' + doc.link);
            print('📅 ' + doc.published_at + ' | Extracted: ' + doc.extracted_at);
            print('📝 ' + doc.content.substring(0, 200) + '...');
            print('');
        });
    " iqplus_db
}

function Show-ProcessedNews {
    Write-Title "PROCESSED NEWS WITH SENTIMENT"
    
    $query = "{}"
    $conditions = @()
    
    if ($Ticker) { $conditions += "tickers: '$Ticker'" }
    if ($Sentiment) { $conditions += "sentiment: '$Sentiment'" }
    if ($Date) { $conditions += "processed_at: {\`$regex: '$Date'}" }
    
    if ($conditions.Count -gt 0) {
        $query = "{" + ($conditions -join ", ") + "}"
    }

    Write-ColorOutput Yellow "🤖 Showing $Limit processed news records..."
    if ($conditions.Count -gt 0) {
        Write-ColorOutput Cyan "🔍 Filters: $($conditions -join ' | ')"
    }

    docker exec mongodb mongosh --eval "
        db.processed_news.find($query).sort({processed_at: -1}).limit($Limit).forEach(function(doc) {
            print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            print('📰 ' + doc.headline);
            
            var sentimentColor = doc.sentiment === 'positive' ? '🟢' : 
                               doc.sentiment === 'negative' ? '🔴' : '🟡';
            print('📊 Sentiment: ' + sentimentColor + ' ' + doc.sentiment.toUpperCase() + 
                  ' (Confidence: ' + (doc.confidence * 100).toFixed(1) + '%)');
            
            print('🏢 Tickers: ' + doc.tickers.join(', '));
            print('📅 ' + doc.published_at + ' | Processed: ' + doc.processed_at);
            print('🧠 Reasoning: ' + doc.reasoning);
            print('');
        });
    " iqplus_db
}

function Show-Analytics {
    Write-Title "ANALYTICS SUMMARY"
    
    docker exec mongodb mongosh --eval "
        var analytics = db.news_analytics.findOne({}, {}, {sort: {generated_at: -1}});
        if(analytics) {
            print('📊 LATEST ANALYTICS REPORT');
            print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            print('📅 Date: ' + analytics.date);
            print('⏰ Generated: ' + analytics.generated_at);
            print('📄 Total News: ' + analytics.total_news);
            print('📊 Average Confidence: ' + (analytics.average_confidence * 100).toFixed(1) + '%');
            print('');
            print('📈 SENTIMENT DISTRIBUTION:');
            print('🟢 Positive: ' + analytics.sentiment_distribution.positive + 
                  ' (' + analytics.sentiment_percentage.positive.toFixed(1) + '%)');
            print('🟡 Neutral: ' + analytics.sentiment_distribution.neutral + 
                  ' (' + analytics.sentiment_percentage.neutral.toFixed(1) + '%)');
            print('🔴 Negative: ' + analytics.sentiment_distribution.negative + 
                  ' (' + analytics.sentiment_percentage.negative.toFixed(1) + '%)');
            print('');
            print('🏆 TOP TICKERS:');
            analytics.top_tickers.slice(0, 10).forEach(function(ticker, index) {
                print((index + 1) + '. ' + ticker[0] + ': ' + ticker[1] + ' news');
            });
        } else {
            print('❌ No analytics data found');
        }
    " iqplus_db
}

function Show-SentimentDistribution {
    Write-Title "SENTIMENT DISTRIBUTION"
    
    docker exec mongodb mongosh --eval "
        print('📊 OVERALL SENTIMENT DISTRIBUTION:');
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        db.processed_news.aggregate([
            {\`$group: {_id: '\`$sentiment', count: {\`$sum: 1}}},
            {\`$sort: {count: -1}}
        ]).forEach(function(result) {
            var icon = result._id === 'positive' ? '🟢' : 
                      result._id === 'negative' ? '🔴' : '🟡';
            print(icon + ' ' + result._id.toUpperCase() + ': ' + result.count + ' news');
        });
        
        print('');
        print('📈 SENTIMENT BY CONFIDENCE LEVEL:');
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        db.processed_news.aggregate([
            {\`$group: {
                _id: '\`$sentiment',
                avg_confidence: {\`$avg: '\`$confidence'},
                count: {\`$sum: 1}
            }},
            {\`$sort: {avg_confidence: -1}}
        ]).forEach(function(result) {
            print(result._id.toUpperCase() + ': ' + 
                  (result.avg_confidence * 100).toFixed(1) + '% avg confidence (' + 
                  result.count + ' news)');
        });
    " iqplus_db
}

function Show-TopTickers {
    Write-Title "TOP TICKERS ANALYSIS"
    
    docker exec mongodb mongosh --eval "
        print('🏆 TOP 15 MOST MENTIONED TICKERS:');
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        db.processed_news.aggregate([
            {\`$unwind: '\`$tickers'},
            {\`$group: {_id: '\`$tickers', count: {\`$sum: 1}}},
            {\`$sort: {count: -1}},
            {\`$limit: 15}
        ]).forEach(function(result, index) {
            var medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
            print(medal + ' ' + (index + 1).toString().padStart(2) + '. ' + 
                  result._id + ': ' + result.count + ' news');
        });
        
        print('');
        print('📊 SENTIMENT BREAKDOWN FOR TOP 5 TICKERS:');
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        var topTickers = db.processed_news.aggregate([
            {\`$unwind: '\`$tickers'},
            {\`$group: {_id: '\`$tickers', count: {\`$sum: 1}}},
            {\`$sort: {count: -1}},
            {\`$limit: 5}
        ]).toArray();
        
        topTickers.forEach(function(ticker) {
            print('🏢 ' + ticker._id + ':');
            db.processed_news.aggregate([
                {\`$match: {tickers: ticker._id}},
                {\`$group: {_id: '\`$sentiment', count: {\`$sum: 1}}},
                {\`$sort: {count: -1}}
            ]).forEach(function(sentiment) {
                var icon = sentiment._id === 'positive' ? '🟢' : 
                          sentiment._id === 'negative' ? '🔴' : '🟡';
                print('   ' + icon + ' ' + sentiment._id + ': ' + sentiment.count);
            });
            print('');
        });
    " iqplus_db
}

function Search-News {
    Write-Title "SEARCH NEWS"
    
    $conditions = @()
    if ($Ticker) { $conditions += "Ticker: $Ticker" }
    if ($Sentiment) { $conditions += "Sentiment: $Sentiment" }
    if ($Date) { $conditions += "Date: $Date" }
    
    if ($conditions.Count -eq 0) {
        Write-ColorOutput Red "❌ Please specify search criteria (-Ticker, -Sentiment, or -Date)"
        return
    }
    
    Write-ColorOutput Cyan "🔍 Search Criteria: $($conditions -join ' | ')"
    Show-ProcessedNews
}

function Export-Data {
    Write-Title "EXPORT DATA"
    
    $exportDir = ".\data_export"
    if (-not (Test-Path $exportDir)) {
        New-Item -ItemType Directory -Path $exportDir | Out-Null
        Write-ColorOutput Green "✅ Created export directory: $exportDir"
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    
    Write-ColorOutput Yellow "📤 Exporting processed news to JSON..."
    docker exec mongodb mongoexport --db=iqplus_db --collection=processed_news --out="/tmp/processed_news_$timestamp.json"
    docker cp mongodb:"/tmp/processed_news_$timestamp.json" "$exportDir/"
    
    Write-ColorOutput Yellow "📤 Exporting sentiment summary to CSV..."
    docker exec mongodb mongoexport --db=iqplus_db --collection=processed_news --type=csv --fields=headline,sentiment,confidence,tickers,published_at --out="/tmp/sentiment_summary_$timestamp.csv"
    docker cp mongodb:"/tmp/sentiment_summary_$timestamp.csv" "$exportDir/"
    
    Write-ColorOutput Yellow "📤 Exporting analytics to JSON..."
    docker exec mongodb mongoexport --db=iqplus_db --collection=news_analytics --out="/tmp/analytics_$timestamp.json"
    docker cp mongodb:"/tmp/analytics_$timestamp.json" "$exportDir/"
    
    Write-ColorOutput Green "✅ Export completed! Files saved to: $exportDir"
    Get-ChildItem $exportDir | Where-Object { $_.Name -like "*$timestamp*" } | Format-Table Name, Length, LastWriteTime
}

function Show-ExtractionFiles {
    Write-Title "EXTRACTION FILES"
    
    Write-ColorOutput Yellow "📁 Checking extraction output files..."
    
    # Check shared volume
    $sharedPath = ".\shared"
    if (Test-Path $sharedPath) {
        Write-ColorOutput Green "📂 Local shared directory:"
        Get-ChildItem $sharedPath -Recurse | Where-Object { $_.Name -like "*.json" -or $_.Name -like "*.csv" } | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -First 10 | 
            Format-Table Name, Length, LastWriteTime -AutoSize
    }
    
    # Check inside extraction container
    Write-ColorOutput Yellow "🐳 Files inside extraction container:"
    docker exec extraction-iqplus find /shared -name "*.json" -o -name "*.csv" 2>/dev/null | Sort-Object
    
    # Check inside transform container
    Write-ColorOutput Yellow "🤖 Files inside transform container:"
    docker exec transform-llm find /shared -name "*.json" -o -name "*.csv" 2>/dev/null | Sort-Object
    
    # Show latest extraction log
    Write-ColorOutput Yellow "📋 Latest extraction activity:"
    docker logs extraction-iqplus --tail 10
}

function Show-ExtractionFileContent {
    param([string]$FilePath)
    
    if (-not $FilePath) {
        Write-ColorOutput Yellow "📁 Available files in shared directory:"
        docker exec extraction-iqplus ls -la /shared/ 2>/dev/null
        return
    }
    
    Write-Title "FILE CONTENT: $FilePath"
    
    if ($FilePath.EndsWith(".json")) {
        Write-ColorOutput Yellow "📄 JSON Content (first 5 records):"
        docker exec extraction-iqplus head -n 20 "/shared/$FilePath" 2>/dev/null
    } elseif ($FilePath.EndsWith(".csv")) {
        Write-ColorOutput Yellow "📊 CSV Content (first 10 rows):"
        docker exec extraction-iqplus head -n 10 "/shared/$FilePath" 2>/dev/null
    } else {
        Write-ColorOutput Yellow "📝 Text Content:"
        docker exec extraction-iqplus cat "/shared/$FilePath" 2>/dev/null
    }
}

# Main execution
switch ($Action.ToLower()) {
    "help" { Show-Usage }
    "status" { Show-DatabaseStatus }
    "raw" { Show-RawNews }
    "processed" { Show-ProcessedNews }
    "analytics" { Show-Analytics }
    "sentiment" { Show-SentimentDistribution }
    "tickers" { Show-TopTickers }
    "search" { Search-News }
    "export" { Export-Data }
    "files" { Show-ExtractionFiles }
    "content" { Show-ExtractionFileContent -FilePath $Collection }
    default { 
        Write-ColorOutput Red "❌ Unknown action: $Action"
        Show-Usage 
    }
}
