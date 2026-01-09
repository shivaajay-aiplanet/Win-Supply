"""
Bulk Upload API endpoints.
Handles bulk upload of products and cross-reference data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config.settings import (
    POSTGRES_CONNECTION_STRING,
    POSTGRES_TABLE_NAME,
    OPENSEARCH_VECTOR_INDEX_NAME,
)
from app.db.opensearch import get_opensearch_client
from app.db.opensearch_vector import bulk_index_vectors
from app.services.embedding_service import OllamaEmbeddingService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


class ProductUpload(BaseModel):
    """Model for a product to upload."""

    wise_item_number: str
    win_item_name: Optional[str] = None
    brand_name: Optional[str] = None
    catalog_number: Optional[str] = None
    mainframe_description: Optional[str] = None
    preferred_supplier: Optional[str] = None


class BulkProductUploadRequest(BaseModel):
    """Request model for bulk product upload."""

    products: List[ProductUpload]


class CrossReferenceMatch(BaseModel):
    """Model for a single cross-reference match in compact format."""

    r: str  # Format: "WISE_ITEM_NUMBER|SCORE|ATTRS"


class CrossReferenceEntry(BaseModel):
    """Model for a cross-reference entry."""

    wise_item_number: str
    llm_matches: List[CrossReferenceMatch]


class BulkCrossReferenceRequest(BaseModel):
    """Request model for bulk saving cross-references."""

    cross_references: List[CrossReferenceEntry]


@router.post("/bulk-upload/save-cross-references")
async def save_cross_references(request: BulkCrossReferenceRequest):
    """
    Save multiple cross-reference entries to the database.

    This endpoint handles bulk saving of cross-reference data from the bulk upload process.
    Uses UPSERT to handle duplicates - existing entries will be updated.

    - **cross_references**: List of cross-reference entries with wise_item_number and llm_matches

    Returns:
    - **success**: Whether the operation was successful
    - **saved_count**: Number of entries saved
    - **updated_count**: Number of entries updated (existing entries)
    - **error_count**: Number of entries that failed
    """
    conn = None
    saved_count = 0
    updated_count = 0
    error_count = 0
    errors = []

    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        for entry in request.cross_references:
            try:
                # Check if entry already exists
                cursor.execute(
                    """
                    SELECT id FROM public.cross_reference
                    WHERE wise_item_number = %s
                    """,
                    (entry.wise_item_number,),
                )
                existing = cursor.fetchone()

                # Convert matches to JSON-serializable format
                llm_matches_json = [{"r": match.r} for match in entry.llm_matches]

                # Use UPSERT to save or update
                cursor.execute(
                    """
                    INSERT INTO public.cross_reference (wise_item_number, llm_matches)
                    VALUES (%s, %s)
                    ON CONFLICT (wise_item_number)
                    DO UPDATE SET llm_matches = EXCLUDED.llm_matches, updated_at = CURRENT_TIMESTAMP
                    """,
                    (entry.wise_item_number, json.dumps(llm_matches_json)),
                )

                if existing:
                    updated_count += 1
                else:
                    saved_count += 1

            except Exception as e:
                error_count += 1
                errors.append(
                    {"wise_item_number": entry.wise_item_number, "error": str(e)}
                )
                logger.error(
                    f"Error saving cross-reference for {entry.wise_item_number}: {e}"
                )

        conn.commit()

        logger.info(
            f"Bulk save complete: {saved_count} saved, {updated_count} updated, {error_count} errors"
        )

        return {
            "success": True,
            "saved_count": saved_count,
            "updated_count": updated_count,
            "error_count": error_count,
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Bulk save cross-references error: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to save cross-references: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


@router.post("/bulk-upload/upload-products")
async def upload_products_to_inventory(request: BulkProductUploadRequest):
    """
    Upload products to inventory table and index in OpenSearch.

    This endpoint:
    1. Inserts products into PostgreSQL inventory table
    2. Generates embeddings for each product
    3. Indexes products in OpenSearch for search

    - **products**: List of products with wise_item_number and optional fields

    Returns:
    - **success**: Whether the operation was successful
    - **inserted_count**: Number of new products inserted
    - **updated_count**: Number of existing products updated
    - **indexed_count**: Number of products indexed in OpenSearch
    - **error_count**: Number of products that failed
    """
    conn = None
    inserted_count = 0
    updated_count = 0
    indexed_count = 0
    error_count = 0
    errors = []
    inserted_ids = []

    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Insert/Update products in PostgreSQL
        for product in request.products:
            try:
                # Check if product already exists
                cursor.execute(
                    f"""
                    SELECT id FROM public.{POSTGRES_TABLE_NAME}
                    WHERE wise_item_number = %s
                    """,
                    (product.wise_item_number,),
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing product
                    cursor.execute(
                        f"""
                        UPDATE public.{POSTGRES_TABLE_NAME}
                        SET win_item_name = COALESCE(%s, win_item_name),
                            brand_name = COALESCE(%s, brand_name),
                            catalog_number = COALESCE(%s, catalog_number),
                            mainframe_description = COALESCE(%s, mainframe_description),
                            preferred_supplier = COALESCE(%s, preferred_supplier)
                        WHERE wise_item_number = %s
                        RETURNING id
                        """,
                        (
                            product.win_item_name,
                            product.brand_name,
                            product.catalog_number,
                            product.mainframe_description,
                            product.preferred_supplier,
                            product.wise_item_number,
                        ),
                    )
                    result = cursor.fetchone()
                    if result:
                        inserted_ids.append(result["id"])
                    updated_count += 1
                else:
                    # Insert new product
                    cursor.execute(
                        f"""
                        INSERT INTO public.{POSTGRES_TABLE_NAME}
                        (wise_item_number, win_item_name, brand_name, catalog_number,
                         mainframe_description, preferred_supplier)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            product.wise_item_number,
                            product.win_item_name,
                            product.brand_name,
                            product.catalog_number,
                            product.mainframe_description,
                            product.preferred_supplier,
                        ),
                    )
                    result = cursor.fetchone()
                    if result:
                        inserted_ids.append(result["id"])
                    inserted_count += 1

            except Exception as e:
                error_count += 1
                errors.append(
                    {
                        "wise_item_number": product.wise_item_number,
                        "stage": "postgresql_insert",
                        "error": str(e),
                    }
                )
                logger.error(f"Error inserting product {product.wise_item_number}: {e}")

        conn.commit()
        logger.info(f"PostgreSQL: {inserted_count} inserted, {updated_count} updated")

        # Step 2: Generate embeddings and index in OpenSearch
        if inserted_ids:
            try:
                # Fetch the inserted/updated products
                cursor.execute(
                    f"""
                    SELECT id, preferred_supplier, brand_name, wise_item_number,
                           catalog_number, mainframe_description, win_item_name
                    FROM public.{POSTGRES_TABLE_NAME}
                    WHERE id = ANY(%s)
                    """,
                    (inserted_ids,),
                )
                products_to_index = cursor.fetchall()

                if products_to_index:
                    # Convert to list of dicts
                    records = [dict(row) for row in products_to_index]

                    # Generate embeddings
                    embedding_service = OllamaEmbeddingService()
                    enriched_records = embedding_service.generate_batch_embeddings(
                        records, show_progress=False
                    )

                    if enriched_records:
                        # Index into OpenSearch
                        os_client = get_opensearch_client()
                        result = bulk_index_vectors(
                            os_client, enriched_records, OPENSEARCH_VECTOR_INDEX_NAME
                        )
                        indexed_count = result.get("success_count", 0)
                        logger.info(f"OpenSearch: {indexed_count} products indexed")

            except Exception as e:
                logger.error(f"Error indexing products in OpenSearch: {e}")
                errors.append({"stage": "opensearch_indexing", "error": str(e)})

        return {
            "success": True,
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "indexed_count": indexed_count,
            "error_count": error_count,
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Bulk upload products error: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to upload products: {str(e)}"
        )
    finally:
        if conn:
            conn.close()
