"""
Data transformation service.
Handles data cleaning and preparation for OpenSearch indexing.
"""
import logging
from app.config.settings import FIELDS_TO_INDEX

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text_field(value):
    """
    Clean a text field value.
    
    Args:
        value: Field value (can be None, string, or other type)
        
    Returns:
        str or None: Cleaned string value or None if empty
    """
    if value is None:
        return None
    
    # Convert to string and strip whitespace
    cleaned = str(value).strip()
    
    # Return None for empty strings
    if not cleaned or cleaned.lower() in ['null', 'none', 'n/a', '']:
        return None
    
    return cleaned


def transform_record(record):
    """
    Transform a single record from PostgreSQL format to OpenSearch document format.
    
    Args:
        record (dict): Raw record from PostgreSQL
        
    Returns:
        dict or None: Transformed document ready for indexing, or None if invalid
    """
    try:
        # Extract document ID
        doc_id = record.get('id')
        if doc_id is None:
            logger.warning("Record missing 'id' field, skipping")
            return None
        
        # Build document with only the required fields
        document = {}
        has_content = False
        
        for field in FIELDS_TO_INDEX:
            cleaned_value = clean_text_field(record.get(field))
            document[field] = cleaned_value
            
            # Track if we have at least one non-null field
            if cleaned_value is not None:
                has_content = True
        
        # Skip documents with all null fields
        if not has_content:
            logger.warning(f"Record {doc_id} has all null fields, skipping")
            return None
        
        return {
            "id": doc_id,
            "document": document
        }
        
    except Exception as e:
        logger.error(f"Error transforming record: {e}")
        return None


def transform_batch(records):
    """
    Transform a batch of records.
    
    Args:
        records (list): List of raw records from PostgreSQL
        
    Returns:
        list: List of transformed documents ready for indexing
    """
    transformed = []
    skipped = 0
    
    for record in records:
        result = transform_record(record)
        if result:
            transformed.append(result)
        else:
            skipped += 1
    
    if skipped > 0:
        logger.info(f"Skipped {skipped} invalid records in batch")
    
    return transformed


def get_transformation_stats(records):
    """
    Get statistics about the data transformation.
    
    Args:
        records (list): List of raw records
        
    Returns:
        dict: Statistics about field completeness
    """
    stats = {
        "total_records": len(records),
        "field_stats": {}
    }
    
    for field in FIELDS_TO_INDEX:
        non_null_count = sum(1 for r in records if clean_text_field(r.get(field)) is not None)
        stats["field_stats"][field] = {
            "non_null": non_null_count,
            "null": len(records) - non_null_count,
            "completeness": (non_null_count / len(records) * 100) if records else 0
        }
    
    return stats

