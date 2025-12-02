"""
ETL service orchestrator.
Coordinates the extraction, transformation, and loading of product data.
"""
import logging
from datetime import datetime
from app.db.opensearch import get_opensearch_client, create_index, verify_index
from app.db.postgres import extract_product_data, get_table_info
from app.services.transformer_service import transform_batch
from app.services.indexer_service import index_all_documents, refresh_index
from app.config.settings import OPENSEARCH_INDEX_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_etl_pipeline(recreate_index=False, batch_size=1000):
    """
    Run the complete ETL pipeline.
    
    Args:
        recreate_index (bool): If True, delete and recreate the index
        batch_size (int): Number of records to process per batch
        
    Returns:
        dict: Pipeline execution results and statistics
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Starting ETL Pipeline")
    logger.info("=" * 80)
    
    results = {
        "status": "started",
        "start_time": start_time.isoformat(),
        "stages": {}
    }
    
    try:
        # Stage 1: Setup OpenSearch
        logger.info("\n[Stage 1/4] Setting up OpenSearch index...")
        stage_start = datetime.now()
        
        os_client = get_opensearch_client()
        create_index(os_client, OPENSEARCH_INDEX_NAME, recreate=recreate_index)
        
        results["stages"]["opensearch_setup"] = {
            "status": "completed",
            "duration_seconds": (datetime.now() - stage_start).total_seconds()
        }
        logger.info(f"✓ OpenSearch setup completed in {results['stages']['opensearch_setup']['duration_seconds']:.2f}s")
        
        # Stage 2: Get source data info
        logger.info("\n[Stage 2/4] Analyzing source data...")
        stage_start = datetime.now()
        
        table_info = get_table_info()
        logger.info(f"Source table has {table_info['row_count']} rows")
        
        results["stages"]["data_analysis"] = {
            "status": "completed",
            "source_row_count": table_info['row_count'],
            "duration_seconds": (datetime.now() - stage_start).total_seconds()
        }
        logger.info(f"✓ Data analysis completed in {results['stages']['data_analysis']['duration_seconds']:.2f}s")
        
        # Stage 3: Extract, Transform, and Load
        logger.info("\n[Stage 3/4] Extracting, transforming, and loading data...")
        stage_start = datetime.now()
        
        def transform_and_yield():
            """Generator that extracts, transforms, and yields batches."""
            for raw_batch in extract_product_data(batch_size=batch_size):
                transformed_batch = transform_batch(raw_batch)
                if transformed_batch:
                    yield transformed_batch
        
        # Index all documents
        indexing_results = index_all_documents(
            os_client,
            transform_and_yield(),
            OPENSEARCH_INDEX_NAME
        )
        
        results["stages"]["etl"] = {
            "status": "completed",
            "batches_processed": indexing_results["total_batches"],
            "documents_indexed": indexing_results["total_success"],
            "documents_failed": indexing_results["total_failed"],
            "duration_seconds": (datetime.now() - stage_start).total_seconds()
        }
        logger.info(f"✓ ETL completed in {results['stages']['etl']['duration_seconds']:.2f}s")
        
        # Stage 4: Refresh and verify
        logger.info("\n[Stage 4/4] Refreshing index and verifying...")
        stage_start = datetime.now()
        
        refresh_index(os_client, OPENSEARCH_INDEX_NAME)
        index_info = verify_index(os_client, OPENSEARCH_INDEX_NAME)
        
        results["stages"]["verification"] = {
            "status": "completed",
            "final_document_count": index_info["document_count"],
            "duration_seconds": (datetime.now() - stage_start).total_seconds()
        }
        logger.info(f"✓ Verification completed in {results['stages']['verification']['duration_seconds']:.2f}s")
        
        # Final summary
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        results["status"] = "completed"
        results["end_time"] = end_time.isoformat()
        results["total_duration_seconds"] = total_duration
        
        logger.info("\n" + "=" * 80)
        logger.info("ETL Pipeline Completed Successfully!")
        logger.info("=" * 80)
        logger.info(f"Total duration: {total_duration:.2f}s")
        logger.info(f"Source rows: {table_info['row_count']}")
        logger.info(f"Documents indexed: {indexing_results['total_success']}")
        logger.info(f"Documents failed: {indexing_results['total_failed']}")
        logger.info(f"Final document count: {index_info['document_count']}")
        logger.info("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"\n✗ ETL Pipeline failed: {e}", exc_info=True)
        results["status"] = "failed"
        results["error"] = str(e)
        results["end_time"] = datetime.now().isoformat()
        results["total_duration_seconds"] = (datetime.now() - start_time).total_seconds()
        raise


if __name__ == "__main__":
    """Run the ETL pipeline when executed directly."""
    import sys
    
    recreate = "--recreate" in sys.argv
    
    if recreate:
        logger.warning("⚠️  Index will be recreated (all existing data will be deleted)")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Pipeline execution cancelled")
            sys.exit(0)
    
    try:
        results = run_etl_pipeline(recreate_index=recreate)
        logger.info("\nPipeline execution completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nPipeline execution failed: {e}")
        sys.exit(1)

