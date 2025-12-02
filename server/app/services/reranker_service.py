"""
Reranker service using HuggingFace BAAI/bge-reranker-v2-m3.
Reranks search results by relevance using a cross-encoder model.
Runs locally using sentence-transformers for better performance and reliability.
"""

import logging
import os
from typing import List, Dict, Any, Tuple
from sentence_transformers import CrossEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RerankerService:
    """Service for reranking search results using HuggingFace reranker model."""

    def __init__(self, model: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize the Reranker service with local CrossEncoder model.

        Args:
            model: HuggingFace model ID for reranking
        """
        self.model_name = model

        logger.info(f"Loading CrossEncoder model: {model}")
        logger.info("This may take a minute on first run (downloading model)...")

        try:
            # Load the cross-encoder model locally
            self.model = CrossEncoder(model, max_length=512)
            logger.info(f"✅ Successfully loaded reranker model: {model}")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            logger.warning("Reranking will be disabled")
            self.model = None

    def prepare_text_pairs(
        self, query: str, documents: List[Dict[str, Any]], text_field: str = "text_combined"
    ) -> List[Dict[str, str]]:
        """
        Prepare query-document pairs for reranking.

        Args:
            query: Search query text
            documents: List of document dictionaries
            text_field: Field name containing the document text

        Returns:
            List of dictionaries with 'text' (query) and 'text_pair' (document)
        """
        pairs = []

        for doc in documents:
            # Get document text from specified field or combine fields
            if text_field in doc:
                doc_text = doc[text_field]
            else:
                # Fallback: combine available text fields
                text_parts = []
                for field in ['win_item_name', 'brand_name', 'mainframe_description',
                             'catalog_number', 'wise_item_number', 'preferred_supplier']:
                    if field in doc and doc[field]:
                        text_parts.append(str(doc[field]))
                doc_text = " ".join(text_parts)

            pairs.append({
                "text": query,
                "text_pair": doc_text
            })

        return pairs

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 20,
        text_field: str = "text_combined"
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rerank documents based on relevance to the query using local CrossEncoder.

        Args:
            query: Search query text
            documents: List of document dictionaries to rerank
            top_k: Number of top results to return
            text_field: Field name containing the document text

        Returns:
            List of tuples (document, relevance_score) sorted by relevance (highest first)
        """
        if not documents:
            logger.warning("No documents provided for reranking")
            return []

        if not query or not query.strip():
            logger.warning("Empty query provided for reranking")
            return [(doc, 0.0) for doc in documents[:top_k]]

        # If model failed to load, return documents with zero scores
        if self.model is None:
            logger.warning("Reranker model not loaded, returning documents without reranking")
            return [(doc, 0.0) for doc in documents[:top_k]]

        try:
            logger.info(f"Reranking {len(documents)} documents for query: '{query[:100]}...'")

            # Prepare sentence pairs for the reranker
            sentence_pairs = []
            for doc in documents:
                if text_field in doc:
                    doc_text = doc[text_field]
                else:
                    # Fallback: combine available text fields
                    text_parts = []
                    for field in ['win_item_name', 'brand_name', 'mainframe_description',
                                 'catalog_number', 'wise_item_number', 'preferred_supplier']:
                        if field in doc and doc[field]:
                            text_parts.append(str(doc[field]))
                    doc_text = " ".join(text_parts)

                # CrossEncoder expects pairs of [query, document]
                sentence_pairs.append([query, doc_text])

            # Get relevance scores from the model
            scores = self.model.predict(sentence_pairs)

            # Create results list with documents and scores
            results = []
            for idx, score in enumerate(scores):
                results.append((documents[idx], float(score)))

            # Sort by score (descending) and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            top_results = results[:top_k]

            if len(top_results) > 0:
                logger.info(f"Reranking complete. Top score: {top_results[0][1]:.4f}, "
                           f"Bottom score: {top_results[-1][1]:.4f}")
            else:
                logger.warning("No results after reranking")

            return top_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            # Return original documents with zero scores on failure
            return [(doc, 0.0) for doc in documents[:top_k]]

    def rerank_batch(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 10,
        top_k: int = 20,
        text_field: str = "text_combined"
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rerank documents in batches (for large document sets).

        Args:
            query: Search query text
            documents: List of document dictionaries to rerank
            batch_size: Number of documents to process per batch
            top_k: Number of top results to return
            text_field: Field name containing the document text

        Returns:
            List of tuples (document, relevance_score) sorted by relevance
        """
        if len(documents) <= batch_size:
            return self.rerank(query, documents, top_k, text_field)

        # Process in batches
        all_results = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_results = self.rerank(query, batch, len(batch), text_field)
            all_results.extend(batch_results)
            logger.info(f"Processed batch {i//batch_size + 1}, total results: {len(all_results)}")

        # Sort all results and return top_k
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]


def test_reranker_service():
    """Test function for the Reranker service."""
    logger.info("Testing Reranker Service...")

    # Check for HF_TOKEN
    if not os.environ.get("HF_TOKEN"):
        logger.warning("⚠️  HF_TOKEN not set. Set it with: export HF_TOKEN='your_token_here'")

    service = RerankerService()

    # Test data
    query = "stainless steel pipe fitting"
    test_documents = [
        {
            "id": "1",
            "text_combined": "Carbon steel pipe connector 2 inch diameter",
            "win_item_name": "Carbon Steel Connector",
            "brand_name": "ACME"
        },
        {
            "id": "2",
            "text_combined": "Stainless steel pipe fitting 1.5 inch premium quality",
            "win_item_name": "SS Pipe Fitting",
            "brand_name": "QUALITY"
        },
        {
            "id": "3",
            "text_combined": "Brass elbow joint for plumbing",
            "win_item_name": "Brass Elbow",
            "brand_name": "PLUMB"
        },
        {
            "id": "4",
            "text_combined": "Stainless steel coupling heavy duty industrial",
            "win_item_name": "SS Coupling",
            "brand_name": "INDUSTRIAL"
        }
    ]

    logger.info(f"Query: '{query}'")
    logger.info(f"Reranking {len(test_documents)} test documents...")

    # Test reranking
    results = service.rerank(query, test_documents, top_k=4)

    logger.info("\n=== Reranking Results ===")
    for idx, (doc, score) in enumerate(results, 1):
        logger.info(f"{idx}. Score: {score:.4f} - {doc['win_item_name']} ({doc['brand_name']})")
        logger.info(f"   Text: {doc['text_combined']}")

    # Expected: Document 2 and 4 should rank highest (contain "stainless steel")
    logger.info("\n✅ Test complete!")
    return True


if __name__ == "__main__":
    test_reranker_service()
