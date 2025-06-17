#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Airflow DAG untuk Orchestration ETL IQPlus Financial News dengan Docker Operator
Menjalankan setiap service dalam container terpisah menggunakan Docker Operator
"""

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pytz
import logging
import os
import json

# Configuration
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')
DOCKER_NETWORK = 'etl_network'
SHARED_VOLUME = 'etl-iqplus_shared_data'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_target_date(**kwargs):
    """Get target date untuk processing"""
    target_date = kwargs.get('dag_run').conf.get('target_date') if kwargs.get('dag_run') and kwargs.get('dag_run').conf else None
    
    if not target_date:
        # Default ke kemarin
        yesterday = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).date()
        target_date = yesterday.strftime("%Y-%m-%d")
    
    logger.info(f"📅 Target date untuk ETL: {target_date}")
    
    # Push ke XCom untuk digunakan task lain
    kwargs['ti'].xcom_push(key='target_date', value=target_date)
    
    return target_date

def validate_extraction_result(**kwargs):
    """Validate hasil extraction"""
    ti = kwargs['ti']
    target_date = ti.xcom_pull(key='target_date')
    
    result_file = f"/opt/airflow/shared/extraction_result_{target_date}.json"
    
    try:
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            logger.info(f"✅ Extraction validation passed: {result.get('articles_scraped', 0)} articles")
            return result
        else:
            raise FileNotFoundError(f"Extraction result file not found: {result_file}")
            
    except Exception as e:
        logger.error(f"❌ Extraction validation failed: {e}")
        raise

def validate_transform_result(**kwargs):
    """Validate hasil transform"""
    ti = kwargs['ti']
    target_date = ti.xcom_pull(key='target_date')
    
    result_file = f"/opt/airflow/shared/transform_result_{target_date}.json"
    
    try:
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            logger.info(f"✅ Transform validation passed: {result.get('articles_processed', 0)} articles processed")
            return result
        else:
            raise FileNotFoundError(f"Transform result file not found: {result_file}")
            
    except Exception as e:
        logger.error(f"❌ Transform validation failed: {e}")
        raise

def validate_load_result(**kwargs):
    """Validate hasil load dan generate summary"""
    ti = kwargs['ti']
    target_date = ti.xcom_pull(key='target_date')
    
    result_file = f"/opt/airflow/shared/load_result_{target_date}.json"
    
    try:
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            logger.info("🏁 ETL Pipeline Summary:")
            logger.info(f"   Target Date: {target_date}")
            
            load_result = result.get('load_result', {})
            analytics_result = result.get('analytics_result', {})
            
            logger.info(f"   Load Result: {load_result}")
            
            if analytics_result:
                analytics_data = analytics_result.get('analytics', {})
                logger.info(f"   Total News: {analytics_data.get('total_news', 0)}")
                logger.info(f"   Sentiment Distribution: {analytics_data.get('sentiment_distribution', {})}")
            
            logger.info(f"🎉 ETL Pipeline completed successfully!")
            return result
        else:
            raise FileNotFoundError(f"Load result file not found: {result_file}")
            
    except Exception as e:
        logger.error(f"❌ Load validation failed: {e}")
        raise

def cleanup_shared_files(**kwargs):
    """Cleanup shared files setelah processing"""
    ti = kwargs['ti']
    target_date = ti.xcom_pull(key='target_date')
    
    files_to_cleanup = [
        f"/opt/airflow/shared/extraction_result_{target_date}.json",
        f"/opt/airflow/shared/transform_result_{target_date}.json",
        # Tidak cleanup load_result untuk audit trail
    ]
    
    for file_path in files_to_cleanup:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup {file_path}: {e}")
    
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
    'etl_iqplus_docker_operators',
    default_args=default_args,
    schedule_interval='0 8 * * *',  # Setiap hari jam 8 pagi
    catchup=False,
    description='ETL IQPlus dengan Docker Operators: Extract -> Transform -> Load',
    tags=['etl', 'iqplus', 'docker', 'microservices', 'llm', 'mongodb'],
    max_active_runs=1,  # Hanya satu run aktif dalam satu waktu
)

# Task 1: Get target date
get_date_task = PythonOperator(
    task_id='get_target_date',
    python_callable=get_target_date,
    provide_context=True,
    dag=dag,
)

# Task 2: Docker Extraction
extract_docker_task = DockerOperator(
    task_id='extract_news_docker',
    image='etl-iqplus-extraction:latest',
    command='python /app/entrypoint.py {{ ti.xcom_pull(key="target_date") }}',
    docker_url='unix://var/run/docker.sock',
    network_mode=DOCKER_NETWORK,
    volumes=[
        f'{SHARED_VOLUME}:/shared',
        '/tmp:/tmp'
    ],
    environment={
        'TARGET_DATE': '{{ ti.xcom_pull(key="target_date") }}',
        'MONGO_URI': 'mongodb://mongodb:27017/',
        'SELENIUM_HUB_URL': 'http://chrome:4444/wd/hub'
    },
    auto_remove=True,
    dag=dag,
    execution_timeout=timedelta(minutes=15),
)

# Task 3: Validate extraction
validate_extraction_task = PythonOperator(
    task_id='validate_extraction',
    python_callable=validate_extraction_result,
    provide_context=True,
    dag=dag,
)

# Task 4: Docker Transform
transform_docker_task = DockerOperator(
    task_id='transform_with_llm_docker',
    image='etl-iqplus-transform:latest',
    command='python /app/entrypoint.py {{ ti.xcom_pull(key="target_date") }}',
    docker_url='unix://var/run/docker.sock',
    network_mode=DOCKER_NETWORK,
    volumes=[
        f'{SHARED_VOLUME}:/shared',
        '/tmp:/tmp'
    ],
    environment={
        'TARGET_DATE': '{{ ti.xcom_pull(key="target_date") }}',
        'MONGO_URI': 'mongodb://mongodb:27017/',
        'OLLAMA_BASE_URL': 'http://ollama:11434'
    },
    auto_remove=True,
    dag=dag,
    execution_timeout=timedelta(minutes=30),
)

# Task 5: Validate transform
validate_transform_task = PythonOperator(
    task_id='validate_transform',
    python_callable=validate_transform_result,
    provide_context=True,
    dag=dag,
)

# Task 6: Docker Load
load_docker_task = DockerOperator(
    task_id='load_to_final_docker',
    image='etl-iqplus-load:latest',
    command='python /app/entrypoint.py {{ ti.xcom_pull(key="target_date") }}',
    docker_url='unix://var/run/docker.sock',
    network_mode=DOCKER_NETWORK,
    volumes=[
        f'{SHARED_VOLUME}:/shared',
        '/tmp:/tmp'
    ],
    environment={
        'TARGET_DATE': '{{ ti.xcom_pull(key="target_date") }}',
        'MONGO_URI': 'mongodb://mongodb:27017/'
    },
    auto_remove=True,
    dag=dag,
    execution_timeout=timedelta(minutes=10),
)

# Task 7: Validate load dan generate summary
validate_load_task = PythonOperator(
    task_id='validate_load_and_summary',
    python_callable=validate_load_result,
    provide_context=True,
    dag=dag,
)

# Task 8: Cleanup
cleanup_task = PythonOperator(
    task_id='cleanup_shared_files',
    python_callable=cleanup_shared_files,
    provide_context=True,
    dag=dag,
    trigger_rule='all_done',  # Jalankan meskipun ada task yang gagal
)

# Task dependencies
get_date_task >> extract_docker_task >> validate_extraction_task >> transform_docker_task >> validate_transform_task >> load_docker_task >> validate_load_task >> cleanup_task
