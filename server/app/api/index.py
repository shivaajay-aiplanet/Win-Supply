"""
Index management API endpoints.
"""
from fastapi import APIRouter, HTTPException
import logging
from app.db.opensearch import get_opensearch_client, verify_index
from app.db.postgres import get_table_info
from app.config.settings import OPENSEARCH_INDEX_NAME, FIELDS_TO_INDEX

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/index/info")
async def get_index_info():
    """Get information about the OpenSearch index."""
    try:
        os_client = get_opensearch_client()
        index_info = verify_index(os_client, OPENSEARCH_INDEX_NAME)

        if not index_info:
            raise HTTPException(status_code=404, detail="Index not found")

        return {
            "index_name": OPENSEARCH_INDEX_NAME,
            "document_count": index_info["document_count"],
            "indexed_fields": FIELDS_TO_INDEX,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index info error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get index info: {str(e)}"
        )


@router.get("/source/info")
async def get_source_info():
    """Get information about the PostgreSQL source table."""
    try:
        table_info = get_table_info()
        return table_info
    except Exception as e:
        logger.error(f"Source info error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get source info: {str(e)}"
        )

