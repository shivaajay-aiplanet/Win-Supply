# Phase 2: Vector Embedding Implementation

## 📋 Overview

This phase extends the keyword-based search system with vector embeddings and semantic search capabilities using:
- **Ollama** with **NomicEmbedTextV1.5** model for local embedding generation
- **OpenSearch k-NN** for vector similarity search
- **SQLite** for crash-safe progress tracking
- **Resume functionality** for handling interruptions

---

## 🎯 What Was Implemented

### 1. **Embedding Service** (`app/services/embedding_service.py`)
- Connects to local Ollama instance
- Generates embeddings using NomicEmbedTextV1.5 model
- Combines 6 text fields into single embedding
- Batch processing with retry logic
- Exponential backoff for transient errors

### 2. **Progress Tracker** (`app/services/progress_tracker.py`)
- SQLite-based progress tracking
- Crash-safe resume functionality
- Tracks processed/failed/skipped records
- Maintains metadata and statistics
- Supports batch operations

### 3. **Vector Index Management** (`app/db/opensearch_vector.py`)
- Creates OpenSearch index with k-NN enabled
- HNSW algorithm for efficient vector search
- Cosine similarity for relevance scoring
- Bulk indexing operations
- Vector search functionality

### 4. **ETL Pipeline** (`embedding_etl_pipeline.py`)
- End-to-end embedding generation pipeline
- Extracts data from PostgreSQL
- Generates embeddings via Ollama
- Indexes into OpenSearch
- Progress tracking and resume support
- Comprehensive logging and statistics

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

**New dependencies added:**
- `ollama==0.4.4` - Ollama Python client
- `requests==2.32.3` - HTTP library
- `numpy==1.26.4` - Numerical operations
- `tqdm==4.66.1` - Progress bars

### Step 2: Install and Start Ollama

#### On Windows:
1. Download Ollama from https://ollama.ai/download
2. Install and start Ollama
3. Pull the embedding model:
```bash
ollama pull nomic-embed-text:v1.5
```

#### On Linux/Mac:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull nomic-embed-text:v1.5
```

### Step 3: Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

You should see the `nomic-embed-text:v1.5` model listed.

### Step 4: Test the Embedding Service

```bash
cd server
python -m app.services.embedding_service
```

Expected output:
```
Testing Ollama Embedding Service...
Connected to OpenSearch cluster: opensearch-cluster
Available Ollama models: ['nomic-embed-text:v1.5']
Connection successful! Embedding dimension: 768
Generated embedding with dimension: 768
✅ All tests passed!
```

### Step 5: Test the Progress Tracker

```bash
python -m app.services.progress_tracker
```

Expected output:
```
Testing Progress Tracker...
Progress tracker initialized at: ./test_progress.db
Last processed ID: 2
Progress stats: {'total_processed': 3, 'completed': 2, 'failed': 1, ...}
✅ All tests passed!
```

---

## 🏃 Running the ETL Pipeline

### Basic Usage

```bash
cd server
python embedding_etl_pipeline.py
```

This will:
1. Connect to PostgreSQL and OpenSearch
2. Create the `inventory_vector` index (if not exists)
3. Start processing records in batches
4. Generate embeddings using Ollama
5. Index documents with embeddings
6. Track progress in SQLite database

### Command Line Options

```bash
# Recreate the index (deletes existing data)
python embedding_etl_pipeline.py --recreate

# Use custom batch size
python embedding_etl_pipeline.py --batch-size 50

# Reset progress and start from beginning
python embedding_etl_pipeline.py --reset-progress

# Combine options
python embedding_etl_pipeline.py --recreate --batch-size 200 --reset-progress
```

### Resume After Interruption

If the pipeline is interrupted (Ctrl+C, crash, etc.), simply run it again:

```bash
python embedding_etl_pipeline.py
```

The pipeline will:
- Load progress from SQLite database
- Skip already processed records
- Continue from where it left off

---

## 📊 Expected Performance

### Embedding Generation Speed
- **Ollama (CPU)**: ~5-10 embeddings/second
- **Ollama (GPU)**: ~20-50 embeddings/second

### Total Processing Time (330,000 records)
- **CPU only**: ~9-18 hours
- **With GPU**: ~2-5 hours

### Batch Size Recommendations
- **CPU**: 50-100 records per batch
- **GPU**: 100-200 records per batch
- **High memory**: 200-500 records per batch

---

## 📁 Files Created

### Configuration
- `.env` - Updated with Phase 2 settings
- `app/config/settings.py` - Added embedding configuration

### Services
- `app/services/embedding_service.py` - Ollama embedding generation
- `app/services/progress_tracker.py` - SQLite progress tracking

### Database
- `app/db/opensearch_vector.py` - Vector index management

### Pipeline
- `embedding_etl_pipeline.py` - Main ETL script

### Logs and Data
- `embedding_etl.log` - Pipeline execution logs
- `embedding_progress.db` - SQLite progress database

---

## 🔧 Configuration

All configuration is in `.env`:

```bash
# Vector Index Name
OPENSEARCH_VECTOR_INDEX_NAME=inventory_vector

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text:v1.5

# Embedding Settings
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=100

# Progress Tracking
PROGRESS_DB_PATH=./embedding_progress.db
```

---

## 📈 Monitoring Progress

### View Progress in Real-Time

The pipeline shows a progress bar:
```
Processing: 45%|████████████          | 150000/330000 [2:30:00<2:00:00, 25.00 records/s]
```

### Check Progress Manually

```python
from app.services.progress_tracker import ProgressTracker

tracker = ProgressTracker()
stats = tracker.get_progress_stats()
print(stats)
```

Output:
```python
{
    'total_processed': 150000,
    'completed': 149500,
    'failed': 500,
    'skipped': 0,
    'last_processed_id': 150000,
    'status_breakdown': {'completed': 149500, 'failed': 500}
}
```

### Check OpenSearch Index

```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

---

## 🧪 Testing

### Test Individual Components

```bash
# Test embedding service
python -m app.services.embedding_service

# Test progress tracker
python -m app.services.progress_tracker

# Test vector index
python -m app.db.opensearch_vector
```

### Test with Small Sample

```bash
# Process only first 1000 records
python embedding_etl_pipeline.py --batch-size 100 --recreate
# Then stop with Ctrl+C after a few batches
```

---

## 🔍 Vector Index Schema

### Index: `inventory_vector`

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "text_combined": {"type": "text"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "preferred_supplier": {"type": "text"},
      "brand_name": {"type": "text"},
      "wise_item_number": {"type": "text"},
      "catalog_number": {"type": "text"},
      "mainframe_description": {"type": "text"},
      "win_item_name": {"type": "text"}
    }
  }
}
```

### Document Structure

```json
{
  "id": 62,
  "text_combined": "AIR FLOW PRODUCTS 4 x 12 x 6 in. 90-Degree Center End Register Boot",
  "embedding": [0.123, -0.456, 0.789, ...],  // 768 dimensions
  "preferred_supplier": "AIR FLOW PRODUCTS",
  "brand_name": "AIR FLOW PRODUCTS",
  "wise_item_number": "WIS-12345",
  "catalog_number": "CAT-456",
  "mainframe_description": "90-Degree Center End Register Boot",
  "win_item_name": "4 x 12 x 6 in. 90-Degree Center End Register Boot"
}
```

---

## 🐛 Troubleshooting

### Issue: Ollama Connection Failed

**Error**: `Failed to connect to Ollama`

**Solution**:
1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. Start Ollama: `ollama serve`
3. Verify model is pulled: `ollama list`

### Issue: Model Not Found

**Error**: `Model 'nomic-embed-text:v1.5' not found`

**Solution**:
```bash
ollama pull nomic-embed-text:v1.5
```

### Issue: OpenSearch Connection Failed

**Error**: `Failed to connect to OpenSearch`

**Solution**:
1. Check if OpenSearch is running: `docker ps`
2. Start OpenSearch: `cd server && docker-compose up -d`
3. Verify connection: `curl -k -u admin:Shiva54510$ https://localhost:9200`

### Issue: Out of Memory

**Error**: `MemoryError` or system slowdown

**Solution**:
1. Reduce batch size: `--batch-size 50`
2. Close other applications
3. Increase system swap space

### Issue: Slow Processing

**Problem**: Very slow embedding generation

**Solution**:
1. Check CPU usage - Ollama is CPU-intensive
2. Consider using GPU if available
3. Reduce batch size to avoid memory swapping
4. Run during off-peak hours

---

## 📊 Progress Tracking Database

### Schema

```sql
-- Progress tracking table
CREATE TABLE embedding_progress (
    id INTEGER PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL,
    status TEXT NOT NULL,
    embedding_dimension INTEGER,
    text_length INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Metadata table
CREATE TABLE embedding_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

### Query Progress

```bash
sqlite3 embedding_progress.db "SELECT status, COUNT(*) FROM embedding_progress GROUP BY status;"
```

---

## ✅ Verification

### After Pipeline Completes

1. **Check document count**:
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_count"
```

Expected: `{"count": 330000, ...}`

2. **Verify embeddings**:
```bash
curl -k -u admin:Shiva54510$ "https://localhost:9200/inventory_vector/_search?size=1"
```

Should show documents with `embedding` field containing 768-dimensional vectors.

3. **Check progress stats**:
```python
from app.services.progress_tracker import ProgressTracker
tracker = ProgressTracker()
print(tracker.get_progress_stats())
```

Expected: `{'completed': 330000, 'failed': 0, ...}`

---

## 🎯 Next Steps (Phase 3)

After Phase 2 completes, you'll have:
- ✅ 330,000+ products with vector embeddings
- ✅ OpenSearch index with k-NN enabled
- ✅ Both keyword (BM25) and vector search capabilities

**Phase 3 will add:**
- Hybrid search (BM25 + vector similarity)
- Reranking with multiple signals
- Business logic filters
- Advanced search API endpoints

---

## 📝 Summary

Phase 2 successfully implements:
- ✅ Local embedding generation with Ollama
- ✅ NomicEmbedTextV1.5 model integration
- ✅ Crash-safe progress tracking
- ✅ Resume functionality
- ✅ Batch processing with retry logic
- ✅ OpenSearch vector index with k-NN
- ✅ Comprehensive logging and monitoring
- ✅ 768-dimensional embeddings for all products

**Status**: Ready for production embedding generation! 🚀

