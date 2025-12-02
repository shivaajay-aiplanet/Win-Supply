"""
Inventory API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
import logging
from app.db.postgres import get_paginated_products

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/inventory/products")
async def get_inventory_products(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of products per page"),
):
    """
    Get paginated inventory products from PostgreSQL.

    - **page**: Page number (default: 1, min: 1)
    - **page_size**: Number of products per page (default: 10, max: 100)

    Returns paginated product data with pagination metadata.
    """
    try:
        result = get_paginated_products(page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error fetching inventory products: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch inventory: {str(e)}"
        )

