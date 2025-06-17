#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Docker Operators untuk ETL IQPlus Pipeline
Script ini menjalankan test end-to-end menggunakan Docker Operators
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timedelta
import pytz

def run_command(command, description, timeout=300):
    """Run shell command dengan timeout"""
    print(f"🚀 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def test_docker_image_exists(image_name):
    """Test apakah Docker image sudah ada"""
    command = f"docker images -q {image_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() != ""

def test_extraction_docker():
    """Test extraction service dengan Docker"""
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    command = f"""docker run --rm \
        --network etl_network \
        -v etl-iqplus_shared_data:/shared \
        -e TARGET_DATE={target_date} \
        -e MONGO_URI=mongodb://mongodb:27017/ \
        -e SELENIUM_HUB_URL=http://chrome:4444/wd/hub \
        etl-iqplus-extraction:latest \
        python /app/entrypoint.py {target_date}"""
    
    return run_command(command, f"Testing extraction Docker untuk tanggal {target_date}", timeout=900)

def test_transform_docker():
    """Test transform service dengan Docker"""
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    command = f"""docker run --rm \
        --network etl_network \
        -v etl-iqplus_shared_data:/shared \
        -e TARGET_DATE={target_date} \
        -e MONGO_URI=mongodb://mongodb:27017/ \
        -e OLLAMA_BASE_URL=http://ollama:11434 \
        etl-iqplus-transform:latest \
        python /app/entrypoint.py {target_date}"""
    
    return run_command(command, f"Testing transform Docker untuk tanggal {target_date}", timeout=1800)

def test_load_docker():
    """Test load service dengan Docker"""
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    command = f"""docker run --rm \
        --network etl_network \
        -v etl-iqplus_shared_data:/shared \
        -e TARGET_DATE={target_date} \
        -e MONGO_URI=mongodb://mongodb:27017/ \
        etl-iqplus-load:latest \
        python /app/entrypoint.py {target_date}"""
    
    return run_command(command, f"Testing load Docker untuk tanggal {target_date}", timeout=600)

def check_shared_volume():
    """Check isi shared volume"""
    command = "docker run --rm -v etl-iqplus_shared_data:/shared alpine ls -la /shared"
    return run_command(command, "Checking shared volume contents")

def main():
    """Main test function"""
    print("🧪 Testing ETL IQPlus Docker Operators")
    print("=" * 50)
    
    # 1. Check Docker images
    print("\n📦 Checking Docker Images...")
    images = [
        "etl-iqplus-extraction:latest",
        "etl-iqplus-transform:latest", 
        "etl-iqplus-load:latest"
    ]
    
    missing_images = []
    for image in images:
        if test_docker_image_exists(image):
            print(f"✅ {image} - EXISTS")
        else:
            print(f"❌ {image} - MISSING")
            missing_images.append(image)
    
    if missing_images:
        print(f"\n❌ Missing images: {missing_images}")
        print("   Run build_docker_images.ps1 first!")
        return False
    
    # 2. Check Docker network
    print("\n🌐 Checking Docker Network...")
    if not run_command("docker network inspect etl_network", "Checking etl_network"):
        print("   Network etl_network not found. Run docker-compose up first!")
        return False
    
    # 3. Check shared volume
    print("\n💾 Checking Shared Volume...")
    check_shared_volume()
    
    # 4. Test individual services
    print("\n🔍 Testing Individual Services...")
    
    # Test extraction
    print("\n" + "="*30)
    print("Testing Extraction Service")
    print("="*30)
    if not test_extraction_docker():
        print("❌ Extraction test failed!")
        return False
    
    # Test transform (jika extraction berhasil)
    print("\n" + "="*30)
    print("Testing Transform Service")
    print("="*30)
    if not test_transform_docker():
        print("❌ Transform test failed!")
        return False
    
    # Test load (jika transform berhasil)
    print("\n" + "="*30)
    print("Testing Load Service")
    print("="*30)
    if not test_load_docker():
        print("❌ Load test failed!")
        return False
    
    # 5. Final check
    print("\n📊 Final Check - Shared Volume Contents:")
    check_shared_volume()
    
    print("\n🎉 All Docker Operator tests passed!")
    print("\n💡 Next steps:")
    print("   1. Test Airflow DAG dengan Docker Operators")
    print("   2. Run: docker-compose exec airflow-webserver airflow dags test etl_iqplus_docker_operators")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
