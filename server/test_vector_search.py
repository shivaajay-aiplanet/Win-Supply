"""
Test script to verify vector search functionality.
Searches for a specific product using semantic vector similarity.
"""

import sys
import logging
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, ".")

from app.services.embedding_service import OllamaEmbeddingService
from app.db.opensearch_vector import search_by_vector
from app.db.opensearch import get_opensearch_client
from app.config.settings import OPENSEARCH_VECTOR_INDEX_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_separator(char="=", length=100):
    """Print a separator line."""
    print(char * length)


def print_result(rank: int, result: Dict[str, Any]):
    """
    Print a single search result in a formatted way.
    
    Args:
        rank: Result ranking (1-based)
        result: Result dictionary containing score and document
    """
    doc = result["document"]
    score = result["score"]
    
    print(f"\n{rank}. SIMILARITY SCORE: {score:.4f}")
    print(f"   Product ID: {doc.get('id', 'N/A')}")
    print(f"   Product Name: {doc.get('win_item_name', 'N/A')}")
    print(f"   Brand: {doc.get('brand_name', 'N/A')}")
    print(f"   Supplier: {doc.get('preferred_supplier', 'N/A')}")
    print(f"   Item Number: {doc.get('wise_item_number', 'N/A')}")
    print(f"   Category: {doc.get('category', 'N/A')}")
    print(f"   Usage: {doc.get('usage', 'N/A')}")


def test_vector_search(query_text: str, top_k: int = 10):
    """
    Test vector search functionality by searching for a specific product.
    
    Args:
        query_text: Search query text
        top_k: Number of results to return
    """
    try:
        print_separator()
        print("VECTOR SEARCH TEST")
        print_separator()
        print(f"\nSearch Query: \"{query_text}\"")
        print(f"Top K Results: {top_k}")
        print(f"Index: {OPENSEARCH_VECTOR_INDEX_NAME}")
        
        # Step 1: Initialize embedding service
        print("\n[1/4] Initializing Ollama embedding service...")
        embedding_service = OllamaEmbeddingService()
        
        # Test connection
        if not embedding_service.test_connection():
            logger.error("Failed to connect to Ollama service")
            return False
        
        print("✅ Ollama service connected")
        
        # Step 2: Generate query embedding
        print("\n[2/4] Generating embedding for search query...")
        query_embedding = embedding_service.generate_embedding(query_text)
        
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return False
        
        print(f"✅ Query embedding generated (dimension: {len(query_embedding)})")
        
        # Step 3: Connect to OpenSearch
        print("\n[3/4] Connecting to OpenSearch...")
        opensearch_client = get_opensearch_client()
        
        # Verify index exists and get document count
        if not opensearch_client.indices.exists(index=OPENSEARCH_VECTOR_INDEX_NAME):
            logger.error(f"Index '{OPENSEARCH_VECTOR_INDEX_NAME}' does not exist")
            return False
        
        doc_count = opensearch_client.count(index=OPENSEARCH_VECTOR_INDEX_NAME)["count"]
        print(f"✅ Connected to OpenSearch (Index: {OPENSEARCH_VECTOR_INDEX_NAME}, Documents: {doc_count:,})")
        
        # Step 4: Perform vector search
        print("\n[4/4] Performing vector similarity search...")
        search_results = search_by_vector(
            client=opensearch_client,
            query_embedding=query_embedding,
            index_name=OPENSEARCH_VECTOR_INDEX_NAME,
            top_k=top_k
        )
        
        print(f"✅ Search complete (Found: {search_results['total_hits']} total matches)")
        
        # Display results
        print_separator()
        print(f"TOP {top_k} MOST SIMILAR PRODUCTS")
        print_separator()
        
        if not search_results["results"]:
            print("\n⚠️  No results found")
            return True
        
        for idx, result in enumerate(search_results["results"], 1):
            print_result(idx, result)
        
        print_separator()
        print("\n✅ Vector search test completed successfully!")
        print_separator()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during vector search test: {e}", exc_info=True)
        return False


def main():
    """Main function to run the vector search test."""
    # Default search query
    default_query = "1/100 HP 110 V Evaporator Fan Motor Kit"
    
    # Allow custom query from command line
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = default_query
    
    # Run the test
    success = test_vector_search(query, top_k=10)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

