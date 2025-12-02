"""
Progress tracker for embedding ETL pipeline.
Uses SQLite to maintain crash-safe progress tracking.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.config.settings import PROGRESS_DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks embedding progress using SQLite database."""
    
    def __init__(self, db_path: str = PROGRESS_DB_PATH):
        """
        Initialize the progress tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
        
    def _initialize_db(self):
        """Create the progress tracking table if it doesn't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embedding_progress (
                    id INTEGER PRIMARY KEY,
                    product_id INTEGER UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    embedding_dimension INTEGER,
                    text_length INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on product_id for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_id 
                ON embedding_progress(product_id)
            """)
            
            # Create index on status for filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON embedding_progress(status)
            """)
            
            # Create metadata table for tracking overall progress
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embedding_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            logger.info(f"Progress tracker initialized at: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize progress database: {e}")
            raise
    
    def mark_processed(
        self, 
        product_id: int, 
        status: str = "completed",
        embedding_dimension: Optional[int] = None,
        text_length: Optional[int] = None
    ):
        """
        Mark a product as processed.
        
        Args:
            product_id: ID of the product
            status: Status (completed, failed, skipped)
            embedding_dimension: Dimension of the embedding vector
            text_length: Length of the combined text
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO embedding_progress 
                (product_id, status, embedding_dimension, text_length, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, status, embedding_dimension, text_length, datetime.now()))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to mark product {product_id} as processed: {e}")
            raise
    
    def mark_batch_processed(self, records: List[Dict[str, Any]], status: str = "completed"):
        """
        Mark multiple products as processed in a single transaction.
        
        Args:
            records: List of records with 'id', 'embedding', 'text_combined' fields
            status: Status to set for all records
        """
        try:
            cursor = self.conn.cursor()
            
            data = []
            for record in records:
                product_id = record.get('id')
                embedding_dim = len(record.get('embedding', []))
                text_length = len(record.get('text_combined', ''))
                
                data.append((
                    product_id, 
                    status, 
                    embedding_dim, 
                    text_length, 
                    datetime.now()
                ))
            
            cursor.executemany("""
                INSERT OR REPLACE INTO embedding_progress 
                (product_id, status, embedding_dimension, text_length, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, data)
            
            self.conn.commit()
            logger.info(f"Marked {len(records)} records as {status}")
            
        except Exception as e:
            logger.error(f"Failed to mark batch as processed: {e}")
            raise
    
    def is_processed(self, product_id: int) -> bool:
        """
        Check if a product has been processed.
        
        Args:
            product_id: ID of the product
            
        Returns:
            bool: True if product has been processed
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM embedding_progress 
                WHERE product_id = ? AND status = 'completed'
            """, (product_id,))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check if product {product_id} is processed: {e}")
            return False
    
    def get_processed_ids(self) -> List[int]:
        """
        Get list of all processed product IDs.
        
        Returns:
            List[int]: List of processed product IDs
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT product_id FROM embedding_progress 
                WHERE status = 'completed'
                ORDER BY product_id
            """)
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Failed to get processed IDs: {e}")
            return []
    
    def get_last_processed_id(self) -> Optional[int]:
        """
        Get the ID of the last successfully processed product.
        
        Returns:
            Optional[int]: Last processed product ID, or None if no records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT MAX(product_id) FROM embedding_progress 
                WHERE status = 'completed'
            """)
            
            result = cursor.fetchone()[0]
            return result
            
        except Exception as e:
            logger.error(f"Failed to get last processed ID: {e}")
            return None
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """
        Get overall progress statistics.
        
        Returns:
            Dict: Statistics including total processed, failed, etc.
        """
        try:
            cursor = self.conn.cursor()
            
            # Get counts by status
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM embedding_progress 
                GROUP BY status
            """)
            
            status_counts = dict(cursor.fetchall())
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM embedding_progress")
            total = cursor.fetchone()[0]
            
            # Get last processed ID
            last_id = self.get_last_processed_id()
            
            stats = {
                'total_processed': total,
                'completed': status_counts.get('completed', 0),
                'failed': status_counts.get('failed', 0),
                'skipped': status_counts.get('skipped', 0),
                'last_processed_id': last_id,
                'status_breakdown': status_counts
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get progress stats: {e}")
            return {}
    
    def reset_progress(self):
        """Reset all progress (use with caution!)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM embedding_progress")
            cursor.execute("DELETE FROM embedding_metadata")
            self.conn.commit()
            logger.warning("Progress tracker has been reset!")
            
        except Exception as e:
            logger.error(f"Failed to reset progress: {e}")
            raise
    
    def set_metadata(self, key: str, value: str):
        """
        Set a metadata key-value pair.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO embedding_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to set metadata {key}: {e}")
            raise
    
    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get a metadata value by key.
        
        Args:
            key: Metadata key
            
        Returns:
            Optional[str]: Metadata value or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT value FROM embedding_metadata WHERE key = ?
            """, (key,))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get metadata {key}: {e}")
            return None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Progress tracker connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_progress_tracker():
    """Test function for the progress tracker."""
    logger.info("Testing Progress Tracker...")
    
    # Use a test database
    test_db = "./test_progress.db"
    
    with ProgressTracker(db_path=test_db) as tracker:
        # Test marking single record
        tracker.mark_processed(1, "completed", 768, 150)
        tracker.mark_processed(2, "completed", 768, 200)
        tracker.mark_processed(3, "failed", None, 0)
        
        # Test checking if processed
        assert tracker.is_processed(1) == True
        assert tracker.is_processed(999) == False
        
        # Test getting last processed ID
        last_id = tracker.get_last_processed_id()
        logger.info(f"Last processed ID: {last_id}")
        
        # Test getting stats
        stats = tracker.get_progress_stats()
        logger.info(f"Progress stats: {stats}")
        
        # Test metadata
        tracker.set_metadata("start_time", datetime.now().isoformat())
        start_time = tracker.get_metadata("start_time")
        logger.info(f"Start time: {start_time}")
    
    logger.info("✅ All tests passed!")
    
    # Clean up test database
    import os
    if os.path.exists(test_db):
        os.remove(test_db)
        logger.info("Test database cleaned up")


if __name__ == "__main__":
    test_progress_tracker()

