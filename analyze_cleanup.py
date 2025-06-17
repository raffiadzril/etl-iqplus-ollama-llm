#!/usr/bin/env python3
"""
Script untuk mengidentifikasi file yang bisa dihapus vs file penting
"""

import os
from datetime import datetime

# File-file PENTING yang TIDAK BOLEH dihapus
CRITICAL_FILES = {
    # Core project files
    'docker-compose.yml',
    'requirements.txt', 
    'README.md',
    
    # Documentation
    'README_MICROSERVICES.md',
    'README_MONGODB.md',
    'GETTING_STARTED.md',
    
    # Main scripts
    'start_services.ps1',
    'stop_services.ps1',
    'monitor_mongodb.ps1',
    'quick_mongo.ps1',
    'extract_files.ps1',
    
    # Current working scripts
    'check_status.ps1',
    'show_status.ps1'
}

# File-file yang BISA DIHAPUS (testing, backup, unused)
DELETABLE_FILES = {
    # Test files
    'tes.py',
    'test_airflow_dag.ps1', 
    'test_api_simple.py',
    'test_bahasa_indonesia.py',
    'test_complete_pipeline.ps1',
    'test_docker_operators.py',
    'test_end_to_end.py',
    'test_pipeline.py',
    'test_pipeline_fixed.py',
    'test_services.py',
    'test_summary.py', 
    'test_together_quick.py',
    'debug_transform.py',
    'check_summary.py',
    
    # Backup/alternative files
    'docker-compose-clean.yml',
    'docker-compose-fixed.yml',
    'requirements_test.txt',
    'Dockerfile.ollama',
    'ollama-init.sh',
    
    # Build/deploy scripts (jika tidak dipakai)
    'build_docker_images.ps1',
    'build_simple.ps1', 
    'deploy_docker_operators.ps1',
    
    # Cleanup/verification scripts
    'verify_cleanup.ps1',
    'verify_cleanup_final.ps1', 
    'verify_cleanup_simple.ps1',
    'CLEANUP_SUMMARY.md',
    
    # Unused README
    'README_DOCKER_OPERATORS.md',
    
    # Monitor data (jika tidak dipakai)
    'monitor_data.py'
}

def analyze_files():
    base_path = r"d:\kuliah\semester 4\Big data\tugas3\ETL-IQPLUS\etl-iqplus"
    
    print("=== ANALISIS FILE ETL-IQPLUS ===\n")
    
    # Get all files in directory
    all_files = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isfile(item_path):
            all_files.append(item)
    
    print(f"📁 Total files di root directory: {len(all_files)}\n")
    
    # Critical files
    print("🚨 FILE PENTING (JANGAN DIHAPUS):")
    print("=" * 50)
    critical_found = []
    for file in sorted(all_files):
        if file in CRITICAL_FILES:
            critical_found.append(file)
            size = os.path.getsize(os.path.join(base_path, file))
            print(f"✅ {file:<35} ({size:,} bytes)")
    
    print(f"\nTotal file penting: {len(critical_found)}\n")
    
    # Deletable files  
    print("🗑️  FILE YANG BISA DIHAPUS:")
    print("=" * 50)
    deletable_found = []
    total_size = 0
    for file in sorted(all_files):
        if file in DELETABLE_FILES:
            deletable_found.append(file)
            size = os.path.getsize(os.path.join(base_path, file))
            total_size += size
            print(f"❌ {file:<35} ({size:,} bytes)")
    
    print(f"\nTotal file bisa dihapus: {len(deletable_found)}")
    print(f"Total size yang bisa dihemat: {total_size:,} bytes ({total_size/1024:.1f} KB)\n")
    
    # Unknown files
    unknown_files = []
    for file in all_files:
        if file not in CRITICAL_FILES and file not in DELETABLE_FILES:
            unknown_files.append(file)
    
    if unknown_files:
        print("❓ FILE TIDAK DIKETAHUI (PERLU REVIEW):")
        print("=" * 50)
        for file in sorted(unknown_files):
            size = os.path.getsize(os.path.join(base_path, file))
            print(f"⚠️  {file:<35} ({size:,} bytes)")
        print(f"\nTotal file unknown: {len(unknown_files)}\n")
    
    # Summary
    print("📊 RINGKASAN:")
    print("=" * 30)
    print(f"File penting (keep):     {len(critical_found)}")
    print(f"File bisa dihapus:       {len(deletable_found)}")
    print(f"File perlu review:       {len(unknown_files)}")
    print(f"Total file analyzed:     {len(all_files)}")
    
    return deletable_found

if __name__ == "__main__":
    analyze_files()
