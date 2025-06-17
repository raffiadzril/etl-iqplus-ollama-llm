# ETL IQPlus Financial News - Microservices Pipeline

Pipeline ETL (Extract, Transform, Load) modern untuk scraping dan analisis berita finansial IQPlus dengan arsitektur **microservices** dan **Docker Operators**.

## 🚀 Quick Start

```powershell
# Deploy complete pipeline
.\deploy_docker_operators.ps1

# Manual testing
.\test_complete_pipeline.ps1
```

## 📁 Architecture

```
Extract Service → Transform Service → Load Service
     ↓                 ↓                ↓
  Raw News      →  Processed News  → Final News + Analytics
```

## 📚 Documentation

- **[Docker Operators Guide](README_DOCKER_OPERATORS.md)** - Complete setup with Docker Operators
- **[Microservices Guide](README_MICROSERVICES.md)** - Service architecture details

## 🔗 Access Points

- **Airflow UI**: http://localhost:8081 (admin/admin)
- **Services**: Extract (5000), Transform (5001), Load (5002)  
- **MongoDB**: localhost:27017

## 🧪 Testing

- `test_complete_pipeline.ps1` - Full pipeline test
- `test_docker_operators.py` - Container testing
- `monitor_data.py` - Data validation
