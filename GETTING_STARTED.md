# 🚀 ETL IQPlus - Getting Started Guide

## Project Overview
ETL IQPlus adalah pipeline modern untuk scraping dan analisis berita finansial dengan arsitektur microservices dan Docker Operators.

## ✅ Post-Cleanup Status
- ✅ **Structure**: Clean and organized
- ✅ **Dependencies**: Properly separated per service  
- ✅ **Testing**: Comprehensive test suite available
- ✅ **Documentation**: Complete and updated
- ✅ **Deployment**: Fully automated

## 🎯 Quick Start Options

### Option 1: Full Automated Deployment
```powershell
.\deploy_docker_operators.ps1
```
This will:
- Build all Docker images
- Start all services  
- Run health checks
- Execute tests
- Provide access URLs

### Option 2: Step-by-Step Manual
```powershell
# 1. Build images
.\build_docker_images.ps1

# 2. Start services
.\start_services.ps1

# 3. Test pipeline
.\test_complete_pipeline.ps1

# 4. Monitor
python monitor_data.py
```

### Option 3: Testing Only
```powershell
# Test individual components
python test_docker_operators.py

# Test Airflow DAG
.\test_airflow_dag.ps1

# End-to-end test
python test_end_to_end.py
```

## 📊 Access Information

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow UI** | http://localhost:8081 | admin/admin |
| **MongoDB** | localhost:27017 | - |
| **Extract API** | http://localhost:5000 | - |
| **Transform API** | http://localhost:5001 | - |
| **Load API** | http://localhost:5002 | - |

## 🔧 Troubleshooting

### Common Issues
1. **Docker not running**: Start Docker Desktop
2. **Ports in use**: Stop conflicting services or change ports in docker-compose.yml
3. **Memory issues**: Ensure Docker has at least 4GB RAM allocated

### Health Check Commands
```powershell
# Check all services
.\check_status.ps1

# View logs
docker-compose logs [service-name]

# Restart services
.\stop_services.ps1
.\start_services.ps1
```

## 📚 Documentation Structure

```
README.md                      # This file - main overview
README_DOCKER_OPERATORS.md    # Docker Operators setup guide
README_MICROSERVICES.md       # Microservices architecture details
CLEANUP_SUMMARY.md            # What was cleaned up
```

## 🧪 Testing Levels

1. **Unit Testing**: Individual service containers
2. **Integration Testing**: Service communication
3. **E2E Testing**: Complete pipeline workflow
4. **Performance Testing**: Load and monitoring

## 🏗️ Architecture Summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Extract    │───▶│ Transform   │───▶│    Load     │
│  Service    │    │   Service   │    │   Service   │
│ (Selenium)  │    │ (LLM/Ollama)│    │ (MongoDB)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│              Airflow Orchestration                  │
│           (Docker Operators + XCom)                │
└─────────────────────────────────────────────────────┘
```

## 🎉 Success Indicators

After deployment, you should see:
- ✅ All services running in `docker-compose ps`
- ✅ Airflow UI accessible with admin/admin
- ✅ DAG `etl_iqplus_docker_operators` available
- ✅ MongoDB collections created after first run
- ✅ Test scripts passing

## 🔄 Next Steps

1. **Run First Pipeline**: Trigger DAG manually in Airflow UI
2. **Schedule Pipeline**: Enable DAG for daily runs
3. **Monitor Results**: Use `python monitor_data.py`
4. **Customize**: Modify services in `services/` folders
5. **Scale**: Add more extraction sources or transform logic

## ⚡ Performance Tips

- **Resource Allocation**: Ensure Docker has sufficient memory (4GB+)
- **Parallel Processing**: Adjust Airflow parallelism settings
- **Model Optimization**: Use appropriate Ollama model size
- **MongoDB Indexing**: Add indexes for better query performance

## 🆘 Support

If you encounter issues:
1. Check logs: `docker-compose logs [service-name]`
2. Verify status: `.\check_status.ps1`
3. Run cleanup: `.\verify_cleanup.ps1`
4. Restart: `.\stop_services.ps1 && .\start_services.ps1`

---

**Project Status**: ✅ Ready for Production
**Last Updated**: June 12, 2025
**Architecture**: Microservices + Docker Operators
