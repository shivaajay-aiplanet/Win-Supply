"""
PostgreSQL data extraction module.
Handles connection to PostgreSQL and data extraction.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from app.config.settings import (
    POSTGRES_CONNECTION_STRING,
    FIELDS_TO_INDEX,
    POSTGRES_TABLE_NAME,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_postgres_connection():
    """
    Create and return a PostgreSQL connection.

    Returns:
        psycopg2.connection: PostgreSQL connection object
    """
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        logger.info("Successfully connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


def extract_product_data(batch_size=1000):
    """
    Extract product data from PostgreSQL database.
    Yields batches of records with only the required fields.

    Args:
        batch_size (int): Number of records to fetch per batch

    Yields:
        list: Batch of product records as dictionaries
    """
    conn = None
    cursor = None

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build the SELECT query with only required fields
        fields = ["id"] + FIELDS_TO_INDEX
        fields_str = ", ".join(fields)

        query = f"SELECT {fields_str} FROM public.{POSTGRES_TABLE_NAME} ORDER BY id"

        logger.info(f"Executing query: {query}")
        cursor.execute(query)

        total_records = 0
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break

            total_records += len(batch)
            logger.info(f"Fetched {len(batch)} records (total: {total_records})")

            # Convert to list of dicts
            yield [dict(record) for record in batch]

        logger.info(f"Total records extracted: {total_records}")

    except Exception as e:
        logger.error(f"Error extracting data from PostgreSQL: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("PostgreSQL connection closed")


def get_table_info():
    """
    Get information about the inventory table (column names, row count).

    Returns:
        dict: Table information including columns and row count
    """
    conn = None
    cursor = None

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        # Get column information
        cursor.execute(
            f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{POSTGRES_TABLE_NAME}'
            ORDER BY ordinal_position
        """
        )
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM public.{POSTGRES_TABLE_NAME}")
        row_count = cursor.fetchone()[0]

        logger.info(
            f"Table '{POSTGRES_TABLE_NAME}' has {len(columns)} columns and {row_count} rows"
        )

        return {
            "columns": [{"name": col[0], "type": col[1]} for col in columns],
            "row_count": row_count,
        }

    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_paginated_products(page=1, page_size=10):
    """
    Get paginated product data from PostgreSQL.

    Args:
        page (int): Page number (1-indexed)
        page_size (int): Number of records per page

    Returns:
        dict: Paginated results with products, total count, and pagination info
    """
    conn = None
    cursor = None

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM public.{POSTGRES_TABLE_NAME}")
        total_count = cursor.fetchone()["count"]

        # Get paginated data - fetch all columns
        query = f"""
            SELECT *
            FROM public.{POSTGRES_TABLE_NAME}
            ORDER BY id
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (page_size, offset))
        products = [dict(record) for record in cursor.fetchall()]

        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size

        logger.info(
            f"Fetched page {page}/{total_pages} ({len(products)} products, total: {total_count})"
        )

        return {
            "products": products,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching paginated products: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection():
    """
    Test the PostgreSQL connection and return basic database info.

    Returns:
        dict: Database connection status and version info
    """
    conn = None
    cursor = None

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        # Get PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]

        # Get current database name
        cursor.execute("SELECT current_database()")
        database = cursor.fetchone()[0]

        logger.info(f"Connected to database: {database}")
        logger.info(f"PostgreSQL version: {version}")

        return {"status": "connected", "database": database, "version": version}

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
