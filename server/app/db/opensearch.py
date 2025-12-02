"""
OpenSearch client and index management module.
Handles connection to OpenSearch and index creation with proper mappings.
"""
from opensearchpy import OpenSearch
from opensearchpy.exceptions import RequestError
import logging
from app.config.settings import (
    OPENSEARCH_HOST,
    OPENSEARCH_PORT,
    OPENSEARCH_USER,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_opensearch_client():
    """
    Create and return an OpenSearch client instance.
    
    Returns:
        OpenSearch: Configured OpenSearch client
    """
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )
    
    # Test connection
    try:
        info = client.info()
        logger.info(f"Connected to OpenSearch cluster: {info['cluster_name']}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to OpenSearch: {e}")
        raise


def get_index_mapping():
    """
    Define the index mapping with text analyzers for BM25 search.
    Includes standard analyzer and edge n-gram analyzer for partial matching.
    
    Returns:
        dict: Index mapping configuration
    """
    return {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "standard_analyzer": {
                        "type": "standard",
                        "stopwords": "_english_"
                    },
                    "edge_ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "edge_ngram_tokenizer",
                        "filter": ["lowercase", "asciifolding"]
                    },
                    "edge_ngram_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"]
                    }
                },
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "preferred_supplier": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        },
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "brand_name": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        },
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "wise_item_number": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        },
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "catalog_number": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        },
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "mainframe_description": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        }
                    }
                },
                "win_item_name": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "edge_ngram_search_analyzer"
                        }
                    }
                }
            }
        }
    }


def create_index(client, index_name=OPENSEARCH_INDEX_NAME, recreate=False):
    """
    Create the OpenSearch index with proper mappings.
    
    Args:
        client (OpenSearch): OpenSearch client instance
        index_name (str): Name of the index to create
        recreate (bool): If True, delete existing index before creating
        
    Returns:
        bool: True if index was created successfully
    """
    try:
        # Check if index exists
        if client.indices.exists(index=index_name):
            if recreate:
                logger.info(f"Deleting existing index: {index_name}")
                client.indices.delete(index=index_name)
            else:
                logger.info(f"Index '{index_name}' already exists")
                return True
        
        # Create index with mappings
        mapping = get_index_mapping()
        response = client.indices.create(index=index_name, body=mapping)
        logger.info(f"Index '{index_name}' created successfully")
        return True
        
    except RequestError as e:
        logger.error(f"Error creating index: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating index: {e}")
        raise


def verify_index(client, index_name=OPENSEARCH_INDEX_NAME):
    """
    Verify that the index exists and has the correct mappings.
    
    Args:
        client (OpenSearch): OpenSearch client instance
        index_name (str): Name of the index to verify
        
    Returns:
        dict: Index information including mappings and settings
    """
    try:
        if not client.indices.exists(index=index_name):
            logger.error(f"Index '{index_name}' does not exist")
            return None
        
        # Get index mappings
        mappings = client.indices.get_mapping(index=index_name)
        settings = client.indices.get_settings(index=index_name)
        
        # Get document count
        count = client.count(index=index_name)
        
        logger.info(f"Index '{index_name}' verified successfully")
        logger.info(f"Document count: {count['count']}")
        
        return {
            "mappings": mappings,
            "settings": settings,
            "document_count": count['count']
        }
        
    except Exception as e:
        logger.error(f"Error verifying index: {e}")
        raise

