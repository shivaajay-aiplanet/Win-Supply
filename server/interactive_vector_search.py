"""
Interactive vector search tool.
Allows you to test vector search with multiple queries in a session.
"""

import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, ".")

from app.services.embedding_service import OllamaEmbeddingService
from app.db.opensearch_vector import search_by_vector
from app.db.opensearch import get_opensearch_client
from app.config.settings import OPENSEARCH_VECTOR_INDEX_NAME

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise in interactive mode
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InteractiveVectorSearch:
    """Interactive vector search session."""
    
    def __init__(self):
        """Initialize the search session."""
        self.embedding_service = None
        self.opensearch_client = None
        self.initialized = False
    
    def initialize(self):
        """Initialize connections to Ollama and OpenSearch."""
        if self.initialized:
            return True
        
        try:
            print("\n🔧 Initializing vector search system...")
            
            # Initialize embedding service
            print("   → Connecting to Ollama...")
            self.embedding_service = OllamaEmbeddingService()
            
            if not self.embedding_service.test_connection():
                print("   ❌ Failed to connect to Ollama")
                return False
            
            print("   ✅ Ollama connected")
            
            # Initialize OpenSearch
            print("   → Connecting to OpenSearch...")
            self.opensearch_client = get_opensearch_client()
            
            # Verify index exists
            if not self.opensearch_client.indices.exists(index=OPENSEARCH_VECTOR_INDEX_NAME):
                print(f"   ❌ Index '{OPENSEARCH_VECTOR_INDEX_NAME}' does not exist")
                return False
            
            doc_count = self.opensearch_client.count(index=OPENSEARCH_VECTOR_INDEX_NAME)["count"]
            print(f"   ✅ OpenSearch connected ({doc_count:,} products indexed)")
            
            self.initialized = True
            print("✅ System ready!\n")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def search(self, query: str, top_k: int = 10):
        """
        Perform vector search for a query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
        """
        if not self.initialized:
            print("❌ System not initialized. Please run initialize() first.")
            return
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            if not query_embedding:
                print("❌ Failed to generate query embedding")
                return
            
            # Perform vector search
            search_results = search_by_vector(
                client=self.opensearch_client,
                query_embedding=query_embedding,
                index_name=OPENSEARCH_VECTOR_INDEX_NAME,
                top_k=top_k
            )
            
            # Display results
            self._display_results(query, search_results, top_k)
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    def _display_results(self, query: str, results: dict, top_k: int):
        """Display search results in a formatted way."""
        print("\n" + "=" * 100)
        print(f"🔍 Query: \"{query}\"")
        print(f"📊 Found: {results['total_hits']} matches | Showing top {top_k}")
        print("=" * 100)
        
        if not results["results"]:
            print("\n⚠️  No results found\n")
            return
        
        for idx, result in enumerate(results["results"], 1):
            doc = result["document"]
            score = result["score"]
            
            print(f"\n{idx}. 📦 {doc.get('win_item_name', 'N/A')}")
            print(f"   🎯 Similarity: {score:.4f} ({score*100:.2f}%)")
            print(f"   🏷️  Brand: {doc.get('brand_name', 'N/A')}")
            print(f"   🔢 Item #: {doc.get('wise_item_number', 'N/A')}")
            print(f"   🆔 ID: {doc.get('id', 'N/A')}")
        
        print("\n" + "=" * 100 + "\n")
    
    def run_interactive(self):
        """Run interactive search session."""
        print("\n" + "=" * 100)
        print("🔍 INTERACTIVE VECTOR SEARCH")
        print("=" * 100)
        print("\nSearch 333,668 products using semantic vector similarity!")
        print("\nCommands:")
        print("  • Type your search query and press Enter")
        print("  • Type 'quit' or 'exit' to exit")
        print("  • Type 'help' for examples")
        print("=" * 100)
        
        # Initialize system
        if not self.initialize():
            print("\n❌ Failed to initialize. Exiting.")
            return
        
        # Interactive loop
        while True:
            try:
                # Get user input
                query = input("\n🔍 Search: ").strip()
                
                if not query:
                    continue
                
                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break
                
                if query.lower() == 'help':
                    self._show_examples()
                    continue
                
                # Perform search
                self.search(query, top_k=10)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    def _show_examples(self):
        """Show example queries."""
        print("\n" + "=" * 100)
        print("📚 EXAMPLE QUERIES")
        print("=" * 100)
        print("\n1. Specific product search:")
        print("   → 1/100 HP 110 V Evaporator Fan Motor Kit")
        print("   → copper pipe for plumbing")
        print("   → air conditioning unit")
        
        print("\n2. Category search:")
        print("   → HVAC equipment")
        print("   → electrical wiring")
        print("   → plumbing fixtures")
        
        print("\n3. Application-based search:")
        print("   → parts for refrigerator")
        print("   → heating system components")
        print("   → water heater accessories")
        
        print("\n4. Specification search:")
        print("   → 3 ton air conditioner")
        print("   → 1/2 inch copper tubing")
        print("   → 110 volt motor")
        
        print("\n" + "=" * 100)


def main():
    """Main function to run interactive search."""
    searcher = InteractiveVectorSearch()
    searcher.run_interactive()


if __name__ == "__main__":
    main()

