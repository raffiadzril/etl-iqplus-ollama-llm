# File Extraction Viewer - ETL IQPlus
# Script untuk melihat dan mengekstrak file hasil ETL pipeline

param(
    [string]$Action = "list",
    [string]$Container = "extraction",
    [string]$FileName = "",
    [int]$Lines = 20,
    [string]$OutputDir = ".\extracted_files"
)

$ErrorActionPreference = "Continue"

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
    Write-Title "File Extraction Viewer - ETL IQPlus"
    Write-Host ""
    Write-ColorOutput Green "USAGE:"
    Write-Host "  .\extract_files.ps1 -Action <action> [options]"
    Write-Host ""
    Write-ColorOutput Green "ACTIONS:"
    Write-Host "  list            - List all files in containers"
    Write-Host "  view            - View file content"
    Write-Host "  extract         - Copy files to local directory"
    Write-Host "  latest          - Show latest extraction output"
    Write-Host "  logs            - Show container logs"
    Write-Host "  clean           - Clean old files"
    Write-Host ""
    Write-ColorOutput Green "OPTIONS:"
    Write-Host "  -Container      - Container name (extraction, transform, load)"
    Write-Host "  -FileName       - Specific file name to view/extract"
    Write-Host "  -Lines          - Number of lines to show (default: 20)"
    Write-Host "  -OutputDir      - Local directory for extracted files"
    Write-Host ""
    Write-ColorOutput Green "EXAMPLES:"
    Write-Host "  .\extract_files.ps1 -Action list"
    Write-Host "  .\extract_files.ps1 -Action view -FileName news_2025-06-12.json"
    Write-Host "  .\extract_files.ps1 -Action extract -Container transform"
    Write-Host "  .\extract_files.ps1 -Action latest"
}

function Get-ContainerName($Container) {
    switch ($Container.ToLower()) {
        "extraction" { return "extraction-iqplus" }
        "transform" { return "transform-llm" }
        "load" { return "load-service" }
        default { return $Container }
    }
}

function List-AllFiles {
    Write-Title "FILES IN ALL CONTAINERS"
    
    $containers = @("extraction-iqplus", "transform-llm", "load-service")
    
    foreach ($container in $containers) {
        Write-ColorOutput Yellow "🐳 Container: $container"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Check /shared directory
        Write-ColorOutput Cyan "📁 /shared directory:"
        docker exec $container ls -la /shared/ 2>/dev/null | ForEach-Object {
            if ($_ -match "\.json|\.csv|\.txt") {
                Write-ColorOutput Green "  $_"
            } else {
                Write-Host "  $_"
            }
        }
        
        # Check /tmp directory for temporary files
        Write-ColorOutput Cyan "📁 /tmp directory (recent files):"
        docker exec $container find /tmp -name "*.json" -o -name "*.csv" -o -name "*.txt" -mtime -1 2>/dev/null | ForEach-Object {
            Write-ColorOutput Green "  $_"
        }
        
        Write-Host ""
    }
    
    # Also check local shared directory if exists
    if (Test-Path ".\shared") {
        Write-ColorOutput Yellow "💻 Local shared directory:"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Get-ChildItem ".\shared" -Recurse | Where-Object { $_.Extension -in @('.json', '.csv', '.txt') } | 
            Sort-Object LastWriteTime -Descending | 
            Format-Table Name, Length, LastWriteTime -AutoSize
    }
}

function View-FileContent {
    param([string]$Container, [string]$FileName)
    
    if (-not $FileName) {
        Write-ColorOutput Red "❌ Please specify a filename with -FileName parameter"
        return
    }
    
    $containerName = Get-ContainerName $Container
    Write-Title "FILE CONTENT: $FileName"
    Write-ColorOutput Cyan "📦 Container: $containerName"
    
    # Try different paths
    $paths = @("/shared/$FileName", "/tmp/$FileName", "/$FileName")
    $found = $false
    
    foreach ($path in $paths) {
        $result = docker exec $containerName test -f "$path" 2>/dev/null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ Found file at: $path"
            $found = $true
            
            # Show file info
            Write-ColorOutput Yellow "📊 File Information:"
            docker exec $containerName ls -lh "$path"
            Write-Host ""
            
            # Show content based on file type
            if ($FileName.EndsWith(".json")) {
                Write-ColorOutput Yellow "📄 JSON Content (first $Lines lines):"
                docker exec $containerName head -n $Lines "$path" | ForEach-Object {
                    if ($_ -match '"headline":|"sentiment":|"confidence":') {
                        Write-ColorOutput Green $_
                    } else {
                        Write-Host $_
                    }
                }
                
                Write-Host ""
                Write-ColorOutput Yellow "📊 JSON Statistics:"
                $lineCount = docker exec $containerName wc -l "$path" | ForEach-Object { ($_ -split '\s+')[0] }
                Write-Host "Total lines: $lineCount"
                
                # Count objects in JSON
                $objCount = docker exec $containerName grep -c '"headline"' "$path" 2>/dev/null
                if ($objCount) {
                    Write-Host "Estimated objects: $objCount"
                }
                
            } elseif ($FileName.EndsWith(".csv")) {
                Write-ColorOutput Yellow "📊 CSV Content (first $Lines rows):"
                docker exec $containerName head -n $Lines "$path" | ForEach-Object {
                    if ($_ -match "headline|sentiment|ticker") {
                        Write-ColorOutput Green $_
                    } else {
                        Write-Host $_
                    }
                }
                
                Write-Host ""
                Write-ColorOutput Yellow "📊 CSV Statistics:"
                $lineCount = docker exec $containerName wc -l "$path" | ForEach-Object { ($_ -split '\s+')[0] }
                Write-Host "Total rows: $lineCount"
                
            } else {
                Write-ColorOutput Yellow "📝 Text Content (first $Lines lines):"
                docker exec $containerName head -n $Lines "$path"
            }
            
            break
        }
    }
    
    if (-not $found) {
        Write-ColorOutput Red "❌ File not found: $FileName"
        Write-ColorOutput Yellow "💡 Available files in $containerName:"
        docker exec $containerName find /shared /tmp -name "*.json" -o -name "*.csv" -o -name "*.txt" 2>/dev/null
    }
}

function Extract-Files {
    param([string]$Container)
    
    $containerName = Get-ContainerName $Container
    Write-Title "EXTRACTING FILES FROM $containerName"
    
    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
        Write-ColorOutput Green "✅ Created directory: $OutputDir"
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $containerDir = Join-Path $OutputDir "$Container_$timestamp"
    New-Item -ItemType Directory -Path $containerDir | Out-Null
    
    Write-ColorOutput Yellow "📦 Extracting from container: $containerName"
    Write-ColorOutput Yellow "📁 Output directory: $containerDir"
    
    # Find all relevant files
    $files = docker exec $containerName find /shared /tmp -name "*.json" -o -name "*.csv" -o -name "*.txt" 2>/dev/null
    
    if (-not $files) {
        Write-ColorOutput Red "❌ No files found in $containerName"
        return
    }
    
    $extractedCount = 0
    foreach ($file in $files) {
        if ($file.Trim()) {
            $fileName = Split-Path $file -Leaf
            $localPath = Join-Path $containerDir $fileName
            
            Write-ColorOutput Cyan "📄 Extracting: $file -> $fileName"
            docker cp "$containerName`:$file" $localPath 2>/dev/null
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "  ✅ Success"
                $extractedCount++
            } else {
                Write-ColorOutput Red "  ❌ Failed"
            }
        }
    }
    
    Write-Host ""
    Write-ColorOutput Green "🎉 Extraction completed!"
    Write-Host "📊 Files extracted: $extractedCount"
    Write-Host "📁 Location: $containerDir"
    
    # Show extracted files
    if (Test-Path $containerDir) {
        Write-Host ""
        Write-ColorOutput Yellow "📋 Extracted Files:"
        Get-ChildItem $containerDir | Format-Table Name, Length, LastWriteTime -AutoSize
    }
}

function Show-LatestOutput {
    Write-Title "LATEST EXTRACTION OUTPUT"
    
    # Show latest from extraction service
    Write-ColorOutput Yellow "🔄 Latest Extraction Activity:"
    docker logs extraction-iqplus --tail 15 | ForEach-Object {
        if ($_ -match "✅|🎉|📰|📊") {
            Write-ColorOutput Green $_
        } elseif ($_ -match "❌|⚠️|ERROR") {
            Write-ColorOutput Red $_
        } else {
            Write-Host $_
        }
    }
    
    Write-Host ""
    Write-ColorOutput Yellow "🤖 Latest Transform Activity:"
    docker logs transform-llm --tail 10 | ForEach-Object {
        if ($_ -match "✅|🎉|sentiment") {
            Write-ColorOutput Green $_
        } elseif ($_ -match "❌|⚠️|ERROR") {
            Write-ColorOutput Red $_
        } else {
            Write-Host $_
        }
    }
    
    Write-Host ""
    Write-ColorOutput Yellow "💾 Latest Load Activity:"
    docker logs load-service --tail 10 | ForEach-Object {
        if ($_ -match "✅|🎉|success") {
            Write-ColorOutput Green $_
        } elseif ($_ -match "❌|⚠️|ERROR") {
            Write-ColorOutput Red $_
        } else {
            Write-Host $_
        }
    }
    
    # Show latest files
    Write-Host ""
    Write-ColorOutput Yellow "📁 Latest Files Created:"
    $containers = @("extraction-iqplus", "transform-llm", "load-service")
    foreach ($container in $containers) {
        $latestFile = docker exec $container find /shared -name "*.json" -o -name "*.csv" -printf "%T@ %p\n" 2>/dev/null | 
                     Sort-Object -Descending | Select-Object -First 1
        if ($latestFile) {
            $fileName = ($latestFile -split ' ', 2)[1]
            Write-ColorOutput Cyan "  $container`: $fileName"
        }
    }
}

function Show-ContainerLogs {
    param([string]$Container)
    
    $containerName = Get-ContainerName $Container
    Write-Title "CONTAINER LOGS: $containerName"
    
    Write-ColorOutput Yellow "📋 Recent logs (last $Lines lines):"
    docker logs $containerName --tail $Lines | ForEach-Object {
        if ($_ -match "✅|🎉|SUCCESS|success") {
            Write-ColorOutput Green $_
        } elseif ($_ -match "❌|⚠️|ERROR|error|failed") {
            Write-ColorOutput Red $_
        } elseif ($_ -match "🔄|INFO|processing") {
            Write-ColorOutput Yellow $_
        } else {
            Write-Host $_
        }
    }
}

function Clean-OldFiles {
    Write-Title "CLEANING OLD FILES"
    
    $containers = @("extraction-iqplus", "transform-llm", "load-service")
    
    foreach ($container in $containers) {
        Write-ColorOutput Yellow "🧹 Cleaning $container..."
        
        # Remove files older than 7 days
        $oldFiles = docker exec $container find /shared /tmp -name "*.json" -o -name "*.csv" -mtime +7 2>/dev/null
        
        if ($oldFiles) {
            Write-ColorOutput Cyan "📁 Files to be removed (older than 7 days):"
            foreach ($file in $oldFiles) {
                if ($file.Trim()) {
                    Write-Host "  $file"
                    docker exec $container rm -f "$file" 2>/dev/null
                }
            }
        } else {
            Write-ColorOutput Green "  ✅ No old files to clean"
        }
    }
    
    # Clean local extracted files
    if (Test-Path $OutputDir) {
        Write-ColorOutput Yellow "🧹 Cleaning local extracted files..."
        $oldDirs = Get-ChildItem $OutputDir -Directory | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
        
        if ($oldDirs) {
            Write-ColorOutput Cyan "📁 Local directories to be removed:"
            foreach ($dir in $oldDirs) {
                Write-Host "  $($dir.FullName)"
                Remove-Item $dir.FullName -Recurse -Force
            }
        } else {
            Write-ColorOutput Green "  ✅ No old local files to clean"
        }
    }
    
    Write-ColorOutput Green "🎉 Cleanup completed!"
}

# Main execution
switch ($Action.ToLower()) {
    "help" { Show-Usage }
    "list" { List-AllFiles }
    "view" { View-FileContent -Container $Container -FileName $FileName }
    "extract" { Extract-Files -Container $Container }
    "latest" { Show-LatestOutput }
    "logs" { Show-ContainerLogs -Container $Container }
    "clean" { Clean-OldFiles }
    default { 
        Write-ColorOutput Red "❌ Unknown action: $Action"
        Show-Usage 
    }
}
