"""
Test script to verify Phase 2 setup is complete and working.

This script tests:
1. Ollama connection and model availability
2. OpenSearch connection
3. PostgreSQL connection
4. Embedding generation
5. Vector index creation
6. Progress tracking

Usage:
    python test_phase2_setup.py
"""

import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ollama_connection():
    """Test Ollama connection and model availability."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Ollama Connection")
    logger.info("=" * 80)
    
    try:
        from app.services.embedding_service import OllamaEmbeddingService
        
        service = OllamaEmbeddingService()
        
        # Test connection
        if not service.test_connection():
            logger.error("❌ Ollama connection failed")
            return False
        
        # Test embedding generation
        test_text = "Test product for embedding"
        embedding = service.generate_embedding(test_text)
        
        if not embedding:
            logger.error("❌ Failed to generate test embedding")
            return False
        
        logger.info(f"✅ Ollama connection successful")
        logger.info(f"✅ Generated test embedding: dimension={len(embedding)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ollama test failed: {e}")
        return False


def test_opensearch_connection():
    """Test OpenSearch connection."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: OpenSearch Connection")
    logger.info("=" * 80)
    
    try:
        from app.db.opensearch import get_opensearch_client
        
        client = get_opensearch_client()
        info = client.info()
        
        logger.info(f"✅ Connected to OpenSearch cluster: {info['cluster_name']}")
        logger.info(f"✅ Version: {info['version']['number']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ OpenSearch connection failed: {e}")
        return False


def test_postgres_connection():
    """Test PostgreSQL connection."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: PostgreSQL Connection")
    logger.info("=" * 80)
    
    try:
        from app.db.postgres import get_postgres_connection
        
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT COUNT(*) FROM public.inventory")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Connected to PostgreSQL")
        logger.info(f"✅ Total records in inventory table: {count:,}")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False


def test_vector_index_creation():
    """Test vector index creation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Vector Index Creation")
    logger.info("=" * 80)
    
    try:
        from app.db.opensearch import get_opensearch_client
        from app.db.opensearch_vector import create_vector_index, verify_vector_index
        from app.config.settings import OPENSEARCH_VECTOR_INDEX_NAME
        
        client = get_opensearch_client()
        
        # Create test index
        test_index = "test_vector_index_phase2"
        create_vector_index(client, test_index, embedding_dim=768, recreate=True)
        
        # Verify index
        info = verify_vector_index(client, test_index)
        
        if not info:
            logger.error("❌ Failed to verify vector index")
            return False
        
        logger.info(f"✅ Vector index created: {test_index}")
        logger.info(f"✅ Index verified successfully")
        
        # Clean up
        client.indices.delete(index=test_index)
        logger.info(f"✅ Test index cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector index test failed: {e}")
        return False


def test_progress_tracker():
    """Test progress tracker."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Progress Tracker")
    logger.info("=" * 80)
    
    try:
        from app.services.progress_tracker import ProgressTracker
        import os
        
        # Use test database
        test_db = "./test_progress_phase2.db"
        
        tracker = ProgressTracker(db_path=test_db)
        
        # Test marking records
        tracker.mark_processed(1, "completed", 768, 150)
        tracker.mark_processed(2, "completed", 768, 200)
        
        # Test checking
        assert tracker.is_processed(1) == True
        assert tracker.is_processed(999) == False
        
        # Test stats
        stats = tracker.get_progress_stats()
        
        tracker.close()
        
        logger.info(f"✅ Progress tracker working")
        logger.info(f"✅ Stats: {stats}")
        
        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)
            logger.info(f"✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Progress tracker test failed: {e}")
        return False


def test_end_to_end_sample():
    """Test end-to-end with a small sample."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: End-to-End Sample Processing")
    logger.info("=" * 80)
    
    try:
        from app.db.postgres import get_postgres_connection
        from app.services.embedding_service import OllamaEmbeddingService
        from app.db.opensearch import get_opensearch_client
        from app.db.opensearch_vector import create_vector_index, bulk_index_vectors
        
        # Fetch sample records
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, preferred_supplier, brand_name, wise_item_number, 
                   catalog_number, mainframe_description, win_item_name
            FROM public.inventory
            ORDER BY id
            LIMIT 3
        """)
        
        columns = [desc[0] for desc in cursor.description]
        records = []
        for row in cursor.fetchall():
            records.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Fetched {len(records)} sample records")
        
        # Generate embeddings
        service = OllamaEmbeddingService()
        enriched = service.generate_batch_embeddings(records, show_progress=False)
        
        logger.info(f"✅ Generated embeddings for {len(enriched)} records")
        
        # Create test index and index documents
        client = get_opensearch_client()
        test_index = "test_e2e_phase2"
        create_vector_index(client, test_index, embedding_dim=768, recreate=True)
        
        result = bulk_index_vectors(client, enriched, test_index)
        
        logger.info(f"✅ Indexed {result['success_count']} documents")
        
        # Verify
        import time
        time.sleep(2)  # Wait for indexing
        
        count = client.count(index=test_index)['count']
        logger.info(f"✅ Verified {count} documents in index")
        
        # Clean up
        client.indices.delete(index=test_index)
        logger.info(f"✅ Test index cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2 SETUP VERIFICATION")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("OpenSearch Connection", test_opensearch_connection),
        ("PostgreSQL Connection", test_postgres_connection),
        ("Vector Index Creation", test_vector_index_creation),
        ("Progress Tracker", test_progress_tracker),
        ("End-to-End Sample", test_end_to_end_sample),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Phase 2 setup is complete and ready.")
        logger.info("\nYou can now run the embedding ETL pipeline:")
        logger.info("    python embedding_etl_pipeline.py")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues before running the pipeline.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

