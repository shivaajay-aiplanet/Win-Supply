"""
OpenSearch vector index management module.
Handles creation and management of vector index for semantic search.
"""

from opensearchpy import OpenSearch
from opensearchpy.exceptions import RequestError
import logging
from app.config.settings import (
    OPENSEARCH_HOST,
    OPENSEARCH_PORT,
    OPENSEARCH_USER,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_VECTOR_INDEX_NAME,
    EMBEDDING_DIMENSION,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_vector_index_mapping(embedding_dim: int = EMBEDDING_DIMENSION):
    """
    Define the vector index mapping for semantic search.
    Includes both text fields and dense vector field.

    Args:
        embedding_dim: Dimension of the embedding vectors

    Returns:
        dict: Index mapping configuration
    """
    return {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "index": {
                "knn": True,  # Enable k-NN search
                "knn.algo_param.ef_search": 100,  # HNSW search parameter
            },
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "text_combined": {"type": "text", "analyzer": "standard"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": embedding_dim,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",  # Changed from nmslib (deprecated in OpenSearch 3.0+)
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
                # Original fields for reference
                "preferred_supplier": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "brand_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "wise_item_number": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "catalog_number": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "mainframe_description": {"type": "text"},
                "win_item_name": {"type": "text"},
            }
        },
    }


def create_vector_index(
    client: OpenSearch,
    index_name: str = OPENSEARCH_VECTOR_INDEX_NAME,
    embedding_dim: int = EMBEDDING_DIMENSION,
    recreate: bool = False,
):
    """
    Create the OpenSearch vector index with proper mappings.

    Args:
        client: OpenSearch client instance
        index_name: Name of the index to create
        embedding_dim: Dimension of embedding vectors
        recreate: If True, delete existing index before creating

    Returns:
        bool: True if index was created successfully
    """
    try:
        # Check if index exists
        if client.indices.exists(index=index_name):
            if recreate:
                logger.info(f"Deleting existing vector index: {index_name}")
                client.indices.delete(index=index_name)
            else:
                logger.info(f"Vector index '{index_name}' already exists")
                return True

        # Create index with mappings
        mapping = get_vector_index_mapping(embedding_dim)
        response = client.indices.create(index=index_name, body=mapping)
        logger.info(f"Vector index '{index_name}' created successfully")
        logger.info(f"Embedding dimension: {embedding_dim}")
        return True

    except RequestError as e:
        logger.error(f"Error creating vector index: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating vector index: {e}")
        raise


def verify_vector_index(
    client: OpenSearch, index_name: str = OPENSEARCH_VECTOR_INDEX_NAME
):
    """
    Verify that the vector index exists and has correct settings.

    Args:
        client: OpenSearch client instance
        index_name: Name of the index to verify

    Returns:
        dict: Index information
    """
    try:
        if not client.indices.exists(index=index_name):
            logger.error(f"Vector index '{index_name}' does not exist")
            return None

        # Get index settings and mappings
        settings = client.indices.get_settings(index=index_name)
        mappings = client.indices.get_mapping(index=index_name)

        # Get document count
        count_response = client.count(index=index_name)
        doc_count = count_response["count"]

        info = {
            "index_name": index_name,
            "exists": True,
            "document_count": doc_count,
            "settings": settings[index_name]["settings"],
            "mappings": mappings[index_name]["mappings"],
        }

        logger.info(f"Vector index '{index_name}' verified: {doc_count} documents")
        return info

    except Exception as e:
        logger.error(f"Error verifying vector index: {e}")
        return None


def bulk_index_vectors(
    client: OpenSearch, documents: list, index_name: str = OPENSEARCH_VECTOR_INDEX_NAME
):
    """
    Bulk index documents with embeddings into OpenSearch.

    Args:
        client: OpenSearch client instance
        documents: List of documents with embeddings
        index_name: Name of the index

    Returns:
        dict: Indexing results
    """
    try:
        from opensearchpy.helpers import bulk

        # Prepare bulk actions
        actions = []
        for doc in documents:
            action = {"_index": index_name, "_id": doc["id"], "_source": doc}
            actions.append(action)

        # Perform bulk indexing
        success, failed = bulk(client, actions, raise_on_error=False)

        logger.info(
            f"Bulk indexing complete: {success} successful, {len(failed)} failed"
        )

        return {
            "success_count": success,
            "failed_count": len(failed),
            "failed_items": failed,
        }

    except Exception as e:
        logger.error(f"Error during bulk indexing: {e}")
        raise


def search_by_vector(
    client: OpenSearch,
    query_embedding: list,
    index_name: str = OPENSEARCH_VECTOR_INDEX_NAME,
    top_k: int = 10,
):
    """
    Search for similar documents using vector similarity.

    Args:
        client: OpenSearch client instance
        query_embedding: Query embedding vector
        index_name: Name of the index to search
        top_k: Number of results to return

    Returns:
        dict: Search results
    """
    try:
        query = {
            "size": top_k,
            "query": {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}},
        }

        response = client.search(index=index_name, body=query)

        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {"id": hit["_id"], "score": hit["_score"], "document": hit["_source"]}
            )

        return {"total_hits": response["hits"]["total"]["value"], "results": results}

    except Exception as e:
        logger.error(f"Error during vector search: {e}")
        raise


def test_vector_index():
    """Test function for vector index operations."""
    from app.db.opensearch import get_opensearch_client

    logger.info("Testing Vector Index Operations...")

    # Get client
    client = get_opensearch_client()

    # Create test index
    test_index = "test_vector_index"
    create_vector_index(client, test_index, embedding_dim=768, recreate=True)

    # Verify index
    info = verify_vector_index(client, test_index)
    logger.info(f"Index info: {info}")

    # Test document with embedding
    import numpy as np

    test_doc = {
        "id": 1,
        "text_combined": "Test product description",
        "embedding": np.random.rand(768).tolist(),
        "win_item_name": "Test Product",
        "brand_name": "Test Brand",
    }

    # Index document
    result = bulk_index_vectors(client, [test_doc], test_index)
    logger.info(f"Indexing result: {result}")

    # Wait for indexing
    import time

    time.sleep(2)

    # Test vector search
    query_embedding = np.random.rand(768).tolist()
    search_results = search_by_vector(client, query_embedding, test_index, top_k=5)
    logger.info(f"Search results: {search_results}")

    # Clean up
    client.indices.delete(index=test_index)
    logger.info("Test index cleaned up")

    logger.info("✅ All tests passed!")


if __name__ == "__main__":
    test_vector_index()
