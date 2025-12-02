"""
Search API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
import logging
from app.models.schemas import SearchRequest, FieldSearchRequest
from app.services.search_service import (
    search_products,
    search_by_field,
    get_document_by_id,
    hybrid_search_by_wise_item,
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query string"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
):
    """
    Search for products using BM25 keyword search across all fields.

    - **q**: Search query string (required)
    - **top_k**: Number of top results to return (default: 10, max: 100)
    """
    try:
        results = search_products(q, top_k=top_k)

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search")
async def search_post(request: SearchRequest):
    """
    Search for products using BM25 keyword search (POST method).

    Request body:
    - **query**: Search query string
    - **top_k**: Number of results to return (optional, default: 10)
    """
    try:
        results = search_products(request.query, top_k=request.top_k)

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/field")
async def search_field(
    q: str = Query(..., description="Search query string"),
    field: str = Query(..., description="Field name to search in"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
):
    """
    Search for products in a specific field.

    - **q**: Search query string (required)
    - **field**: Field name to search in (required)
    - **top_k**: Number of top results to return (default: 10, max: 100)

    Available fields: preferred_supplier, brand_name, wise_item_number,
                     catalog_number, mainframe_description, win_item_name
    """
    try:
        results = search_by_field(q, field, top_k=top_k)

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Field search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """
    Retrieve a specific document by its ID.

    - **doc_id**: Document ID (PostgreSQL id field)
    """
    try:
        result = get_document_by_id(doc_id)

        if not result.get("found"):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.get("/search/wise-item")
async def search_by_wise_item(
    wise_item_number: str = Query(..., description="WISE item number to search for"),
    top_k: int = Query(20, ge=1, le=100, description="Number of results to return"),
):
    """
    Hybrid search for product discovery by WISE item number.

    This endpoint implements a sophisticated hybrid search pipeline:
    1. Retrieves product details from PostgreSQL by WISE item number
    2. Generates embedding from product name + description using Ollama (NomicEmbedTextV1.5)
    3. Executes parallel BM25 keyword search in OpenSearch
    4. Executes parallel vector search using semantic embeddings
    5. Combines and deduplicates results from both search methods
    6. Reranks all results using BAAI/bge-reranker-v2-m3 for optimal relevance
    7. Returns top 20 results sorted by reranker relevance score

    - **wise_item_number**: WISE item number (required)
    - **top_k**: Number of top results to return after reranking (default: 20, max: 100)

    Returns:
    - **wise_item_number**: Input WISE item number
    - **product_found**: Whether the source product was found
    - **query_text**: Generated query text from product name/description
    - **source_product**: Details of the source product
    - **search_stats**: Statistics about keyword, vector, and combined results
    - **total_results**: Number of results returned
    - **results**: Array of reranked results with relevance scores
    """
    try:
        logger.info(
            f"Hybrid search request for WISE item: {wise_item_number}, top_k: {top_k}"
        )

        results = hybrid_search_by_wise_item(
            wise_item_number=wise_item_number, top_k=top_k
        )

        if "error" in results and not results.get("product_found"):
            raise HTTPException(status_code=404, detail=results["error"])

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
