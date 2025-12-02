"""
Phase 2: Vector Embedding ETL Pipeline

This script:
1. Extracts product data from PostgreSQL
2. Generates embeddings using Ollama (NomicEmbedTextV1.5)
3. Indexes documents with embeddings into OpenSearch
4. Maintains crash-safe progress tracking
5. Supports resume functionality

Usage:
    python embedding_etl_pipeline.py [--recreate] [--batch-size 100] [--reset-progress]
"""

import argparse
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm

from app.db.opensearch import get_opensearch_client
from app.db.opensearch_vector import (
    create_vector_index,
    verify_vector_index,
    bulk_index_vectors,
)
from app.db.postgres import get_postgres_connection
from app.services.embedding_service import OllamaEmbeddingService
from app.services.progress_tracker import ProgressTracker
from app.config.settings import (
    OPENSEARCH_VECTOR_INDEX_NAME,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    POSTGRES_TABLE_NAME,
    FIELDS_TO_INDEX,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("embedding_etl.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class EmbeddingETLPipeline:
    """Main ETL pipeline for generating and indexing embeddings."""

    def __init__(
        self,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        recreate_index: bool = False,
        reset_progress: bool = False,
    ):
        """
        Initialize the embedding ETL pipeline.

        Args:
            batch_size: Number of records to process per batch
            recreate_index: Whether to recreate the OpenSearch index
            reset_progress: Whether to reset progress tracking
        """
        self.batch_size = batch_size
        self.recreate_index = recreate_index
        self.reset_progress = reset_progress

        # Initialize services
        self.os_client = None
        self.pg_conn = None
        self.embedding_service = None
        self.progress_tracker = None

        # Statistics
        self.stats = {
            "total_records": 0,
            "processed_records": 0,
            "skipped_records": 0,
            "failed_records": 0,
            "start_time": None,
            "end_time": None,
        }

    def setup(self):
        """Setup all required connections and services."""
        logger.info("=" * 80)
        logger.info("PHASE 2: VECTOR EMBEDDING ETL PIPELINE")
        logger.info("=" * 80)

        # Setup OpenSearch
        logger.info("\n[1/5] Setting up OpenSearch connection...")
        self.os_client = get_opensearch_client()

        # Create vector index
        logger.info(f"\n[2/5] Creating vector index: {OPENSEARCH_VECTOR_INDEX_NAME}")
        create_vector_index(
            self.os_client,
            OPENSEARCH_VECTOR_INDEX_NAME,
            EMBEDDING_DIMENSION,
            recreate=self.recreate_index,
        )

        # Verify index
        index_info = verify_vector_index(self.os_client, OPENSEARCH_VECTOR_INDEX_NAME)
        if index_info:
            logger.info(
                f"Vector index verified: {index_info['document_count']} existing documents"
            )

        # Setup PostgreSQL
        logger.info("\n[3/5] Setting up PostgreSQL connection...")
        self.pg_conn = get_postgres_connection()

        # Get total record count
        cursor = self.pg_conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM public.{POSTGRES_TABLE_NAME}")
        self.stats["total_records"] = cursor.fetchone()[0]
        logger.info(f"Total records in PostgreSQL: {self.stats['total_records']:,}")
        cursor.close()

        # Setup Ollama embedding service
        logger.info("\n[4/5] Setting up Ollama embedding service...")
        self.embedding_service = OllamaEmbeddingService()

        if not self.embedding_service.test_connection():
            raise Exception("Failed to connect to Ollama service")

        # Setup progress tracker
        logger.info("\n[5/5] Setting up progress tracker...")
        self.progress_tracker = ProgressTracker()

        if self.reset_progress:
            logger.warning("Resetting progress tracker...")
            self.progress_tracker.reset_progress()

        # Get existing progress
        progress_stats = self.progress_tracker.get_progress_stats()
        logger.info(f"Progress stats: {progress_stats}")

        if progress_stats.get("completed", 0) > 0:
            logger.info(
                f"Resuming from last checkpoint: {progress_stats['last_processed_id']}"
            )
            self.stats["processed_records"] = progress_stats["completed"]

        logger.info("\n✅ Setup complete!\n")

    def fetch_unprocessed_batch(self, last_id: int, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch a batch of unprocessed records from PostgreSQL.

        Args:
            last_id: Last processed ID (fetch records with id > last_id)
            limit: Number of records to fetch

        Returns:
            List of records
        """
        cursor = self.pg_conn.cursor()

        # Build query - fetch records with ID greater than last processed ID
        fields = ["id"] + FIELDS_TO_INDEX
        fields_str = ", ".join(fields)

        query = f"""
            SELECT {fields_str}
            FROM public.{POSTGRES_TABLE_NAME}
            WHERE id > %s
            ORDER BY id
            LIMIT %s
        """

        cursor.execute(query, (last_id, limit))

        # Convert to list of dicts
        columns = [desc[0] for desc in cursor.description]
        records = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            records.append(record)

        cursor.close()
        return records

    def process_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Process a batch of records: generate embeddings and index.

        Args:
            records: List of product records

        Returns:
            Number of successfully processed records
        """
        if not records:
            return 0

        try:
            # Generate embeddings
            enriched_records = self.embedding_service.generate_batch_embeddings(
                records, show_progress=False
            )

            if not enriched_records:
                logger.warning("No records enriched in this batch")
                return 0

            # Index into OpenSearch
            result = bulk_index_vectors(
                self.os_client, enriched_records, OPENSEARCH_VECTOR_INDEX_NAME
            )

            # Mark as processed
            self.progress_tracker.mark_batch_processed(enriched_records, "completed")

            # Update stats
            success_count = result["success_count"]
            failed_count = result["failed_count"]

            self.stats["processed_records"] += success_count
            self.stats["failed_records"] += failed_count

            return success_count

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.stats["failed_records"] += len(records)
            return 0

    def run(self):
        """Run the complete ETL pipeline."""
        self.stats["start_time"] = datetime.now()

        logger.info("=" * 80)
        logger.info("STARTING ETL PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Total records: {self.stats['total_records']:,}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Already processed: {self.stats['processed_records']:,}")
        logger.info("")

        # Get last processed ID to resume from
        last_processed_id = self.progress_tracker.get_last_processed_id() or 0
        logger.info(f"Starting from ID: {last_processed_id + 1}")

        # Calculate remaining batches
        remaining_records = (
            self.stats["total_records"] - self.stats["processed_records"]
        )
        total_batches = (remaining_records + self.batch_size - 1) // self.batch_size

        # Progress bar
        with tqdm(
            total=self.stats["total_records"], initial=self.stats["processed_records"]
        ) as pbar:
            batch_num = 0
            current_id = last_processed_id

            while self.stats["processed_records"] < self.stats["total_records"]:
                batch_num += 1

                # Fetch batch starting from current_id
                records = self.fetch_unprocessed_batch(current_id, self.batch_size)

                if not records:
                    # No more records to process
                    logger.info("No more unprocessed records found")
                    break

                # Process batch
                success_count = self.process_batch(records)
                pbar.update(success_count)

                # Update current_id to the last processed record's ID
                if records:
                    current_id = max(r["id"] for r in records)

                # Log progress
                if batch_num % 10 == 0:
                    self._log_progress(batch_num, total_batches)

                # Small delay to avoid overwhelming services
                time.sleep(0.1)

        self.stats["end_time"] = datetime.now()
        self._log_final_summary()

    def _log_progress(self, current_batch: int, total_batches: int):
        """Log progress update."""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        rate = self.stats["processed_records"] / elapsed if elapsed > 0 else 0

        logger.info(f"\n--- Progress Update ---")
        logger.info(f"Batch: {current_batch}/{total_batches}")
        logger.info(
            f"Processed: {self.stats['processed_records']:,}/{self.stats['total_records']:,}"
        )
        logger.info(f"Rate: {rate:.1f} records/sec")
        logger.info(f"Elapsed: {elapsed/60:.1f} minutes")

    def _log_final_summary(self):
        """Log final summary."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("ETL PIPELINE COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Total records: {self.stats['total_records']:,}")
        logger.info(f"Successfully processed: {self.stats['processed_records']:,}")
        logger.info(f"Skipped (already done): {self.stats['skipped_records']:,}")
        logger.info(f"Failed: {self.stats['failed_records']:,}")
        logger.info(f"Duration: {duration/60:.1f} minutes")
        logger.info(
            f"Average rate: {self.stats['processed_records']/duration:.1f} records/sec"
        )
        logger.info("=" * 80)

        # Verify final index
        index_info = verify_vector_index(self.os_client, OPENSEARCH_VECTOR_INDEX_NAME)
        if index_info:
            logger.info(
                f"\nFinal index document count: {index_info['document_count']:,}"
            )

    def cleanup(self):
        """Cleanup connections."""
        if self.pg_conn:
            self.pg_conn.close()
        if self.progress_tracker:
            self.progress_tracker.close()
        logger.info("Cleanup complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Vector Embedding ETL Pipeline")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the OpenSearch index (deletes existing data)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=EMBEDDING_BATCH_SIZE,
        help=f"Batch size for processing (default: {EMBEDDING_BATCH_SIZE})",
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset progress tracker (start from beginning)",
    )

    args = parser.parse_args()

    pipeline = EmbeddingETLPipeline(
        batch_size=args.batch_size,
        recreate_index=args.recreate,
        reset_progress=args.reset_progress,
    )

    try:
        pipeline.setup()
        pipeline.run()
    except KeyboardInterrupt:
        logger.warning("\n\nPipeline interrupted by user. Progress has been saved.")
    except Exception as e:
        logger.error(f"\n\nPipeline failed with error: {e}", exc_info=True)
    finally:
        pipeline.cleanup()


if __name__ == "__main__":
    main()
