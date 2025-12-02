"""
Configuration module for the Product Search API.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Configuration
POSTGRES_CONNECTION_STRING = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://admin:jsewRsEebObGO2lvPoxXvcBhzvNvZ57F@dpg-d49dvs4hg0os738oqnog-a.oregon-postgres.render.com/win_inventory",
)

# OpenSearch Configuration
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "Shiva54510$")
OPENSEARCH_INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "inventory")

# OpenSearch connection URL
OPENSEARCH_URL = f"https://{OPENSEARCH_HOST}:{OPENSEARCH_PORT}"

# PostgreSQL table name
POSTGRES_TABLE_NAME = "inventory"

# Fields to extract from PostgreSQL and index in OpenSearch
FIELDS_TO_INDEX = [
    "preferred_supplier",
    "brand_name",
    "wise_item_number",
    "catalog_number",
    "mainframe_description",
    "win_item_name",
]

# Bulk indexing configuration
BULK_INDEX_BATCH_SIZE = 500

# Phase 2: Vector Embeddings Configuration
OPENSEARCH_VECTOR_INDEX_NAME = os.getenv(
    "OPENSEARCH_VECTOR_INDEX_NAME", "inventory_vector"
)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text:v1.5")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
PROGRESS_DB_PATH = os.getenv("PROGRESS_DB_PATH", "./embedding_progress.db")

# Phase 3: Azure OpenAI LLM Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT", "o4-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "50"))
LLM_MAX_RESULTS = int(os.getenv("LLM_MAX_RESULTS", "20"))
