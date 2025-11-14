"""
Core framework modules for semantic search

Easy imports:
    from core import SemanticSearch
    from core import VectorStore
    from core.mock_embeddings import MockEmbeddingGenerator  # For offline mode
"""

from core.query_engine import SemanticSearch, QueryEngine
from core.vector_store import VectorStore

# EmbeddingGenerator and ResponseGenerator require OpenAI
# Import them only when needed to avoid dependency issues in offline mode

__all__ = [
    'SemanticSearch',
    'QueryEngine',
    'VectorStore'
]
