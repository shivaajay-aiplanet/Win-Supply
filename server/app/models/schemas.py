"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SearchRequest(BaseModel):
    """Request model for product search."""
    query: str = Field(..., description="Search query string")
    top_k: Optional[int] = Field(10, ge=1, le=100, description="Number of results to return")


class FieldSearchRequest(BaseModel):
    """Request model for field-specific search."""
    query: str = Field(..., description="Search query string")
    field: str = Field(..., description="Field name to search in")
    top_k: Optional[int] = Field(10, ge=1, le=100, description="Number of results to return")


class ETLRequest(BaseModel):
    """Request model for ETL pipeline execution."""
    recreate_index: Optional[bool] = Field(False, description="If true, delete and recreate the index")
    batch_size: Optional[int] = Field(1000, ge=100, le=10000, description="Number of records to process per batch")


class ProductDocument(BaseModel):
    """Model for a product document."""
    preferred_supplier: Optional[str] = None
    brand_name: Optional[str] = None
    wise_item_number: Optional[str] = None
    catalog_number: Optional[str] = None
    mainframe_description: Optional[str] = None
    win_item_name: Optional[str] = None


class SearchResult(BaseModel):
    """Model for a single search result."""
    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Relevance score")
    document: ProductDocument = Field(..., description="Product document")


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str = Field(..., description="Original search query")
    total_hits: int = Field(..., description="Total number of matching documents")
    returned_count: int = Field(..., description="Number of results returned")
    results: List[SearchResult] = Field(..., description="List of search results")


class DocumentResponse(BaseModel):
    """Response model for document retrieval."""
    id: str = Field(..., description="Document ID")
    found: bool = Field(..., description="Whether the document was found")
    document: Optional[ProductDocument] = Field(None, description="Product document if found")
    error: Optional[str] = Field(None, description="Error message if not found")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    components: Dict[str, Any] = Field(..., description="Component health status")


class IndexInfoResponse(BaseModel):
    """Response model for index information."""
    index_name: str = Field(..., description="Name of the index")
    document_count: int = Field(..., description="Number of documents in the index")
    indexed_fields: List[str] = Field(..., description="List of indexed fields")


class TableInfoResponse(BaseModel):
    """Response model for table information."""
    columns: List[Dict[str, str]] = Field(..., description="List of table columns")
    row_count: int = Field(..., description="Number of rows in the table")


class ETLStageResult(BaseModel):
    """Model for ETL stage result."""
    status: str = Field(..., description="Stage status")
    duration_seconds: float = Field(..., description="Stage duration in seconds")


class ETLResponse(BaseModel):
    """Response model for ETL pipeline execution."""
    status: str = Field(..., description="Pipeline status")
    start_time: str = Field(..., description="Pipeline start time")
    end_time: Optional[str] = Field(None, description="Pipeline end time")
    total_duration_seconds: Optional[float] = Field(None, description="Total duration in seconds")
    stages: Dict[str, Any] = Field(..., description="Stage-wise results")
    error: Optional[str] = Field(None, description="Error message if failed")

