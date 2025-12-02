"""
Quick test to verify the resume functionality works correctly.
"""

import logging
from app.db.postgres import get_postgres_connection
from app.services.progress_tracker import ProgressTracker
from app.config.settings import POSTGRES_TABLE_NAME, FIELDS_TO_INDEX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_resume_query():
    """Test that the new query correctly fetches unprocessed records."""
    
    # Get progress tracker
    tracker = ProgressTracker()
    last_id = tracker.get_last_processed_id() or 0
    
    logger.info(f"Last processed ID: {last_id}")
    
    # Connect to PostgreSQL
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # Build query (same as in ETL pipeline)
    fields = ["id"] + FIELDS_TO_INDEX
    fields_str = ", ".join(fields)
    
    query = f"""
        SELECT {fields_str}
        FROM public.{POSTGRES_TABLE_NAME}
        WHERE id > %s
        ORDER BY id
        LIMIT 5
    """
    
    cursor.execute(query, (last_id,))
    
    # Fetch results
    columns = [desc[0] for desc in cursor.description]
    records = []
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        records.append(record)
    
    cursor.close()
    conn.close()
    tracker.close()
    
    # Display results
    logger.info(f"\nFound {len(records)} unprocessed records:")
    for i, record in enumerate(records, 1):
        logger.info(f"  {i}. ID: {record['id']} - {record.get('win_item_name', 'N/A')[:50]}")
    
    if records:
        logger.info(f"\n✅ Resume query works! Next batch will start from ID {last_id + 1}")
        logger.info(f"   First unprocessed record ID: {records[0]['id']}")
        return True
    else:
        logger.warning(f"\n⚠️ No unprocessed records found after ID {last_id}")
        logger.info("   This might mean all records are already processed!")
        return False

if __name__ == "__main__":
    test_resume_query()

