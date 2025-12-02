# Win Supply - Intelligent Product Search System

A sophisticated product search and matching system for industrial inventory management, featuring hybrid search capabilities with BM25 keyword search, vector embeddings, and AI-powered reranking.

## 🏗️ Architecture

```
PostgreSQL (330K+ products) → ETL Pipeline → OpenSearch (BM25 + Vector) → FastAPI → React Frontend
                                    ↓
                            Ollama (Embeddings) + HuggingFace (Reranking)
```

## ✨ Features

### 🔍 Multi-Modal Search
- **BM25 Keyword Search**: Traditional text-based search across all product fields
- **Vector Semantic Search**: AI-powered semantic similarity using NomicEmbedTextV1.5 embeddings
- **Hybrid Search**: Combines BM25 + Vector search with AI reranking for optimal results
- **LLM Product Matching**: Find similar and alternative products using advanced AI reasoning

### 🎯 Search Capabilities
- Search across 6 key product fields (supplier, brand, item number, catalog number, description, name)
- WISE item number lookup with intelligent product matching
- Real-time search with sub-second response times
- Relevance scoring and ranking

### 🚀 Performance
- **330,000+ products** indexed and searchable
- **Sub-second search** response times
- **Resume-capable ETL** pipeline with crash-safe progress tracking
- **Scalable architecture** supporting millions of products

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Primary data storage
- **OpenSearch** - Search engine with BM25 and k-NN vector search
- **Ollama** - Local LLM inference for embeddings (NomicEmbedTextV1.5)
- **HuggingFace** - AI reranking models (BAAI/bge-reranker-v2-m3)

### Frontend
- **React** - Modern UI framework
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL database access
- 8GB+ RAM recommended

### 1. Clone Repository
```bash
git clone https://github.com/aiplanethub/Win-Supply.git
cd Win-Supply
```

### 2. Backend Setup

#### Install Dependencies
```bash
cd server
pip install -r requirements.txt
```

#### Configure Environment
Create `.env` file in `server/` directory:
```bash
# PostgreSQL
POSTGRES_CONNECTION_STRING=postgresql://username:password@host:port/database

# OpenSearch
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=Shiva54510$
OPENSEARCH_INDEX_NAME=inventory
OPENSEARCH_VECTOR_INDEX_NAME=inventory_vector

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text:v1.5

# HuggingFace (optional, for better rate limits)
HF_TOKEN=your_huggingface_token_here
```

#### Start OpenSearch
```bash
cd server
docker-compose up -d
```

Wait ~30 seconds for OpenSearch to start, then verify:
```bash
curl -k -u admin:Shiva54510$ https://localhost:9200
```

#### Install Ollama
**Windows**: Download from https://ollama.ai/download
**Linux/Mac**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
```

Pull the embedding model:
```bash
ollama pull nomic-embed-text:v1.5
```

#### Run ETL Pipeline

**Phase 1: BM25 Index**
```bash
python etl_pipeline.py
```

**Phase 2: Vector Embeddings** (9-18 hours for full dataset)
```bash
python embedding_etl_pipeline.py --batch-size 100
```

#### Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd client
npm install
npm run dev
```

The application will be available at http://localhost:5173

## 📖 Usage Guide

### Search Types

#### 1. All Fields Search (BM25)
- Select "All Fields" from dropdown
- Enter any product-related keywords
- Returns BM25-scored results across all indexed fields

#### 2. WISE Item Number Search (Hybrid + AI)
- Select "WISE Item Number" from dropdown  
- Enter a WISE item number (e.g., "100027")
- System performs:
  1. Product lookup in PostgreSQL
  2. Embedding generation via Ollama
  3. Parallel BM25 + Vector search
  4. AI reranking with relevance scoring
  5. Returns top matches with similarity scores

### Understanding Results

- **Blue Badge**: BM25 keyword relevance score
- **Purple Badge**: AI reranker relevance percentage (0-100%)
- **Green "Best Match"**: Top-ranked result
- **K/V Scores**: Keyword and Vector component scores
- **Rank Numbers**: Position in reranked results

## 🔧 API Endpoints

### Health Check
```bash
GET /api/health
```

### BM25 Search
```bash
GET /api/search?q=cable&top_k=10
```

### Hybrid Search by WISE Item
```bash
GET /api/search/wise-item?wise_item_number=100027&top_k=20
```

### Product Details
```bash
GET /api/inventory/products/{id}
```

### ETL Operations
```bash
POST /api/etl/run
```

## 📊 Performance Metrics

### Search Performance
- **BM25 Search**: 50-150ms
- **Vector Search**: 100-300ms  
- **Hybrid Search**: 1-3 seconds (including AI reranking)
- **Index Size**: 330,000+ products

### ETL Performance
- **BM25 Indexing**: ~30 minutes
- **Vector Embedding**: 9-18 hours (CPU) / 2-5 hours (GPU)
- **Resume Capability**: Automatic checkpoint recovery

## 🗂️ Project Structure

```
Win-Supply/
├── server/                          # Backend FastAPI application
│   ├── app/
│   │   ├── api/                     # API endpoints
│   │   ├── services/                # Business logic
│   │   │   ├── embedding_service.py # Ollama embedding generation
│   │   │   ├── search_service.py    # Hybrid search logic
│   │   │   ├── reranker_service.py  # HuggingFace reranking
│   │   │   └── llm_matching_service.py # LLM product matching
│   │   ├── db/                      # Database clients
│   │   └── config/                  # Configuration
│   ├── etl_pipeline.py              # BM25 indexing pipeline
│   ├── embedding_etl_pipeline.py    # Vector embedding pipeline
│   ├── docker-compose.yml           # OpenSearch containers
│   └── requirements.txt             # Python dependencies
├── client/                          # Frontend React application
│   ├── src/
│   │   ├── pages/                   # React pages
│   │   ├── components/              # Reusable components
│   │   └── services/                # API clients
│   └── package.json                 # Node.js dependencies
└── docs/                            # Documentation
    ├── PHASE2_VECTOR_EMBEDDINGS.md
    ├── HYBRID_SEARCH_IMPLEMENTATION.md
    └── VECTOR_SEARCH_TEST_RESULTS.md
```

## 🐛 Troubleshooting

### OpenSearch Connection Failed
```bash
# Check containers
docker ps

# Check logs
docker logs opensearch-node1

# Restart if needed
docker-compose down && docker-compose up -d
```

### Ollama Connection Failed
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Verify model
ollama list
```

### PostgreSQL Connection Timeout
- Check network connectivity
- Verify connection string in `.env`
- Consider adding connection retry logic

### Out of Memory During ETL
- Reduce batch size: `--batch-size 25`
- Close other applications
- Increase system swap space

## 🚦 Development Phases

### ✅ Phase 1: BM25 Keyword Search
- PostgreSQL data extraction
- OpenSearch BM25 indexing
- FastAPI search endpoints
- React search interface

### ✅ Phase 2: Vector Embeddings
- Ollama integration for embeddings
- OpenSearch k-NN vector search
- Resume-capable ETL pipeline
- Vector similarity search

### ✅ Phase 3: Hybrid Search + Reranking
- Combined BM25 + Vector search
- HuggingFace AI reranking
- Advanced relevance scoring
- Production-ready search API

### 🔄 Phase 4: LLM Product Matching (In Progress)
- AI-powered product similarity
- Alternative product suggestions
- Advanced matching algorithms
- Business logic integration

## 📈 Scaling Considerations

### Performance Optimization
- Use GPU for Ollama (20-50x faster embeddings)
- Implement result caching (Redis)
- Add connection pooling
- Optimize batch sizes

### Production Deployment
- Use managed OpenSearch (AWS/GCP)
- Implement load balancing
- Add monitoring and alerting
- Set up CI/CD pipelines

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic Claude** for AI assistance
- **Ollama** for local LLM inference
- **OpenSearch** for powerful search capabilities
- **HuggingFace** for state-of-the-art AI models
- **FastAPI** for excellent API framework

