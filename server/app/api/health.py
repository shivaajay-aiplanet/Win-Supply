"""
Health check API endpoints.
"""
from fastapi import APIRouter, HTTPException
import logging
from app.db.opensearch import get_opensearch_client
from app.db.postgres import test_connection
from app.config.settings import OPENSEARCH_INDEX_NAME

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint that verifies all system components."""
    try:
        # Check OpenSearch connection
        os_client = get_opensearch_client()
        index_exists = os_client.indices.exists(index=OPENSEARCH_INDEX_NAME)

        # Check PostgreSQL connection
        pg_status = test_connection()

        return {
            "status": "healthy",
            "service": "Product Search API",
            "components": {
                "opensearch": {
                    "connected": True,
                    "index_exists": index_exists,
                    "index_name": OPENSEARCH_INDEX_NAME,
                },
                "postgresql": pg_status,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

