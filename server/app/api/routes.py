"""
API routes aggregator.
Combines all API routers into a single router.
"""

from fastapi import APIRouter
from app.api import health, search, index, etl, inventory, bulk_upload

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health.router, prefix="/api", tags=["Health"])
api_router.include_router(search.router, prefix="/api", tags=["Search"])
api_router.include_router(index.router, prefix="/api", tags=["Index"])
api_router.include_router(etl.router, prefix="/api", tags=["ETL"])
api_router.include_router(inventory.router, prefix="/api", tags=["Inventory"])
api_router.include_router(bulk_upload.router, prefix="/api", tags=["Bulk Upload"])
