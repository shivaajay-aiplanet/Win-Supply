# Phase 2: Pre-Flight Checklist

## 📋 Before Running the ETL Pipeline

Use this checklist to ensure everything is ready before starting the embedding generation process.

---

## ✅ Prerequisites

### 1. Phase 1 Complete
- [ ] PostgreSQL database accessible
- [ ] OpenSearch cluster running
- [ ] BM25 keyword search working
- [ ] FastAPI backend running
- [ ] Frontend search UI working

### 2. System Requirements
- [ ] Python 3.8+ installed
- [ ] At least 8GB RAM available
- [ ] At least 10GB free disk space
- [ ] Stable internet connection (for Ollama download)

---

## ✅ Installation Steps

### 1. Install Dependencies
```bash
cd server
pip install -r requirements.txt
```

**Verify:**
- [ ] `ollama` package installed
- [ ] `numpy` package installed
- [ ] `tqdm` package installed
- [ ] `requests` package installed

### 2. Install Ollama

**Windows:**
- [ ] Downloaded from https://ollama.ai/download
- [ ] Installed successfully
- [ ] Ollama running (check system tray)

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
```

**Verify:**
```bash
curl http://localhost:11434/api/tags
```
- [ ] Ollama responds with JSON

### 3. Pull Embedding Model
```bash
ollama pull nomic-embed-text:v1.5
```

**Verify:**
```bash
ollama list
```
- [ ] `nomic-embed-text:v1.5` appears in list
- [ ] Model size: ~1.5 GB

---

## ✅ Configuration Check

### 1. Environment Variables (`.env`)
- [ ] `OPENSEARCH_VECTOR_INDEX_NAME=inventory_vector`
- [ ] `OLLAMA_HOST=http://localhost:11434`
- [ ] `OLLAMA_MODEL=nomic-embed-text:v1.5`
- [ ] `EMBEDDING_DIMENSION=768`
- [ ] `EMBEDDING_BATCH_SIZE=100`
- [ ] `PROGRESS_DB_PATH=./embedding_progress.db`

### 2. Database Connections
- [ ] PostgreSQL connection string correct
- [ ] OpenSearch credentials correct
- [ ] Can connect to both databases

---

## ✅ Pre-Flight Tests

### 1. Run Setup Verification
```bash
cd server
python test_phase2_setup.py
```

**Expected Results:**
- [ ] ✅ PASS - Ollama Connection
- [ ] ✅ PASS - OpenSearch Connection
- [ ] ✅ PASS - PostgreSQL Connection
- [ ] ✅ PASS - Vector Index Creation
- [ ] ✅ PASS - Progress Tracker
- [ ] ✅ PASS - End-to-End Sample

**If any test fails, DO NOT proceed. Fix the issue first.**

### 2. Test Individual Components

**Embedding Service:**
```bash
python -m app.services.embedding_service
```
- [ ] Connection successful
- [ ] Embedding dimension: 768
- [ ] Test embedding generated

**Progress Tracker:**
```bash
python -m app.services.progress_tracker
```
- [ ] Database created
- [ ] Records tracked
- [ ] Stats retrieved

**Vector Index:**
```bash
python -m app.db.opensearch_vector
```
- [ ] Index created
- [ ] Documents indexed
- [ ] Vector search works

---

## ✅ Resource Check

### 1. System Resources
- [ ] CPU usage < 80%
- [ ] RAM usage < 70%
- [ ] Disk space > 10GB free
- [ ] No other heavy processes running

### 2. Services Running
- [ ] PostgreSQL running
- [ ] OpenSearch running (docker ps)
- [ ] Ollama running (curl test)
- [ ] No port conflicts

### 3. Network
- [ ] Can reach PostgreSQL
- [ ] Can reach OpenSearch
- [ ] Can reach Ollama (localhost)

---

## ✅ Backup & Safety

### 1. Backup Existing Data
- [ ] Backup PostgreSQL database (optional)
- [ ] Backup OpenSearch indices (optional)
- [ ] Note: ETL creates NEW index, doesn't modify existing

### 2. Disk Space
- [ ] Check available space: `df -h` (Linux/Mac) or `dir` (Windows)
- [ ] Ensure at least 10GB free
- [ ] Progress DB will use ~500MB
- [ ] Logs will use ~100MB

### 3. Time Planning
- [ ] Understand processing time: 9-18 hours (CPU only)
- [ ] Plan to run overnight or during off-hours
- [ ] Ensure system won't sleep/hibernate
- [ ] Ensure stable power supply

---

## ✅ Running the Pipeline

### 1. Test Run (Recommended First)
```bash
python embedding_etl_pipeline.py --batch-size 100 --recreate
```

**After 2-3 minutes, press Ctrl+C**

**Verify:**
- [ ] No errors in console
- [ ] Progress bar appeared
- [ ] Some records processed
- [ ] Check index: `curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"`
- [ ] Documents indexed (count > 0)

### 2. Full Run
```bash
python embedding_etl_pipeline.py --batch-size 100 --recreate
```

**Monitor:**
- [ ] Progress bar updating
- [ ] No errors in console
- [ ] CPU usage high (expected)
- [ ] Memory usage stable
- [ ] Logs being written

---

## ✅ During Execution

### 1. Monitoring
- [ ] Watch progress bar
- [ ] Check logs: `tail -f embedding_etl.log`
- [ ] Monitor system resources
- [ ] Check for errors

### 2. If Issues Occur
- [ ] Note the error message
- [ ] Check logs for details
- [ ] Press Ctrl+C to stop safely
- [ ] Progress is saved automatically
- [ ] Can resume later

### 3. Normal Behavior
- [ ] High CPU usage (Ollama embedding generation)
- [ ] Moderate memory usage (2-4 GB)
- [ ] Progress bar updates every few seconds
- [ ] Logs written periodically

---

## ✅ After Completion

### 1. Verify Results
```bash
# Check document count
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```
- [ ] Count ≈ 330,000 (or close to it)

```bash
# Check sample document
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_search?size=1&pretty"
```
- [ ] Document has `embedding` field
- [ ] Embedding is array of 768 numbers
- [ ] All text fields present

### 2. Check Progress Stats
```python
from app.services.progress_tracker import ProgressTracker

tracker = ProgressTracker()
stats = tracker.get_progress_stats()
print(stats)
```
- [ ] `completed` count ≈ 330,000
- [ ] `failed` count < 1% of total
- [ ] `last_processed_id` ≈ 330,000

### 3. Review Logs
```bash
tail -100 embedding_etl.log
```
- [ ] "ETL PIPELINE COMPLETE!" message
- [ ] Final statistics shown
- [ ] No critical errors

---

## ✅ Troubleshooting

### Common Issues

**Issue: Ollama not responding**
- [ ] Check if Ollama is running
- [ ] Restart Ollama
- [ ] Check port 11434 not blocked

**Issue: Out of memory**
- [ ] Reduce batch size: `--batch-size 50`
- [ ] Close other applications
- [ ] Increase system swap

**Issue: Very slow**
- [ ] Normal for CPU-only processing
- [ ] Check CPU usage (should be high)
- [ ] Consider running overnight

**Issue: Connection errors**
- [ ] Check PostgreSQL running
- [ ] Check OpenSearch running
- [ ] Check network connectivity

---

## ✅ Resume After Interruption

If the pipeline stops for any reason:

1. **Don't panic** - Progress is saved
2. **Check what happened** - Review logs
3. **Fix the issue** - If any
4. **Resume** - Just run the command again:
   ```bash
   python embedding_etl_pipeline.py
   ```
5. **Verify** - Pipeline resumes from last checkpoint

**Do NOT use `--recreate` or `--reset-progress` when resuming!**

---

## ✅ Final Checklist

Before marking Phase 2 as complete:

- [ ] All 330,000+ records processed
- [ ] OpenSearch index has ~330,000 documents
- [ ] Sample documents have embeddings
- [ ] Progress tracker shows completion
- [ ] No critical errors in logs
- [ ] Vector search works (test with sample)
- [ ] Documentation reviewed
- [ ] Ready for Phase 3

---

## 📞 Need Help?

### Documentation
- `PHASE2_VECTOR_EMBEDDINGS.md` - Full technical docs
- `PHASE2_QUICKSTART.md` - Quick start guide
- `PHASE2_IMPLEMENTATION_SUMMARY.md` - Overview

### Testing
- `test_phase2_setup.py` - Verify setup
- Individual component tests available

### Logs
- `embedding_etl.log` - Pipeline execution logs
- `embedding_progress.db` - Progress database

---

## 🎯 Success Criteria

Phase 2 is complete when:

✅ All records have embeddings  
✅ Vector index is populated  
✅ Vector search works  
✅ No critical errors  
✅ Documentation complete  
✅ Ready for Phase 3  

---

**Good luck with the embedding generation!** 🚀

*Remember: The pipeline is crash-safe. You can stop and resume anytime.*

