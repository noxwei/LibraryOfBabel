# 🧠 Embedding Pipeline Scripts

## 📁 Script Collection
Production-ready scripts for the LibraryOfBabel embedding pipeline.

### 🚀 Core Scripts

| Script | Purpose | Usage | Confluence Link |
|--------|---------|-------|-----------------|
| `multi_ollama_bge_daemon.py` | Load-balanced BGE embedding daemon | `python3 multi_ollama_bge_daemon.py 42` | [Multi-Ollama Daemon](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/multi-ollama-daemon) |
| `ollama_vector_embedder.py` | Core embedding service | Used by other scripts | [Core Embedder](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/core-embedder) |
| `test_new_embedding_models.py` | Model validation & testing | `python3 test_new_embedding_models.py` | [Model Testing](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/model-testing) |
| `demo_multiple_embeddings.py` | Performance comparison tool | `python3 demo_multiple_embeddings.py` | [Performance Demo](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/performance-demo) |

### 🛠️ Utility Scripts

| Script | Purpose | Usage | Confluence Link |
|--------|---------|-------|-----------------|
| `diagnose_embedding_pipeline.py` | Comprehensive diagnostics | `python3 diagnose_embedding_pipeline.py` | [Diagnostics](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/diagnostics) |
| `monitor_embedding_performance.py` | Real-time monitoring | `python3 monitor_embedding_performance.py` | [Monitoring](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/monitoring) |
| `quick_health_check.sh` | Fast system status | `./quick_health_check.sh` | [Health Checks](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/health-checks) |
| `emergency_reset.sh` | Nuclear reset option | `./emergency_reset.sh` | [Emergency Procedures](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/emergency) |

### 📊 Current Status (August 2025)
- **Multi-Ollama Daemon**: Running with 42 workers across 3 instances
- **Processing Rate**: 51,000+ embeddings/hour
- **Success Rate**: 100%
- **Remaining Work**: 1,521,401 BGE embeddings

### 🚀 Quick Start
```bash
cd data_processing_pipeline/scripts

# Test all models
python3 test_new_embedding_models.py

# Run performance demo
python3 demo_multiple_embeddings.py

# Start production daemon (if not running)
nohup python3 multi_ollama_bge_daemon.py 42 > ../logs/daemon.log 2>&1 &
```

**📋 Script Documentation**: [Complete Scripts Guide](https://libraryofbabel.atlassian.net/wiki/spaces/TECH/pages/scripts-guide)