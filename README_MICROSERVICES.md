# ETL IQPlus Microservices Architecture

## Arsitektur Sistem

Sistem ini menggunakan arsitektur microservices dengan container terpisah:

1. **extraction-iqplus**: Service untuk scraping berita dari IQPlus
2. **transform-llm**: Service untuk analisis sentimen dengan Ollama Phi3
3. **airflow**: Service untuk orchestration workflow
4. **mongodb**: Database untuk menyimpan data
5. **ollama**: LLM service untuk analisis sentimen
6. **chrome**: Selenium Chrome untuk web scraping

## Alur Data

```
IQPlus Website → Extraction Service → MongoDB (raw_news)
                      ↓
                Transform Service ← Ollama Phi3
                      ↓
                JSON File + MongoDB (processed_news)
                      ↓
                Airflow Load Task → MongoDB (final_news)
```

## Struktur Direktori

```
services/
├── extraction/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── extraction_service.py
├── transform/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── transform_service.py
└── airflow/
    ├── Dockerfile
    ├── requirements.txt
    └── dags/
        └── etl_iqplus_microservices_dag.py
```

## Menjalankan Sistem

### 1. Quick Start (Recommended)

```powershell
# Start all services
.\start_services.ps1

# Stop all services  
.\stop_services.ps1
```

### 2. Manual Build dan Run

```powershell
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Testing Services

```powershell
# Install Python dependencies for testing
pip install requests pymongo

# Test all services
python test_services.py

# Monitor MongoDB data
python monitor_data.py
```

### 2. Akses Services

- **Airflow UI**: http://localhost:8081 (admin/admin)
- **Extraction Service**: http://localhost:5000
- **Transform Service**: http://localhost:5001
- **MongoDB**: localhost:27017
- **Ollama**: http://localhost:11434

### 3. Manual Testing Services

#### Test Extraction Service:
```bash
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-06-11"}'
```

#### Test Transform Service:
```bash
curl -X POST http://localhost:5001/transform \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-06-11"}'
```

### 4. Monitor Logs

```bash
# Extraction service
docker logs extraction-iqplus -f

# Transform service
docker logs transform-llm -f

# Airflow
docker logs airflow-webserver -f
docker logs airflow-scheduler -f

# Ollama
docker logs ollama -f
```

## Database Collections

### MongoDB Collections:
1. **raw_news**: Berita mentah hasil scraping
2. **processed_news**: Berita yang sudah dianalisis sentimen
3. **final_news**: Hasil akhir untuk konsumsi

### Contoh Data Flow:

```json
// raw_news
{
  "headline": "CLEO: ANGGARKAN CAPEX Rp500 MILIAR, CLEO SIAP BANGUN TIGA PABRIK BARU",
  "link": "...",
  "published_at": "27/05/25 - 11:09",
  "content": "...",
  "extracted_at": "2025-06-12T13:00:00+07:00",
  "source": "iqplus"
}

// processed_news (+ sentiment analysis)
{
  // ... data dari raw_news
  "sentiment": "positive",
  "confidence": 0.8,
  "tickers": ["CLEO"],
  "reasoning": "...",
  "summary": "...",
  "processed_at": "2025-06-12T13:01:00+07:00"
}

// final_news (+ metadata final)
{
  // ... data dari processed_news
  "final_loaded_at": "2025-06-12T13:02:00+07:00",
  "processing_date": "2025-06-11"
}
```

## Troubleshooting

### 1. Ollama tidak bisa pull model
```bash
docker exec -it ollama ollama pull phi3
```

### 2. Chrome service tidak responding
```bash
docker restart selenium-chrome
```

### 3. MongoDB connection issues
```bash
docker exec -it mongodb mongosh
```

### 4. Reset semua data
```bash
docker-compose down -v
docker-compose up --build
```

## Scaling

Untuk scaling, bisa menambahkan replica:

```yaml
# Dalam docker-compose.yml
extraction-iqplus:
  # ... config existing
  deploy:
    replicas: 2
    
transform-llm:
  # ... config existing  
  deploy:
    replicas: 2
```

## Environment Variables

```bash
# Extraction Service
MONGO_URI=mongodb://mongodb:27017/
CHROME_URL=http://chrome:4444/wd/hub

# Transform Service
MONGO_URI=mongodb://mongodb:27017/
OLLAMA_API=http://ollama:11434/api/generate

# Airflow
EXTRACTION_SERVICE_URL=http://extraction-iqplus:5000
TRANSFORM_SERVICE_URL=http://transform-llm:5001
```
