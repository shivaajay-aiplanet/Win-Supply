"""
Embedding service for generating vector embeddings using Ollama.
Handles connection to local Ollama instance and batch embedding generation.
"""

import logging
import time
from typing import List, Dict, Any
import ollama
from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL, FIELDS_TO_INDEX

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    """Service for generating embeddings using Ollama."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        """
        Initialize the Ollama embedding service.

        Args:
            host: Ollama server host URL
            model: Name of the embedding model to use
        """
        self.host = host
        self.model = model
        self.client = ollama.Client(host=host)
        logger.info(f"Initialized Ollama client with host: {host}, model: {model}")

    def test_connection(self) -> bool:
        """
        Test connection to Ollama server and verify model availability.

        Returns:
            bool: True if connection successful and model available
        """
        try:
            # List available models
            models = self.client.list()

            # Handle different response formats
            if isinstance(models, dict) and "models" in models:
                model_list = models["models"]
            else:
                model_list = models if isinstance(models, list) else []

            # Extract model names safely
            model_names = []
            for m in model_list:
                if isinstance(m, dict):
                    model_names.append(m.get("name", m.get("model", str(m))))
                else:
                    model_names.append(str(m))

            logger.info(f"Available Ollama models: {model_names}")

            # Check if our model is available
            if not any(self.model in name for name in model_names):
                logger.warning(
                    f"Model '{self.model}' not found. Available models: {model_names}"
                )
                logger.info(f"Attempting to pull model '{self.model}'...")
                self.client.pull(self.model)
                logger.info(f"Successfully pulled model '{self.model}'")

            # Test embedding generation
            test_embedding = self.client.embeddings(model=self.model, prompt="test")

            embedding_dim = len(test_embedding["embedding"])
            logger.info(f"Connection successful! Embedding dimension: {embedding_dim}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}", exc_info=True)
            return False

    def combine_text_fields(self, record: Dict[str, Any]) -> str:
        """
        Combine multiple text fields from a product record into a single string.

        Args:
            record: Product record dictionary

        Returns:
            str: Combined and cleaned text
        """
        text_parts = []

        for field in FIELDS_TO_INDEX:
            value = record.get(field)
            if value and str(value).strip() and str(value).lower() != "none":
                text_parts.append(str(value).strip())

        # Join with spaces and clean up
        combined_text = " ".join(text_parts)

        # Remove extra whitespace
        combined_text = " ".join(combined_text.split())

        return combined_text

    def generate_embedding(self, text: str, retry_count: int = 3) -> List[float]:
        """
        Generate embedding for a single text string with retry logic.

        Args:
            text: Input text to embed
            retry_count: Number of retries on failure

        Returns:
            List[float]: Embedding vector

        Raises:
            Exception: If all retries fail
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []

        for attempt in range(retry_count):
            try:
                response = self.client.embeddings(model=self.model, prompt=text)

                embedding = response["embedding"]
                return embedding

            except Exception as e:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Embedding generation failed (attempt {attempt + 1}/{retry_count}): {e}"
                )

                if attempt < retry_count - 1:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for text: {text[:100]}...")
                    raise

        return []

    def generate_batch_embeddings(
        self, records: List[Dict[str, Any]], show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of records.

        Args:
            records: List of product records
            show_progress: Whether to log progress

        Returns:
            List[Dict]: Records with added 'text_combined' and 'embedding' fields
        """
        enriched_records = []
        failed_count = 0

        for idx, record in enumerate(records):
            try:
                # Combine text fields
                combined_text = self.combine_text_fields(record)

                if not combined_text:
                    logger.warning(f"Record ID {record.get('id')} has no text content")
                    failed_count += 1
                    continue

                # Generate embedding
                embedding = self.generate_embedding(combined_text)

                if not embedding:
                    logger.warning(
                        f"Failed to generate embedding for record ID {record.get('id')}"
                    )
                    failed_count += 1
                    continue

                # Add to record
                enriched_record = record.copy()
                enriched_record["text_combined"] = combined_text
                enriched_record["embedding"] = embedding

                enriched_records.append(enriched_record)

                if show_progress and (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx + 1}/{len(records)} records in batch")

            except Exception as e:
                logger.error(f"Error processing record ID {record.get('id')}: {e}")
                failed_count += 1
                continue

        success_count = len(enriched_records)
        logger.info(
            f"Batch complete: {success_count} successful, {failed_count} failed"
        )

        return enriched_records


def test_ollama_service():
    """Test function for the Ollama embedding service."""
    logger.info("Testing Ollama Embedding Service...")

    service = OllamaEmbeddingService()

    # Test connection
    if not service.test_connection():
        logger.error("Connection test failed!")
        return False

    # Test single embedding
    test_text = "4 x 12 x 6 in. 90-Degree Center End Register Boot"
    logger.info(f"Generating test embedding for: '{test_text}'")

    embedding = service.generate_embedding(test_text)
    logger.info(f"Generated embedding with dimension: {len(embedding)}")
    logger.info(f"First 5 values: {embedding[:5]}")

    # Test batch processing
    test_records = [
        {
            "id": 1,
            "win_item_name": "Test Product 1",
            "brand_name": "WATCO",
            "mainframe_description": "Test description 1",
        },
        {
            "id": 2,
            "win_item_name": "Test Product 2",
            "brand_name": "AIR FLOW",
            "mainframe_description": "Test description 2",
        },
    ]

    logger.info("Testing batch embedding generation...")
    enriched = service.generate_batch_embeddings(test_records)
    logger.info(f"Batch processing complete: {len(enriched)} records enriched")

    for record in enriched:
        logger.info(
            f"Record {record['id']}: text length={len(record['text_combined'])}, "
            f"embedding dim={len(record['embedding'])}"
        )

    logger.info("✅ All tests passed!")
    return True


if __name__ == "__main__":
    test_ollama_service()
