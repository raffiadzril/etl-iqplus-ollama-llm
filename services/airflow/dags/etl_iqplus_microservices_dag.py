#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Airflow DAG untuk Orchestration ETL IQPlus Financial News
Koordinasi antara Extraction Service dan Transform Service
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pytz
import requests
import logging
import os
import json
from pymongo import MongoClient

# Configuration
EXTRACTION_SERVICE_URL = os.getenv('EXTRACTION_SERVICE_URL', 'http://extraction-iqplus:5000')
TRANSFORM_SERVICE_URL = os.getenv('TRANSFORM_SERVICE_URL', 'http://transform-llm:5001')
LOAD_SERVICE_URL = os.getenv('LOAD_SERVICE_URL', 'http://load-service:5002')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_extraction_service(**kwargs):
    """Panggil extraction service untuk scraping berita dengan debugging detail"""
    target_date = kwargs.get('target_date', None)
    if not target_date:
        # Default ke kemarin untuk production (tanggal berita yang akan diextract)
        yesterday = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).date()
        target_date = yesterday.strftime("%Y-%m-%d")
        logger.info(f"📅 Tidak ada target_date yang diberikan, menggunakan kemarin: {target_date}")
    
    payload = {"date": target_date}
    
    try:
        logger.info("=" * 60)
        logger.info(f"🚀 MEMULAI EXTRACTION SERVICE")
        logger.info(f"📅 Target Date: {target_date}")
        logger.info(f"🔗 Extraction Service URL: {EXTRACTION_SERVICE_URL}")
        logger.info(f"📦 Payload: {payload}")
        logger.info("=" * 60)
        
        # Check if extraction service is healthy first
        try:
            health_response = requests.get(f"{EXTRACTION_SERVICE_URL}/health", timeout=30)
            if health_response.status_code == 200:
                logger.info(f"✅ Extraction service health check: {health_response.json()}")
            else:
                logger.warning(f"⚠️ Extraction service health check failed: HTTP {health_response.status_code}")
        except Exception as he:
            logger.warning(f"⚠️ Tidak dapat mengecek health extraction service: {he}")
        
        logger.info(f"⏳ Mengirim request ke extraction service...")
        logger.info(f"⏰ Timeout setting: 900 detik (15 menit)")
        
        response = requests.post(
            f"{EXTRACTION_SERVICE_URL}/extract",
            json=payload,
            timeout=900  # 15 menit timeout untuk scraping yang lebih lama
        )
        
        logger.info(f"📡 Response received - Status Code: {response.status_code}")
        logger.info(f"📏 Response Content Length: {len(response.content)} bytes")
        
        response.raise_for_status()
        
        result = response.json()
        logger.info("=" * 60)
        logger.info(f"✅ EXTRACTION BERHASIL!")
        logger.info(f"📊 Extracted Count: {result.get('extracted_count', 'N/A')}")
        logger.info(f"💾 Inserted Count: {result.get('inserted_count', 'N/A')}")
        logger.info(f"📂 Output File: {result.get('output_file', 'N/A')}")
        logger.info(f"📝 Message: {result.get('message', 'N/A')}")
        logger.info(f"🎯 Status: {result.get('status', 'N/A')}")
        logger.info("=" * 60)
        
        # Push hasil ke XCom untuk task berikutnya
        kwargs['ti'].xcom_push(key='extraction_result', value=result)
        kwargs['ti'].xcom_push(key='target_date', value=target_date)
        
        # Log summary untuk monitoring
        if result.get('extracted_count', 0) > 0:
            logger.info(f"🎉 SUCCESS: Berhasil mengekstrak {result.get('extracted_count')} berita untuk tanggal {target_date}")
        else:
            logger.info(f"ℹ️ INFO: Tidak ada berita ditemukan untuk tanggal {target_date}, mungkin perlu cek tanggal lain atau halaman lebih lanjut")
        
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ TIMEOUT: Extraction service tidak merespons dalam 15 menit")
        logger.error(f"💡 Saran: Periksa apakah website target dapat diakses atau tingkatkan timeout")
        raise
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"🌐 CONNECTION ERROR: Tidak dapat terhubung ke extraction service")
        logger.error(f"🔍 Detail: {ce}")
        logger.error(f"💡 Saran: Periksa apakah extraction service berjalan di {EXTRACTION_SERVICE_URL}")
        raise
    except requests.exceptions.HTTPError as he:
        logger.error(f"🚫 HTTP ERROR: {he}")
        logger.error(f"📡 Response Status: {response.status_code}")
        logger.error(f"📝 Response Text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR dalam extraction: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        raise

def call_transform_service(**kwargs):
    """Panggil transform service untuk analisis sentimen"""
    ti = kwargs['ti']
    extraction_result = ti.xcom_pull(key='extraction_result')
    target_date = ti.xcom_pull(key='target_date')
    
    if not extraction_result:
        raise ValueError("Tidak ada hasil extraction untuk diproses")
    
    payload = {"date": target_date}
    
    try:
        logger.info("=" * 60)
        logger.info(f"🤖 MEMULAI TRANSFORM SERVICE")
        logger.info(f"📅 Target Date: {target_date}")
        logger.info(f"🔗 Transform Service URL: {TRANSFORM_SERVICE_URL}")
        logger.info(f"📊 Extraction Result: {extraction_result}")
        logger.info("=" * 60)
        
        # Check if transform service is healthy
        try:
            health_response = requests.get(f"{TRANSFORM_SERVICE_URL}/health", timeout=30)
            if health_response.status_code == 200:
                logger.info(f"✅ Transform service health check: {health_response.json()}")
            else:
                logger.warning(f"⚠️ Transform service health check failed: HTTP {health_response.status_code}")
        except Exception as he:
            logger.warning(f"⚠️ Tidak dapat mengecek health transform service: {he}")
        
        logger.info(f"⏳ Mengirim request ke transform service...")
        logger.info(f"⏰ Timeout setting: 1200 detik (20 menit)")
        
        response = requests.post(
            f"{TRANSFORM_SERVICE_URL}/transform",
            json=payload,
            timeout=1200  # 20 menit timeout untuk processing LLM
        )
        
        logger.info(f"📡 Response received - Status Code: {response.status_code}")
        response.raise_for_status()
        
        result = response.json()
        logger.info("=" * 60)
        logger.info(f"✅ TRANSFORM BERHASIL!")
        logger.info(f"📝 Message: {result.get('message', 'N/A')}")
        logger.info(f"🎯 Status: {result.get('status', 'N/A')}")
        logger.info(f"📂 Output File: {result.get('output_file', 'N/A')}")
        logger.info("=" * 60)
        
        # Push hasil ke XCom
        kwargs['ti'].xcom_push(key='transform_result', value=result)
        
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ TIMEOUT: Transform service tidak merespons dalam 20 menit")
        logger.error(f"💡 Saran: LLM processing mungkin membutuhkan waktu lebih lama")
        raise
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"🌐 CONNECTION ERROR: Tidak dapat terhubung ke transform service")
        logger.error(f"🔍 Detail: {ce}")
        raise
    except Exception as e:
        logger.error(f"❌ ERROR dalam transform: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        raise

def call_load_service(**kwargs):
    """Panggil load service untuk load final data ke MongoDB"""
    ti = kwargs['ti']
    transform_result = ti.xcom_pull(key='transform_result')
    target_date = ti.xcom_pull(key='target_date')
    
    if not transform_result:
        raise ValueError("Tidak ada hasil transform untuk diload")
    
    # Ambil path file JSON dari transform result
    json_file = transform_result.get('output_file')
    
    payload = {
        "json_file": json_file,
        "date": target_date
    }
    
    try:
        logger.info(f"🚀 Memanggil load service untuk file: {json_file}")
        response = requests.post(
            f"{LOAD_SERVICE_URL}/load/json",
            json=payload,
            timeout=10  # 10 menit timeout
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"✅ Load berhasil: {result}")
        
        # Push hasil ke XCom
        kwargs['ti'].xcom_push(key='load_result', value=result)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error dalam load: {e}")
        raise

def generate_analytics(**kwargs):
    """Generate analytics summary"""
    ti = kwargs['ti']
    load_result = ti.xcom_pull(key='load_result')
    target_date = ti.xcom_pull(key='target_date')
    
    if not load_result:
        logger.warning("⚠️ Tidak ada hasil load, tetapi tetap generate analytics")
    
    payload = {"date": target_date}
    
    try:
        logger.info(f"📊 Generate analytics untuk tanggal: {target_date}")
        response = requests.post(
            f"{LOAD_SERVICE_URL}/analytics/generate",
            json=payload,
            timeout=10 # 5 menit timeout
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"✅ Analytics berhasil: {result}")
        
        # Push hasil ke XCom
        kwargs['ti'].xcom_push(key='analytics_result', value=result)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error dalam generate analytics: {e}")
        raise

def final_load_to_mongodb(**kwargs):
    """DEPRECATED: Load logic sudah dipindah ke Load Service"""
    ti = kwargs['ti']
    load_result = ti.xcom_pull(key='load_result')
    analytics_result = ti.xcom_pull(key='analytics_result')
    target_date = ti.xcom_pull(key='target_date')
    
    # Log summary hasil keseluruhan pipeline
    logger.info("🏁 ETL Pipeline Summary:")
    logger.info(f"   Target Date: {target_date}")
    
    if load_result:
        logger.info(f"   Load Result: {load_result.get('result', {})}")
    
    if analytics_result:
        analytics_data = analytics_result.get('analytics', {})
        logger.info(f"   Total News: {analytics_data.get('total_news', 0)}")
        logger.info(f"   Sentiment Distribution: {analytics_data.get('sentiment_distribution', {})}")
    
    result = {
        "status": "completed",
        "message": "ETL Pipeline completed successfully",
        "target_date": target_date,
        "load_result": load_result,
        "analytics_result": analytics_result,
        "completed_at": datetime.now(JAKARTA_TZ).isoformat()
    }
    
    logger.info(f"🎉 ETL Pipeline completed: {result}")
    return result

def cleanup_temp_files(**kwargs):
    """Cleanup file temporary jika diperlukan"""
    ti = kwargs['ti']
    transform_result = ti.xcom_pull(key='transform_result')
    
    # Optional: cleanup temp files
    # Bisa diimplementasikan jika perlu
    logger.info("🧹 Cleanup completed")
    return "cleanup completed"

# DAG Definition
default_args = {
    'owner': 'etl-team',
    'start_date': datetime(2023, 1, 1, tzinfo=JAKARTA_TZ),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG(
    'etl_iqplus_microservices',
    default_args=default_args,
    schedule_interval='0 8 * * *',  # Setiap hari jam 8 pagi
    catchup=False,
    description='ETL IQPlus dengan arsitektur microservices: Extract -> Transform -> Load',
    tags=['etl', 'iqplus', 'microservices', 'llm', 'mongodb'],
    max_active_runs=1,  # Hanya satu run aktif dalam satu waktu
)

# Task definitions
extract_task = PythonOperator(
    task_id='extract_news',
    python_callable=call_extraction_service,
    provide_context=True,
    dag=dag,
    execution_timeout=timedelta(minutes=20),  # Increased to 20 minutes for detailed extraction
)

transform_task = PythonOperator(
    task_id='transform_with_llm',
    python_callable=call_transform_service,
    provide_context=True,
    dag=dag,
    execution_timeout=timedelta(minutes=30),
)

load_task = PythonOperator(
    task_id='load_to_final',
    python_callable=call_load_service,
    provide_context=True,
    dag=dag,
    execution_timeout=timedelta(minutes=10),
)

analytics_task = PythonOperator(
    task_id='generate_analytics',
    python_callable=generate_analytics,
    provide_context=True,
    dag=dag,
    execution_timeout=timedelta(minutes=5),
)

summary_task = PythonOperator(
    task_id='pipeline_summary',
    python_callable=final_load_to_mongodb,
    provide_context=True,
    dag=dag,
    execution_timeout=timedelta(minutes=5),
)

cleanup_task = PythonOperator(
    task_id='cleanup_temp_files',
    python_callable=cleanup_temp_files,
    provide_context=True,
    dag=dag,
    trigger_rule='all_done',  # Jalankan meskipun ada task yang gagal
)

# Task dependencies
extract_task >> transform_task >> load_task >> analytics_task >> summary_task >> cleanup_task
