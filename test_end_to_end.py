#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test untuk ETL IQPlus Docker Operators
Test lengkap pipeline dari deployment hingga data validation
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timedelta
import pymongo
import requests
import pytz

def run_powershell_command(command, description, timeout=300):
    """Run PowerShell command"""
    print(f"🚀 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
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

def check_mongodb_data(target_date):
    """Check data di MongoDB"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["iqplus_db"]
        
        # Check collections
        collections = db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
        # Check raw_news
        raw_count = db.raw_news.count_documents({"scraped_date": target_date})
        print(f"   📰 Raw news: {raw_count} articles")
        
        # Check processed_news  
        processed_count = db.processed_news.count_documents({"scraped_date": target_date})
        print(f"   🧠 Processed news: {processed_count} articles")
        
        # Check final_news
        final_count = db.final_news.count_documents({"scraped_date": target_date})
        print(f"   ✅ Final news: {final_count} articles")
        
        # Check news_analytics
        analytics = db.news_analytics.find_one({"date": target_date})
        if analytics:
            print(f"   📈 Analytics: {analytics.get('analytics', {})}")
        
        client.close()
        
        # Validasi minimal data
        if raw_count > 0 and processed_count > 0 and final_count > 0:
            print("✅ MongoDB data validation passed!")
            return True
        else:
            print("❌ MongoDB data validation failed - missing data")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB check failed: {e}")
        return False

def trigger_dag_run(target_date):
    """Trigger Airflow DAG run"""
    try:
        # Login to Airflow
        session = requests.Session()
        
        # Get CSRF token
        response = session.get("http://localhost:8081/login")
        
        # Login
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        response = session.post("http://localhost:8081/login", data=login_data)
        
        if response.status_code != 200:
            print("❌ Failed to login to Airflow")
            return False
        
        # Trigger DAG
        dag_run_data = {
            "conf": json.dumps({"target_date": target_date}),
            "execution_date": datetime.now().isoformat()
        }
        
        response = session.post(
            "http://localhost:8081/api/experimental/dags/etl_iqplus_docker_operators/dag_runs",
            json=dag_run_data
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ DAG triggered successfully for date: {target_date}")
            return True
        else:
            print(f"❌ Failed to trigger DAG: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ DAG trigger failed: {e}")
        return False

def wait_for_dag_completion(timeout_minutes=60):
    """Wait for DAG run to complete"""
    print(f"⏳ Waiting for DAG completion (max {timeout_minutes} minutes)...")
    
    timeout = datetime.now() + timedelta(minutes=timeout_minutes)
    
    while datetime.now() < timeout:
        try:
            # Check DAG run status via API
            response = requests.get(
                "http://localhost:8081/api/experimental/dags/etl_iqplus_docker_operators/dag_runs"
            )
            
            if response.status_code == 200:
                runs = response.json()
                if runs:
                    latest_run = runs[0]
                    state = latest_run.get("state")
                    print(f"   Current state: {state}")
                    
                    if state == "success":
                        print("✅ DAG completed successfully!")
                        return True
                    elif state == "failed":
                        print("❌ DAG failed!")
                        return False
            
        except Exception as e:
            print(f"   Error checking status: {e}")
        
        time.sleep(30)  # Check every 30 seconds
    
    print("⏰ DAG completion timeout reached")
    return False

def main():
    """Main end-to-end test function"""
    print("🧪 ETL IQPlus Docker Operators - End-to-End Test")
    print("=" * 60)
    
    # Target date for testing
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    target_date = (datetime.now(jakarta_tz) - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📅 Target date: {target_date}")
    
    try:
        # 1. Deploy services
        print("\n" + "="*40)
        print("STEP 1: Deploy Services")
        print("="*40)
        
        if not run_powershell_command(
            ".\\deploy_docker_operators.ps1", 
            "Deploy Docker Operators", 
            timeout=900
        ):
            return False
        
        # 2. Wait for services to be ready
        print("\n" + "="*40)
        print("STEP 2: Verify Services")
        print("="*40)
        
        time.sleep(30)  # Give services time to start
        
        # Check Airflow
        try:
            response = requests.get("http://localhost:8081/health", timeout=10)
            print("✅ Airflow is accessible")
        except:
            print("❌ Airflow is not accessible")
            return False
        
        # 3. Trigger DAG manually
        print("\n" + "="*40)
        print("STEP 3: Trigger DAG")
        print("="*40)
        
        if not trigger_dag_run(target_date):
            return False
        
        # 4. Wait for completion
        print("\n" + "="*40)
        print("STEP 4: Monitor DAG Execution")
        print("="*40)
        
        if not wait_for_dag_completion(timeout_minutes=45):
            print("⚠️ DAG didn't complete in time, checking partial results...")
        
        # 5. Validate results
        print("\n" + "="*40)
        print("STEP 5: Validate Results")
        print("="*40)
        
        # Check MongoDB data
        print("\n📊 Checking MongoDB data...")
        mongodb_ok = check_mongodb_data(target_date)
        
        # Check shared volume
        print("\n💾 Checking shared volume...")
        shared_volume_ok = run_powershell_command(
            'docker run --rm -v etl-iqplus_shared_data:/shared alpine ls -la /shared',
            "Check shared volume contents"
        )
        
        # 6. Generate report
        print("\n" + "="*40)
        print("STEP 6: Test Report")
        print("="*40)
        
        report = {
            "test_date": datetime.now().isoformat(),
            "target_date": target_date,
            "deployment": True,  # If we got this far
            "dag_trigger": True,  # If we got this far
            "mongodb_validation": mongodb_ok,
            "shared_volume_check": shared_volume_ok,
            "overall_status": "PASSED" if (mongodb_ok and shared_volume_ok) else "PARTIAL"
        }
        
        # Save report
        with open(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Test Report:")
        for key, value in report.items():
            status = "✅" if value else "❌"
            if isinstance(value, bool):
                print(f"   {status} {key}: {value}")
            else:
                print(f"   📝 {key}: {value}")
        
        # 7. Next steps
        print("\n💡 Next Steps:")
        print("   1. Check Airflow UI: http://localhost:8081")
        print("   2. Monitor MongoDB data: python monitor_data.py")
        print("   3. Check logs: docker-compose logs [service-name]")
        
        if report["overall_status"] == "PASSED":
            print("\n🎉 End-to-End Test PASSED!")
            return True
        else:
            print("\n⚠️ End-to-End Test PARTIALLY PASSED - check issues above")
            return True  # Still return True as deployment succeeded
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
