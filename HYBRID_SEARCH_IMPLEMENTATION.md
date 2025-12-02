# Hybrid Search with Reranking - Implementation Guide

## Overview

This implementation adds a sophisticated hybrid search pipeline for product discovery by WISE item number, combining BM25 keyword search, vector semantic search, and AI-powered reranking.

## Architecture

```
WISE Item Number Input
        ↓
PostgreSQL Query (Get Product Details)
        ↓
Generate Query Text (Name + Description)
        ↓
    ┌───────────────────────────────┐
    │   Parallel Search Execution   │
    ├───────────────┬───────────────┤
    │   BM25        │   Vector      │
    │   Keyword     │   Semantic    │
    │   Search      │   Search      │
    └───────┬───────┴───────┬───────┘
            │               │
            └───────┬───────┘
                    ↓
        Combine & Deduplicate Results
                    ↓
        BAAI/bge-reranker-v2-m3
        (HuggingFace Reranker)
                    ↓
        Top 20 Re-ranked Results
```

## Features Implemented

### Backend Components

#### 1. Reranker Service (`server/app/services/reranker_service.py`)
- **Model**: BAAI/bge-reranker-v2-m3 from HuggingFace
- **Purpose**: Re-ranks combined search results by relevance
- **Features**:
  - HuggingFace Inference Client integration
  - Batch processing support
  - Relevance score calculation (0-1 range)
  - Fallback handling on errors

#### 2. Hybrid Search Service (`server/app/services/search_service.py`)
- **Function**: `hybrid_search_by_wise_item()`
- **Pipeline Steps**:
  1. Query PostgreSQL by WISE item number
  2. Generate embedding using Ollama (NomicEmbedTextV1.5)
  3. Execute BM25 keyword search (top 40 results)
  4. Execute vector semantic search (top 40 results)
  5. Combine and deduplicate results
  6. Rerank using BAAI/bge-reranker-v2-m3
  7. Return top 20 results with scores

#### 3. API Endpoint (`server/app/api/search.py`)
- **Endpoint**: `GET /api/search/wise-item`
- **Parameters**:
  - `wise_item_number` (required): WISE item number to search
  - `top_k` (optional, default=20): Number of results to return
- **Response**:
  ```json
  {
    "wise_item_number": "12345",
    "product_found": true,
    "query_text": "Product name and description",
    "source_product": {
      "id": 123,
      "wise_item_number": "12345",
      "win_item_name": "Product Name",
      "brand_name": "Brand"
    },
    "search_stats": {
      "keyword_results": 40,
      "vector_results": 40,
      "combined_unique": 65,
      "reranked_returned": 20
    },
    "total_results": 20,
    "results": [
      {
        "rank": 1,
        "id": "456",
        "relevance_score": 0.95,
        "keyword_score": 18.5,
        "vector_score": 0.87,
        "document": { /* product fields */ }
      }
    ]
  }
  ```

### Frontend Components

#### 1. Search Type Dropdown
- **Location**: Search bar, before "Top K Results" selector
- **Options**:
  - **All Fields**: Standard BM25 keyword search across all fields
  - **WISE Item Number**: Hybrid search with reranking

#### 2. Dynamic UI Updates
- **Search Placeholder**: Changes based on selected search type
- **Search Summary**: Shows "Hybrid Search" badge when active
- **Score Display**:
  - BM25 Mode: Blue badge with BM25 score
  - Hybrid Mode: Purple badge with relevance % + rank + breakdown (K/V scores)

#### 3. Results Display
- **Relevance Score**: Displayed as percentage (0-100%)
- **Rank**: Shows position in reranked results (#1, #2, etc.)
- **Score Breakdown**: Shows keyword (K) and vector (V) component scores
- **Best Match**: Green badge for top result

## Setup Instructions

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

New dependency added: `huggingface-hub==0.26.5`

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# HuggingFace API Token (optional but recommended for higher rate limits)
HF_TOKEN=your_huggingface_token_here
```

Get your token from: https://huggingface.co/settings/tokens

### 3. Verify Prerequisites

Ensure these services are running:

- **PostgreSQL**: win_inventory database with inventory table
- **OpenSearch**:
  - BM25 index: `inventory`
  - Vector index: `inventory_vector` (with embeddings)
- **Ollama**: Running locally on port 11434 with NomicEmbedTextV1.5 model

### 4. Start the Backend

```bash
cd server
uvicorn app.main:app --reload --port 8000
```

### 5. Start the Frontend

```bash
cd client
npm install
npm run dev
```

## Usage Guide

### Using Hybrid Search

1. **Open the application** in your browser (usually http://localhost:5173)

2. **Select "WISE Item Number"** from the search type dropdown

3. **Enter a WISE item number** in the search box (e.g., "100027")

4. **Click Search** or press Enter

5. **View Results**:
   - Purple "Hybrid Search" badge confirms hybrid mode
   - Relevance scores show as percentages
   - Rank numbers indicate position
   - K/V scores show keyword and vector components
   - Green "Best Match" badge highlights top result

### Understanding the Scores

- **Relevance Score (Purple Badge)**: AI reranker's confidence (0-100%)
  - Higher = More semantically relevant to the query product
  - Based on cross-encoder model analysis

- **K (Keyword Score)**: BM25 text matching score
  - Higher = More exact text/term matches
  - Traditional search relevance

- **V (Vector Score)**: Cosine similarity score
  - Higher = More semantically similar embeddings
  - Captures meaning beyond exact words

## API Testing

### Test with cURL

```bash
# Test hybrid search
curl "http://localhost:8000/api/search/wise-item?wise_item_number=100027&top_k=20"

# Test regular search (for comparison)
curl "http://localhost:8000/api/search?q=copper%20pipe&top_k=20"
```

### Test with Python

```python
import requests

# Hybrid search
response = requests.get(
    "http://localhost:8000/api/search/wise-item",
    params={
        "wise_item_number": "100027",
        "top_k": 20
    }
)
print(response.json())
```

## Performance Considerations

### Latency Breakdown (Approximate)

1. **PostgreSQL Query**: 10-50ms
2. **Embedding Generation**: 100-200ms (Ollama CPU)
3. **BM25 Search**: 50-150ms
4. **Vector Search**: 100-300ms
5. **Reranking** (20-40 items): 500-2000ms (HuggingFace API)

**Total**: ~1-3 seconds per query

### Optimization Tips

1. **Use HF_TOKEN**: Reduces reranker rate limiting
2. **GPU for Ollama**: Speeds up embedding generation significantly
3. **Adjust top_k**: Lower values = faster reranking
4. **Cache Results**: Consider caching for frequently searched items

## Troubleshooting

### "HF_TOKEN not found" Warning
- Non-critical: Public API will be used
- Set HF_TOKEN environment variable for better rate limits

### "Failed to generate embedding"
- Check Ollama service is running: `curl http://localhost:11434`
- Verify model is available: `ollama list`
- Pull model if needed: `ollama pull nomic-embed-text`

### "Product not found for WISE item number"
- Verify the WISE item number exists in PostgreSQL
- Check database connection settings
- Ensure wise_item_number field is populated

### Vector search returns no results
- Verify vector index is populated: `test_vector_search.py`
- Check embedding dimensions match (768)
- Ensure OpenSearch k-NN plugin is enabled

## Files Modified/Created

### Backend
- ✅ `server/app/services/reranker_service.py` (NEW)
- ✅ `server/app/services/search_service.py` (MODIFIED)
- ✅ `server/app/api/search.py` (MODIFIED)
- ✅ `server/requirements.txt` (MODIFIED)

### Frontend
- ✅ `client/src/pages/Inventory.jsx` (MODIFIED)

### Documentation
- ✅ `HYBRID_SEARCH_IMPLEMENTATION.md` (THIS FILE)

## Next Steps

### Recommended Enhancements

1. **Caching Layer**
   - Cache reranked results for frequently searched items
   - Use Redis for distributed caching

2. **Analytics**
   - Track search performance metrics
   - Log reranker scores for analysis
   - A/B test reranker effectiveness

3. **Weighted Hybrid Search**
   - Allow adjusting BM25 vs Vector weights
   - Dynamic weight optimization based on query type

4. **Batch Reranking**
   - Process multiple queries in parallel
   - Optimize for bulk operations

5. **Alternative Rerankers**
   - Test other models (e.g., ms-marco-MiniLM)
   - Compare performance vs quality tradeoffs

## References

- **BAAI/bge-reranker-v2-m3**: https://huggingface.co/BAAI/bge-reranker-v2-m3
- **Ollama**: https://ollama.ai/
- **OpenSearch k-NN**: https://opensearch.org/docs/latest/search-plugins/knn/
- **HuggingFace Inference API**: https://huggingface.co/docs/api-inference/

---

**Implementation Date**: 2025-11-12
**Status**: ✅ Complete and Ready for Testing
