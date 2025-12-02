"""
Bulk indexing service for OpenSearch.
Handles bulk indexing operations with error handling and logging.
"""

from opensearchpy import helpers
import logging
from app.config.settings import OPENSEARCH_INDEX_NAME, BULK_INDEX_BATCH_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_bulk_actions(documents, index_name=OPENSEARCH_INDEX_NAME):
    """
    Prepare documents for bulk indexing.

    Args:
        documents (list): List of transformed documents with 'id' and 'document' keys
        index_name (str): Name of the index

    Yields:
        dict: Bulk action for each document
    """
    for doc in documents:
        yield {"_index": index_name, "_id": doc["id"], "_source": doc["document"]}


def bulk_index_documents(client, documents, index_name=OPENSEARCH_INDEX_NAME):
    """
    Bulk index documents into OpenSearch.

    Args:
        client (OpenSearch): OpenSearch client instance
        documents (list): List of transformed documents
        index_name (str): Name of the index

    Returns:
        dict: Indexing results with success and error counts
    """
    if not documents:
        logger.warning("No documents to index")
        return {"success": 0, "failed": 0, "errors": []}

    try:
        # Prepare bulk actions
        actions = list(prepare_bulk_actions(documents, index_name))

        # Perform bulk indexing
        success_count = 0
        failed_count = 0
        errors = []

        # Use helpers.bulk for efficient bulk indexing
        success, failed = helpers.bulk(
            client,
            actions,
            chunk_size=BULK_INDEX_BATCH_SIZE,
            raise_on_error=False,
            raise_on_exception=False,
            max_retries=3,
            initial_backoff=2,
        )

        success_count = success
        failed_count = len(failed) if isinstance(failed, list) else 0

        if failed:
            for item in failed:
                error_info = {
                    "id": item.get("index", {}).get("_id"),
                    "error": item.get("index", {}).get("error"),
                }
                errors.append(error_info)
                logger.error(
                    f"Failed to index document {error_info['id']}: {error_info['error']}"
                )

        logger.info(
            f"Bulk indexing completed: {success_count} succeeded, {failed_count} failed"
        )

        return {"success": success_count, "failed": failed_count, "errors": errors}

    except Exception as e:
        logger.error(f"Unexpected error during bulk indexing: {e}")
        raise


def index_all_documents(client, document_batches, index_name=OPENSEARCH_INDEX_NAME):
    """
    Index all documents from multiple batches.

    Args:
        client (OpenSearch): OpenSearch client instance
        document_batches (generator): Generator yielding batches of documents
        index_name (str): Name of the index

    Returns:
        dict: Overall indexing statistics
    """
    total_success = 0
    total_failed = 0
    all_errors = []
    batch_count = 0

    try:
        for batch in document_batches:
            batch_count += 1
            logger.info(f"Processing batch {batch_count} with {len(batch)} documents")

            result = bulk_index_documents(client, batch, index_name)

            total_success += result["success"]
            total_failed += result["failed"]
            all_errors.extend(result["errors"])

        logger.info(f"Indexing completed: {batch_count} batches processed")
        logger.info(f"Total: {total_success} succeeded, {total_failed} failed")

        return {
            "total_batches": batch_count,
            "total_success": total_success,
            "total_failed": total_failed,
            "errors": all_errors,
        }

    except Exception as e:
        logger.error(f"Error during batch indexing: {e}")
        raise


def refresh_index(client, index_name=OPENSEARCH_INDEX_NAME):
    """
    Refresh the index to make all indexed documents searchable.

    Args:
        client (OpenSearch): OpenSearch client instance
        index_name (str): Name of the index
    """
    try:
        client.indices.refresh(index=index_name)
        logger.info(f"Index '{index_name}' refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing index: {e}")
        raise

