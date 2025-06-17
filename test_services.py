#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script untuk semua microservices
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Service URLs
EXTRACTION_URL = "http://localhost:5000"
TRANSFORM_URL = "http://localhost:5001"
LOAD_URL = "http://localhost:5002"
AIRFLOW_URL = "http://localhost:8081"

def test_extraction_service():
    """Test extraction service"""
    print("🧪 Testing Extraction Service...")
    
    # Health check
    try:
        response = requests.get(f"{EXTRACTION_URL}/health", timeout=10)
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test extraction
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {"date": yesterday}
        
        print(f"🚀 Starting extraction for date: {yesterday}")
        response = requests.post(
            f"{EXTRACTION_URL}/extract",
            json=payload,
            timeout=300
        )
        
        result = response.json()
        print(f"✅ Extraction result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def test_load_service():
    """Test load service"""
    print("\n🧪 Testing Load Service...")
    
    # Health check
    try:
        response = requests.get(f"{LOAD_URL}/health", timeout=10)
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test stats
    try:
        response = requests.get(f"{LOAD_URL}/stats", timeout=10)
        result = response.json()
        print(f"✅ Database stats: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Stats check failed: {e}")
        return False

def test_transform_service():
    """Test transform service"""
    print("\n🧪 Testing Transform Service...")
    
    # Health check
    try:
        response = requests.get(f"{TRANSFORM_URL}/health", timeout=10)
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test transform
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {"date": yesterday}
        
        print(f"🚀 Starting transform for date: {yesterday}")
        response = requests.post(
            f"{TRANSFORM_URL}/transform",
            json=payload,
            timeout=600
        )
        
        result = response.json()
        print(f"✅ Transform result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Transform failed: {e}")
        return False

def test_full_pipeline():
    """Test full pipeline"""
    print("\n🧪 Testing Full Pipeline...")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Step 1: Extract
    print(f"Step 1: Extract data for {yesterday}")
    if not test_extraction_service():
        return False
    
    # Wait a bit
    time.sleep(5)
    
    # Step 2: Transform
    print(f"Step 2: Transform data for {yesterday}")
    if not test_transform_service():
        return False
    
    # Wait a bit
    time.sleep(5)
    
    # Step 3: Load
    print(f"Step 3: Load data for {yesterday}")
    try:
        payload = {"date": yesterday}
        response = requests.post(f"{LOAD_URL}/load", json=payload, timeout=300)
        result = response.json()
        print(f"✅ Load result: {result}")
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return False
    
    print("\n✅ Full pipeline test completed successfully!")
    return True

def main():
    print("🔬 ETL IQPlus Microservices Test Suite")
    print("=" * 50)
    
    # Test individual services
    extraction_ok = test_extraction_service()
    transform_ok = test_transform_service()
    load_ok = test_load_service()
    
    if extraction_ok and transform_ok and load_ok:
        print("\n🎉 All individual services are working!")
        
        # Test full pipeline
        test_full_pipeline()
    else:
        print("\n❌ Some services are not working properly")

if __name__ == "__main__":
    main()
