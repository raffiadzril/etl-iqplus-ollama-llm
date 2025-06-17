# ETL IQPlus dengan Docker Operators

## Overview

Proyek ini telah diupgrade untuk menggunakan **Docker Operators** dalam Airflow untuk orchestration microservices ETL pipeline. Docker Operators memberikan isolasi yang lebih baik, resource management yang optimal, dan scalability yang lebih tinggi.

## Arsitektur Docker Operators

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Airflow       │───▶│  Docker Operator │───▶│   Extraction    │
│   Scheduler     │    │  (Extract)       │    │   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Docker        │───▶│  Docker Operator │───▶│   Transform     │
│   Network       │    │  (Transform)     │    │   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Shared        │───▶│  Docker Operator │───▶│      Load       │
│   Volume        │    │  (Load)          │    │   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Komponen Utama

### 1. Docker Images
- **etl-iqplus-extraction:latest** - Web scraping service
- **etl-iqplus-transform:latest** - LLM sentiment analysis service  
- **etl-iqplus-load:latest** - Data loading dan analytics service

### 2. Airflow DAG
- **etl_iqplus_docker_dag.py** - DAG dengan Docker Operators
- **etl_iqplus_microservices_dag.py** - DAG lama dengan HTTP calls (deprecated)

### 3. Entrypoint Scripts
- **entrypoint.py** - Command-line interface untuk setiap service
- Memungkinkan services dijalankan sebagai Docker containers

### 4. Shared Volume
- **etl-iqplus_shared_data** - Volume untuk komunikasi antar containers
- Menyimpan JSON files untuk data exchange

## Quick Start

### 1. Deploy Semua Services
```powershell
.\deploy_docker_operators.ps1
```

### 2. Manual Build dan Test
```powershell
# Build Docker images
.\build_docker_images.ps1

# Start services
.\start_services.ps1

# Test Docker Operators
python test_docker_operators.py

# Test Airflow DAG
.\test_airflow_dag.ps1
```

## File Structure

```
etl-iqplus/
├── services/
│   ├── extraction/
│   │   ├── entrypoint.py          # Docker Operator entrypoint
│   │   ├── extraction_service.py  # Flask service
│   │   └── Dockerfile
│   ├── transform/
│   │   ├── entrypoint.py          # Docker Operator entrypoint
│   │   ├── transform_service.py   # LLM processing service
│   │   └── Dockerfile
│   ├── load/
│   │   ├── entrypoint.py          # Docker Operator entrypoint
│   │   ├── load_service.py        # MongoDB loading service
│   │   └── Dockerfile
│   └── airflow/
│       └── dags/
│           ├── etl_iqplus_docker_dag.py      # Docker Operators DAG
│           └── etl_iqplus_microservices_dag.py  # HTTP calls DAG
├── build_docker_images.ps1       # Build all images
├── test_docker_operators.py      # Test individual containers
├── test_airflow_dag.ps1          # Test Airflow DAG
├── deploy_docker_operators.ps1   # Complete deployment
└── docker-compose.yml            # Updated dengan Docker socket
```

## DAG Tasks

### etl_iqplus_docker_operators

1. **get_target_date** - Determine target date untuk processing
2. **extract_news_docker** - Run extraction dalam Docker container
3. **validate_extraction** - Validate extraction results
4. **transform_with_llm_docker** - Run LLM processing dalam Docker container  
5. **validate_transform** - Validate transform results
6. **load_to_final_docker** - Run final loading dalam Docker container
7. **validate_load_and_summary** - Validate load dan generate summary
8. **cleanup_shared_files** - Cleanup temporary files

## Environment Variables

### Docker Operators
- `TARGET_DATE` - Date untuk processing (YYYY-MM-DD format)
- `MONGO_URI` - MongoDB connection string
- `SELENIUM_HUB_URL` - Selenium WebDriver URL
- `OLLAMA_BASE_URL` - Ollama LLM service URL

### Docker Compose
```yaml
environment:
  - AIRFLOW__CORE__EXECUTOR=LocalExecutor
  - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
```

## Volume Mounts

### Airflow Services
```yaml
volumes:
  - ./services/airflow/dags:/opt/airflow/dags
  - airflow_data:/opt/airflow
  - shared_data:/opt/airflow/shared
  - /var/run/docker.sock:/var/run/docker.sock  # For Docker Operators
```

### ETL Services (Docker Operators)
```yaml
volumes:
  - shared_data:/shared
  - /tmp:/tmp
```

## Komunikasi Data

### Shared Volume Structure
```
/shared/
├── extraction_result_YYYY-MM-DD.json
├── transform_result_YYYY-MM-DD.json
└── load_result_YYYY-MM-DD.json
```

### Data Flow
1. **Extraction** → Save ke `/shared/extraction_result_{date}.json`
2. **Transform** → Read extraction result, save ke `/shared/transform_result_{date}.json`
3. **Load** → Read transform result, save ke `/shared/load_result_{date}.json`

## Monitoring dan Troubleshooting

### Check Services Status
```powershell
.\check_status.ps1
docker-compose ps
```

### View Logs
```powershell
# Airflow logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler

# Service logs  
docker-compose logs extraction-iqplus
docker-compose logs transform-llm
docker-compose logs load-service
```

### Monitor Data
```python
python monitor_data.py
```

### Access Points
- **Airflow UI**: http://localhost:8081 (admin/admin)
- **MongoDB**: localhost:27017
- **Service APIs**: 
  - Extraction: http://localhost:5000
  - Transform: http://localhost:5001
  - Load: http://localhost:5002

## Advanced Usage

### Manual Docker Container Run
```bash
# Run extraction manually
docker run --rm \
  --network etl_network \
  -v etl-iqplus_shared_data:/shared \
  -e TARGET_DATE=2024-01-01 \
  etl-iqplus-extraction:latest \
  python /app/entrypoint.py 2024-01-01
```

### Custom DAG Configuration
```python
# Trigger DAG dengan custom date
airflow dags trigger etl_iqplus_docker_operators \
  --conf '{"target_date": "2024-01-01"}'
```

### Debugging
```powershell
# Enter Airflow container
docker-compose exec airflow-webserver bash

# Check shared volume
docker run --rm -v etl-iqplus_shared_data:/shared alpine ls -la /shared

# Test Docker connectivity
docker-compose exec airflow-webserver docker ps
```

## Keuntungan Docker Operators

1. **Isolasi Resource** - Setiap task berjalan dalam container terpisah
2. **Scalability** - Mudah scale individual components
3. **Dependency Management** - Setiap service punya dependencies sendiri
4. **Failure Isolation** - Task failure tidak mempengaruhi services lain
5. **Resource Control** - Bisa set memory/CPU limits per container
6. **Version Control** - Setiap service bisa punya versioning terpisah

## Migration dari HTTP Calls

Jika ingin kembali ke HTTP calls:
1. Gunakan `etl_iqplus_microservices_dag.py`
2. Pastikan semua services running dengan `docker-compose up -d`
3. Services akan berkomunikasi melalui REST API calls

## Performance Optimization

### Resource Limits
```yaml
# Dalam docker-compose.yml atau DockerOperator
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### Parallel Execution
- Docker Operators mendukung parallel execution
- Bisa menjalankan multiple instances dengan resource yang cukup

### Caching
- Docker images di-cache automatically
- Shared volume mempercepat data transfer

## Troubleshooting Common Issues

### 1. Docker Socket Permission
```bash
# Jika Docker Operators tidak bisa connect
sudo chmod 666 /var/run/docker.sock
```

### 2. Volume Mount Issues  
```bash
# Reset volumes
docker-compose down -v
docker volume prune
```

### 3. Network Connectivity
```bash
# Check network
docker network inspect etl_network
```

### 4. Memory Issues
```bash
# Check Docker resources
docker system df
docker system prune
```
