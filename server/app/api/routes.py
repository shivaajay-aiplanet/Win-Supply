"""
API routes aggregator.
Combines all API routers into a single router.
"""

from fastapi import APIRouter, Depends
from app.api import health, search, index, etl, inventory, bulk_upload, auth
from app.api.deps import get_current_user

# Create main API router
api_router = APIRouter()

# Public routes (no auth required)
api_router.include_router(health.router, prefix="/api", tags=["Health"])
api_router.include_router(auth.router, prefix="/api", tags=["Auth"])

# Protected routes (auth required)
api_router.include_router(
    search.router, prefix="/api", tags=["Search"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    index.router, prefix="/api", tags=["Index"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    etl.router, prefix="/api", tags=["ETL"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    inventory.router, prefix="/api", tags=["Inventory"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    bulk_upload.router, prefix="/api", tags=["Bulk Upload"],
    dependencies=[Depends(get_current_user)]
)
