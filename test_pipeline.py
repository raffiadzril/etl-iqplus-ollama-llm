#!/usr/bin/env python3
"""
Test script untuk memverifikasi ETL pipeline IQPlus
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Service URLs
EXTRACTION_URL = "http://localhost:5000"
TRANSFORM_URL = "http://localhost:5001"
LOAD_URL = "http://localhost:5002"
OLLAMA_URL = "http://localhost:11434"

def test_service_health():
    """Test health endpoints dari semua services"""
    print("🔍 Testing service health...")
    
    services = {
        "Extraction": f"{EXTRACTION_URL}/health",
        "Transform": f"{TRANSFORM_URL}/health", 
        "Load": f"{LOAD_URL}/health"
    }
    
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service} Service: {response.json()}")
            else:
                print(f"❌ {service} Service: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {service} Service: {e}")
    
    # Test Ollama
    try:
        response = requests.get(OLLAMA_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama Service: Running")
        else:
            print(f"❌ Ollama Service: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama Service: {e}")

def test_extraction_service():
    """Test extraction service dengan tanggal sample"""
    print("\n📰 Testing Extraction Service...")
    
    # Test dengan tanggal hari ini untuk mendapatkan berita terbaru
    today = datetime.now().strftime("%Y-%m-%d")
    
    payload = {"date": today}
    
    try:
        print(f"🚀 Calling extraction for date: {today}")        
        response = requests.post(
            f"{EXTRACTION_URL}/extract",
            json=payload,
            timeout=300  # 5 menit timeout untuk scraping
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Extraction success: {result}")
            return result
        else:
            print(f"❌ Extraction failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return None

def test_transform_service(extraction_result=None):
    """Test transform service"""
    print("\n🤖 Testing Transform Service...")
    
    # Test dengan tanggal hari ini
    today = datetime.now().strftime("%Y-%m-%d")
    
    payload = {"date": today}
    
    try:
        print(f"🚀 Calling transform for date: {today}")
        response = requests.post(
            f"{TRANSFORM_URL}/transform",
            json=payload,
            timeout=120  # 2 menit timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transform success: {result}")
            return result
        else:
            print(f"❌ Transform failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Transform error: {e}")
        return None

def test_load_service(transform_result=None):
    """Test load service"""
    print("\n💾 Testing Load Service...")
    
    # Test dengan tanggal hari ini
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Dummy JSON file path untuk testing
    json_file = f"/app/data/transformed_news_{today.replace('-', '')}.json"
    
    payload = {
        "json_file": json_file,
        "date": today
    }
    
    try:
        print(f"🚀 Calling load for file: {json_file}")
        response = requests.post(
            f"{LOAD_URL}/load/json",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Load success: {result}")
            return result
        else:
            print(f"❌ Load failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Load error: {e}")
        return None

def test_analytics_service():
    """Test analytics generation"""
    print("\n📊 Testing Analytics Service...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    payload = {"date": today}
    
    try:
        print(f"🚀 Generating analytics for date: {today}")
        response = requests.post(
            f"{LOAD_URL}/analytics/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analytics success: {result}")
            return result
        else:
            print(f"❌ Analytics failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return None

def main():
    """Main test function"""
    print("🔧 ETL IQPlus Pipeline Test")
    print("=" * 50)
    
    # Test health endpoints
    test_service_health()
    
    # Test extraction
    extraction_result = test_extraction_service()
    
    # Test transform (jika extraction berhasil)
    if extraction_result:
        transform_result = test_transform_service(extraction_result)
    else:
        transform_result = test_transform_service()  # Test tanpa hasil extraction
    
    # Test load
    load_result = test_load_service(transform_result)
    
    # Test analytics
    analytics_result = test_analytics_service()
    
    print("\n🏁 Test Summary:")
    print("=" * 50)
    print(f"✅ Extraction: {'Success' if extraction_result else 'Failed/No data'}")
    print(f"✅ Transform: {'Success' if transform_result else 'Failed'}")
    print(f"✅ Load: {'Success' if load_result else 'Failed'}")
    print(f"✅ Analytics: {'Success' if analytics_result else 'Failed'}")
    
    if all([extraction_result, transform_result, load_result, analytics_result]):
        print("\n🎉 All tests passed! ETL Pipeline is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
