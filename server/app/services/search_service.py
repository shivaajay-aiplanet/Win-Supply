"""
Search service for BM25 keyword-based product search.
Implements keyword search across all indexed text fields.
Also includes hybrid search combining BM25 and vector search with reranking.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from app.db.opensearch import get_opensearch_client
from app.db.opensearch_vector import search_by_vector
from app.config.settings import (
    OPENSEARCH_INDEX_NAME,
    OPENSEARCH_VECTOR_INDEX_NAME,
    FIELDS_TO_INDEX,
    POSTGRES_CONNECTION_STRING,
    POSTGRES_TABLE_NAME
)
from app.services.embedding_service import OllamaEmbeddingService
from app.services.reranker_service import RerankerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_search_query(query_string, use_edge_ngram=True):
    """
    Build a multi-match search query for BM25 scoring.
    
    Args:
        query_string (str): User's search query
        use_edge_ngram (bool): If True, also search edge n-gram fields for partial matching
        
    Returns:
        dict: OpenSearch query DSL
    """
    # Base fields for standard search
    base_fields = FIELDS_TO_INDEX.copy()
    
    # Add edge n-gram fields for partial matching
    search_fields = base_fields.copy()
    if use_edge_ngram:
        edge_ngram_fields = [f"{field}.edge_ngram" for field in FIELDS_TO_INDEX]
        search_fields.extend(edge_ngram_fields)
    
    # Build multi-match query with BM25 scoring
    query = {
        "query": {
            "multi_match": {
                "query": query_string,
                "fields": search_fields,
                "type": "best_fields",  # Use best_fields for BM25 scoring
                "operator": "or",
                "fuzziness": "AUTO",  # Enable fuzzy matching for typos
                "prefix_length": 2,
                "max_expansions": 50
            }
        },
        "size": 10,  # Return top 10 results
        "track_scores": True,
        "_source": FIELDS_TO_INDEX + ["id"]  # Return only indexed fields
    }
    
    return query


def search_products(query_string, client=None, index_name=OPENSEARCH_INDEX_NAME, top_k=10):
    """
    Search for products using BM25 keyword search.
    
    Args:
        query_string (str): User's search query
        client (OpenSearch): OpenSearch client (creates new if None)
        index_name (str): Name of the index to search
        top_k (int): Number of top results to return
        
    Returns:
        dict: Search results with documents and metadata
    """
    if not query_string or not query_string.strip():
        return {
            "query": query_string,
            "total_hits": 0,
            "results": [],
            "error": "Empty query string"
        }
    
    # Get client if not provided
    if client is None:
        client = get_opensearch_client()
    
    try:
        # Build search query
        search_query = build_search_query(query_string)
        search_query["size"] = top_k
        
        logger.info(f"Searching for: '{query_string}'")
        
        # Execute search
        response = client.search(
            index=index_name,
            body=search_query
        )
        
        # Parse results
        hits = response["hits"]["hits"]
        total_hits = response["hits"]["total"]["value"]
        
        results = []
        for hit in hits:
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                "document": hit["_source"]
            }
            results.append(result)
        
        logger.info(f"Found {total_hits} total matches, returning top {len(results)}")
        
        return {
            "query": query_string,
            "total_hits": total_hits,
            "returned_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "query": query_string,
            "total_hits": 0,
            "results": [],
            "error": str(e)
        }


def search_by_field(query_string, field_name, client=None, index_name=OPENSEARCH_INDEX_NAME, top_k=10):
    """
    Search for products in a specific field.
    
    Args:
        query_string (str): User's search query
        field_name (str): Specific field to search in
        client (OpenSearch): OpenSearch client (creates new if None)
        index_name (str): Name of the index to search
        top_k (int): Number of top results to return
        
    Returns:
        dict: Search results with documents and metadata
    """
    if field_name not in FIELDS_TO_INDEX:
        return {
            "query": query_string,
            "field": field_name,
            "total_hits": 0,
            "results": [],
            "error": f"Invalid field name. Must be one of: {FIELDS_TO_INDEX}"
        }
    
    # Get client if not provided
    if client is None:
        client = get_opensearch_client()
    
    try:
        # Build field-specific query
        query = {
            "query": {
                "match": {
                    field_name: {
                        "query": query_string,
                        "fuzziness": "AUTO"
                    }
                }
            },
            "size": top_k,
            "track_scores": True,
            "_source": FIELDS_TO_INDEX
        }
        
        logger.info(f"Searching in field '{field_name}' for: '{query_string}'")
        
        # Execute search
        response = client.search(
            index=index_name,
            body=query
        )
        
        # Parse results
        hits = response["hits"]["hits"]
        total_hits = response["hits"]["total"]["value"]
        
        results = []
        for hit in hits:
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                "document": hit["_source"]
            }
            results.append(result)
        
        logger.info(f"Found {total_hits} total matches in '{field_name}', returning top {len(results)}")
        
        return {
            "query": query_string,
            "field": field_name,
            "total_hits": total_hits,
            "returned_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "query": query_string,
            "field": field_name,
            "total_hits": 0,
            "results": [],
            "error": str(e)
        }


def get_document_by_id(doc_id, client=None, index_name=OPENSEARCH_INDEX_NAME):
    """
    Retrieve a specific document by its ID.

    Args:
        doc_id: Document ID
        client (OpenSearch): OpenSearch client (creates new if None)
        index_name (str): Name of the index

    Returns:
        dict: Document data or error
    """
    # Get client if not provided
    if client is None:
        client = get_opensearch_client()

    try:
        response = client.get(index=index_name, id=doc_id)

        return {
            "id": response["_id"],
            "found": True,
            "document": response["_source"]
        }

    except Exception as e:
        logger.error(f"Error retrieving document {doc_id}: {e}")
        return {
            "id": doc_id,
            "found": False,
            "error": str(e)
        }


def get_product_by_wise_item_number(wise_item_number: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve product details from PostgreSQL by WISE item number.

    Args:
        wise_item_number: WISE item number to search for

    Returns:
        dict: Product data or None if not found
    """
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = f"""
            SELECT *
            FROM public.{POSTGRES_TABLE_NAME}
            WHERE wise_item_number = %s
            LIMIT 1
        """

        cursor.execute(query, (wise_item_number,))
        result = cursor.fetchone()

        if result:
            logger.info(f"Found product for WISE item number: {wise_item_number}")
            return dict(result)
        else:
            logger.warning(f"No product found for WISE item number: {wise_item_number}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving product from PostgreSQL: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def hybrid_search_by_wise_item(
    wise_item_number: str,
    top_k: int = 20,
    keyword_weight: float = 0.5,
    vector_weight: float = 0.5,
    client=None
) -> Dict[str, Any]:
    """
    Hybrid search pipeline for product discovery by WISE item number.

    Pipeline:
    1. Query PostgreSQL to get product details by WISE item number
    2. Generate embedding from product name + description
    3. Execute BM25 keyword search in OpenSearch
    4. Execute vector search in OpenSearch
    5. Combine and deduplicate results
    6. Rerank using BAAI/bge-reranker-v2-m3
    7. Return top 20 reranked results

    Args:
        wise_item_number: WISE item number to search for
        top_k: Number of top results to return after reranking (default 20)
        keyword_weight: Weight for BM25 scores (not used in reranking, but logged)
        vector_weight: Weight for vector scores (not used in reranking, but logged)
        client: OpenSearch client (creates new if None)

    Returns:
        dict: Search results with reranked documents and metadata
    """
    try:
        # Step 1: Get product from PostgreSQL
        logger.info(f"Step 1: Retrieving product for WISE item number: {wise_item_number}")
        product = get_product_by_wise_item_number(wise_item_number)

        if not product:
            return {
                "wise_item_number": wise_item_number,
                "product_found": False,
                "total_results": 0,
                "results": [],
                "error": f"Product not found for WISE item number: {wise_item_number}"
            }

        # Step 2: Prepare query text from product name and description
        query_parts = []
        if product.get('win_item_name'):
            query_parts.append(str(product['win_item_name']))
        if product.get('mainframe_description'):
            query_parts.append(str(product['mainframe_description']))
        if product.get('brand_name'):
            query_parts.append(str(product['brand_name']))

        query_text = " ".join(query_parts)
        logger.info(f"Step 2: Query text: '{query_text[:100]}...'")

        # Get OpenSearch client
        if client is None:
            client = get_opensearch_client()

        # Step 3: Execute BM25 keyword search
        logger.info(f"Step 3: Executing BM25 keyword search (fetching top {top_k * 2})")
        keyword_results = search_products(
            query_string=query_text,
            client=client,
            index_name=OPENSEARCH_INDEX_NAME,
            top_k=top_k * 2  # Fetch more for better reranking pool
        )

        keyword_docs = keyword_results.get('results', [])
        logger.info(f"BM25 search returned {len(keyword_docs)} results")

        # Step 4: Generate embedding and execute vector search
        logger.info("Step 4: Generating embedding and executing vector search")
        embedding_service = OllamaEmbeddingService()
        query_embedding = embedding_service.generate_embedding(query_text)

        if not query_embedding:
            logger.error("Failed to generate embedding")
            # Fall back to keyword-only results
            return {
                "wise_item_number": wise_item_number,
                "product_found": True,
                "query_text": query_text,
                "total_results": len(keyword_docs),
                "results": keyword_docs[:top_k],
                "warning": "Vector search skipped due to embedding generation failure"
            }

        vector_results = search_by_vector(
            client=client,
            query_embedding=query_embedding,
            index_name=OPENSEARCH_VECTOR_INDEX_NAME,
            top_k=top_k * 2
        )

        vector_docs = vector_results.get('results', [])
        logger.info(f"Vector search returned {len(vector_docs)} results")

        # Step 5: Combine and deduplicate results
        logger.info("Step 5: Combining and deduplicating results")
        combined_docs = {}

        # Add keyword results
        for result in keyword_docs:
            doc_id = result['id']
            combined_docs[doc_id] = {
                'document': result['document'],
                'keyword_score': result['score'],
                'vector_score': 0.0
            }

        # Add/merge vector results
        for result in vector_docs:
            doc_id = result['id']
            if doc_id in combined_docs:
                combined_docs[doc_id]['vector_score'] = result['score']
            else:
                combined_docs[doc_id] = {
                    'document': result['document'],
                    'keyword_score': 0.0,
                    'vector_score': result['score']
                }

        # Prepare documents for reranking
        docs_for_reranking = []
        for doc_id, data in combined_docs.items():
            doc = data['document'].copy()
            doc['id'] = doc_id
            doc['original_keyword_score'] = data['keyword_score']
            doc['original_vector_score'] = data['vector_score']
            docs_for_reranking.append(doc)

        logger.info(f"Combined to {len(docs_for_reranking)} unique documents")

        # Step 6: Rerank using HuggingFace reranker
        logger.info("Step 6: Reranking with BAAI/bge-reranker-v2-m3")
        reranker_service = RerankerService()

        # Check if documents have text_combined field, if not we'll use combined fields
        if docs_for_reranking and 'text_combined' not in docs_for_reranking[0]:
            # Add text_combined field from available fields
            for doc in docs_for_reranking:
                text_parts = []
                for field in FIELDS_TO_INDEX:
                    if field in doc and doc[field]:
                        text_parts.append(str(doc[field]))
                doc['text_combined'] = " ".join(text_parts)

        reranked_results = reranker_service.rerank(
            query=query_text,
            documents=docs_for_reranking,
            top_k=top_k,
            text_field='text_combined'
        )

        # Step 7: Format final results
        logger.info("Step 7: Formatting final results")
        final_results = []
        for idx, (doc, rerank_score) in enumerate(reranked_results, 1):
            result = {
                "rank": idx,
                "id": doc.get('id'),
                "relevance_score": float(rerank_score),
                "keyword_score": doc.get('original_keyword_score', 0.0),
                "vector_score": doc.get('original_vector_score', 0.0),
                "document": {
                    k: v for k, v in doc.items()
                    if k not in ['original_keyword_score', 'original_vector_score', 'text_combined']
                }
            }
            final_results.append(result)

        logger.info(f"✅ Hybrid search complete. Returning {len(final_results)} reranked results")

        return {
            "wise_item_number": wise_item_number,
            "product_found": True,
            "query_text": query_text,
            "source_product": {
                "id": product.get('id'),
                "wise_item_number": product.get('wise_item_number'),
                "win_item_name": product.get('win_item_name'),
                "brand_name": product.get('brand_name')
            },
            "search_stats": {
                "keyword_results": len(keyword_docs),
                "vector_results": len(vector_docs),
                "combined_unique": len(docs_for_reranking),
                "reranked_returned": len(final_results)
            },
            "total_results": len(final_results),
            "results": final_results
        }

    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        return {
            "wise_item_number": wise_item_number,
            "product_found": False,
            "total_results": 0,
            "results": [],
            "error": str(e)
        }

