"""
ETL pipeline API endpoints.
"""
from fastapi import APIRouter, HTTPException
import logging
from app.models.schemas import ETLRequest
from app.services.etl_service import run_etl_pipeline

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/etl/run")
async def run_etl(request: ETLRequest):
    """
    Run the ETL pipeline to index data from PostgreSQL to OpenSearch.

    Request body:
    - **recreate_index**: If true, delete and recreate the index (default: false)
    - **batch_size**: Number of records to process per batch (default: 1000)

    ⚠️ Warning: This operation may take several minutes depending on data size.
    """
    try:
        logger.info(f"Starting ETL pipeline (recreate_index={request.recreate_index})")
        results = run_etl_pipeline(
            recreate_index=request.recreate_index, batch_size=request.batch_size
        )
        return results
    except Exception as e:
        logger.error(f"ETL pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"ETL pipeline failed: {str(e)}")

