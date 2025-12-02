# Phase 2: Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- ✅ Phase 1 completed (PostgreSQL → OpenSearch BM25 search working)
- ✅ Python 3.8+ installed
- ✅ OpenSearch running (docker-compose up)
- ✅ PostgreSQL accessible

---

## Step 1: Install Dependencies (2 minutes)

```bash
cd server
pip install -r requirements.txt
```

This installs:
- `ollama` - Ollama Python client
- `numpy` - Numerical operations
- `tqdm` - Progress bars
- `requests` - HTTP library

---

## Step 2: Install Ollama (3 minutes)

### Windows:
1. Download from https://ollama.ai/download
2. Run installer
3. Ollama will start automatically

### Linux/Mac:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
```

### Pull the Embedding Model:
```bash
ollama pull nomic-embed-text:v1.5
```

**Wait for download to complete** (~1.5 GB)

---

## Step 3: Verify Setup (1 minute)

```bash
cd server
python test_phase2_setup.py
```

Expected output:
```
TEST SUMMARY
================================================================================
✅ PASS - Ollama Connection
✅ PASS - OpenSearch Connection
✅ PASS - PostgreSQL Connection
✅ PASS - Vector Index Creation
✅ PASS - Progress Tracker
✅ PASS - End-to-End Sample

Results: 6/6 tests passed

🎉 All tests passed! Phase 2 setup is complete and ready.
```

If any test fails, see troubleshooting section below.

---

## Step 4: Run the ETL Pipeline

### Option A: Test with Small Sample First (Recommended)

```bash
# Process first 1000 records to test
python embedding_etl_pipeline.py --batch-size 100 --recreate
```

Let it run for 2-3 minutes, then press **Ctrl+C** to stop.

Check the results:
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

You should see some documents indexed.

### Option B: Run Full Pipeline (9-18 hours)

```bash
# Process all 330,000+ records
python embedding_etl_pipeline.py --batch-size 100 --recreate
```

**Note**: This will take several hours. The pipeline is crash-safe, so you can stop and resume anytime.

---

## 📊 Monitor Progress

### Real-time Progress Bar
The pipeline shows live progress:
```
Processing: 15%|███▌              | 50000/330000 [45:00<4:15:00, 18.30 records/s]
```

### Check Progress Manually

```python
from app.services.progress_tracker import ProgressTracker

tracker = ProgressTracker()
stats = tracker.get_progress_stats()
print(f"Completed: {stats['completed']:,}")
print(f"Failed: {stats['failed']}")
print(f"Last ID: {stats['last_processed_id']}")
```

### Check OpenSearch Index

```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

---

## 🔄 Resume After Interruption

If the pipeline stops (crash, Ctrl+C, power loss), just run it again:

```bash
python embedding_etl_pipeline.py
```

It will automatically:
- Load progress from database
- Skip already processed records
- Continue from where it left off

---

## 🐛 Troubleshooting

### Issue: "Failed to connect to Ollama"

**Check if Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**If not running:**
- Windows: Start Ollama from Start Menu
- Linux/Mac: `ollama serve &`

### Issue: "Model not found"

**Pull the model:**
```bash
ollama pull nomic-embed-text:v1.5
```

### Issue: "OpenSearch connection failed"

**Check if OpenSearch is running:**
```bash
docker ps | grep opensearch
```

**If not running:**
```bash
cd server
docker-compose up -d
```

### Issue: Very slow processing

**Solutions:**
1. Reduce batch size: `--batch-size 50`
2. Check CPU usage (Ollama is CPU-intensive)
3. Close other applications
4. Consider running overnight

### Issue: Out of memory

**Solutions:**
1. Reduce batch size: `--batch-size 25`
2. Close other applications
3. Increase system swap space

---

## 📈 Performance Expectations

### Embedding Speed
- **CPU only**: 5-10 embeddings/second
- **With GPU**: 20-50 embeddings/second

### Total Time (330,000 records)
- **CPU only**: 9-18 hours
- **With GPU**: 2-5 hours

### Recommended Batch Sizes
- **Low memory (8GB)**: 25-50
- **Medium memory (16GB)**: 50-100
- **High memory (32GB+)**: 100-200

---

## ✅ Verification

After the pipeline completes, verify everything worked:

### 1. Check Document Count
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

Expected: `{"count": 330000, ...}` (or close to it)

### 2. Check Sample Document
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_search?size=1&pretty"
```

Should show a document with:
- `id` field
- `text_combined` field
- `embedding` field (768-dimensional array)
- Original product fields

### 3. Check Progress Stats
```python
from app.services.progress_tracker import ProgressTracker

tracker = ProgressTracker()
stats = tracker.get_progress_stats()
print(stats)
```

Expected:
```python
{
    'total_processed': 330000,
    'completed': 329500,  # Most should be completed
    'failed': 500,        # Some failures are normal
    'last_processed_id': 330000
}
```

---

## 🎯 What's Next?

After Phase 2 completes, you'll have:
- ✅ 330,000+ products with 768-dimensional embeddings
- ✅ OpenSearch vector index with k-NN enabled
- ✅ Both keyword (BM25) and vector search capabilities

**Ready for Phase 3:**
- Hybrid search (combining BM25 + vector similarity)
- Reranking with multiple signals
- Advanced search API endpoints

---

## 📝 Command Reference

### Start Fresh
```bash
python embedding_etl_pipeline.py --recreate --reset-progress
```

### Resume Existing
```bash
python embedding_etl_pipeline.py
```

### Custom Batch Size
```bash
python embedding_etl_pipeline.py --batch-size 50
```

### Test Setup
```bash
python test_phase2_setup.py
```

### Check Ollama
```bash
curl http://localhost:11434/api/tags
ollama list
```

### Check OpenSearch
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/_cat/indices?v"
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

---

## 💡 Tips

1. **Run overnight**: The full pipeline takes hours, so start it before bed
2. **Monitor logs**: Check `embedding_etl.log` for detailed progress
3. **Test first**: Always test with small sample before full run
4. **Be patient**: Embedding generation is CPU-intensive and takes time
5. **Resume is safe**: Don't worry about interruptions, just restart

---

## 🆘 Need Help?

### Check Logs
```bash
tail -f embedding_etl.log
```

### Check Progress Database
```bash
sqlite3 embedding_progress.db "SELECT status, COUNT(*) FROM embedding_progress GROUP BY status;"
```

### Test Individual Components
```bash
python -m app.services.embedding_service
python -m app.services.progress_tracker
python -m app.db.opensearch_vector
```

---

## 🎉 Success!

Once the pipeline completes successfully, you're ready for Phase 3: Hybrid Search!

Your system now has:
- ✅ Keyword search (BM25)
- ✅ Semantic search (vector embeddings)
- ✅ 330,000+ products fully indexed
- ✅ Ready for hybrid reranking

**Congratulations on completing Phase 2!** 🚀

