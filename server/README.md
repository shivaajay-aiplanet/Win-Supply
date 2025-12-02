# Product Search API - Phase 1: BM25 Keyword Search

A data ingestion pipeline that extracts product data from PostgreSQL and indexes it into OpenSearch for keyword-based search using BM25 scoring.

## 🏗️ Architecture

```
PostgreSQL (Source) → ETL Pipeline → OpenSearch (Index) → FastAPI (Search API)
```

### Components

1. **PostgreSQL Database**: Source of product data (14 columns)
2. **ETL Pipeline**: Extracts, transforms, and loads data
3. **OpenSearch**: Search engine with BM25 scoring
4. **FastAPI**: REST API for search operations

## 📋 Prerequisites

- Python 3.8+
- Docker & Docker Compose (for OpenSearch)
- PostgreSQL database access (provided)

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Start OpenSearch

```bash
# From the project root directory
docker-compose up -d
```

This will start:

- OpenSearch Node 1 on port 9200
- OpenSearch Node 2 (cluster)
- OpenSearch Dashboards on port 5601

Wait ~30 seconds for OpenSearch to fully start.

### 3. Verify OpenSearch is Running

```bash
curl -k -u admin:Shiva54510$ https://localhost:9200
```

You should see cluster information in JSON format.

## 📊 Data Pipeline

### Indexed Fields (6 fields from 14 total)

The pipeline indexes only these fields:

1. `preferred_supplier` - Supplier name
2. `brand_name` - Product brand
3. `wise_item_number` - Item number
4. `catalog_number` - Catalog reference
5. `mainframe_description` - Product description
6. `win_item_name` - Product name

### Index Configuration

- **Index Name**: `inventory`
- **Analyzers**:
  - Standard analyzer for full-text search
  - Edge n-gram analyzer for partial/prefix matching
- **Scoring**: BM25 (default OpenSearch ranking)

## 🔧 Running the ETL Pipeline

### Option 1: Using Python Script

```bash
cd server
python etl_pipeline.py
```

To recreate the index (deletes existing data):

```bash
python etl_pipeline.py --recreate
```

### Option 2: Using the API

Start the FastAPI server:

```bash
cd server
uvicorn main:app --reload --port 8000
```

Then trigger the ETL via API:

```bash
curl -X POST http://localhost:8000/api/etl/run \
  -H "Content-Type: application/json" \
  -d '{"recreate_index": false, "batch_size": 1000}'
```

## 🔍 Search API Endpoints

### 1. Health Check

```bash
GET /api/health
```

Checks OpenSearch and PostgreSQL connectivity.

### 2. Multi-Field Search (BM25)

```bash
GET /api/search?q=product+name&top_k=10
```

Searches across all 6 indexed fields using BM25 scoring.

**Example:**

```bash
curl "http://localhost:8000/api/search?q=cable&top_k=10"
```

**Response:**

```json
{
  "query": "cable",
  "total_hits": 150,
  "returned_count": 10,
  "results": [
    {
      "id": "12345",
      "score": 8.234,
      "document": {
        "preferred_supplier": "Acme Corp",
        "brand_name": "TechBrand",
        "wise_item_number": "WI-12345",
        "catalog_number": "CAT-789",
        "mainframe_description": "High-speed ethernet cable",
        "win_item_name": "Ethernet Cable 10ft"
      }
    }
  ]
}
```

### 3. Field-Specific Search

```bash
GET /api/search/field?q=acme&field=brand_name&top_k=10
```

Searches in a specific field only.

### 4. Get Document by ID

```bash
GET /api/document/{doc_id}
```

Retrieves a specific document by its PostgreSQL ID.

### 5. Index Information

```bash
GET /api/index/info
```

Returns index statistics and document count.

### 6. Source Table Information

```bash
GET /api/source/info
```

Returns PostgreSQL table information.

## 📖 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the Search

### Test Queries

```bash
# Search for a brand
curl "http://localhost:8000/api/search?q=sony&top_k=5"

# Search for a catalog number
curl "http://localhost:8000/api/search?q=CAT-12345&top_k=5"

# Search in specific field
curl "http://localhost:8000/api/search/field?q=cable&field=win_item_name&top_k=5"

# Get specific document
curl "http://localhost:8000/api/document/1"
```

## 🔧 Configuration

All configuration is in `config.py` and `.env`:

```python
# PostgreSQL
POSTGRES_CONNECTION_STRING = "postgresql://..."

# OpenSearch
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASSWORD = "Shiva54510$"
OPENSEARCH_INDEX_NAME = "inventory"

# ETL
BULK_INDEX_BATCH_SIZE = 500
```

## 📁 Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API route aggregator
│   │   ├── search.py              # Search endpoints
│   │   ├── health.py              # Health check endpoints
│   │   ├── etl.py                 # ETL endpoints
│   │   └── index.py               # Index management endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_service.py      # Search business logic
│   │   ├── etl_service.py         # ETL orchestration
│   │   ├── indexer_service.py     # Bulk indexing logic
│   │   └── transformer_service.py # Data transformation
│   ├── db/
│   │   ├── __init__.py
│   │   ├── opensearch.py          # OpenSearch client
│   │   └── postgres.py            # PostgreSQL client
│   └── config/
│       ├── __init__.py
│       └── settings.py            # Configuration
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🐛 Troubleshooting

### OpenSearch Connection Failed

- Ensure Docker containers are running: `docker ps`
- Check OpenSearch logs: `docker logs opensearch-node1`
- Verify port 9200 is not in use

### PostgreSQL Connection Failed

- Verify the connection string in `.env`
- Check network connectivity to the database

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## 🚦 Next Steps (Future Phases)

**Phase 2** (Not implemented yet):

- Vector embeddings generation
- ANN (Approximate Nearest Neighbor) search
- Hybrid search (BM25 + vector similarity)

**Phase 3** (Not implemented yet):

- Business logic filters
- Reranking with multiple signals
- CTR and profit margin optimization

## 📝 Notes

- The ETL pipeline processes data in batches for memory efficiency
- Edge n-gram analyzer enables partial matching (e.g., "cab" matches "cable")
- BM25 scoring provides relevance-based ranking
- All text fields support fuzzy matching for typo tolerance
