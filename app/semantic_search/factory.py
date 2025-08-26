# app/semantic_search/factory.py
from pathlib import Path
from enum import Enum
from typing import List, Dict, Union, Optional, Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.semantic_search.core import (
    SearchStrategy,
    SimpleVectorSearch,
    VectorStoreManager
)
from app.semantic_search.document_loaders import DocumentLoader, LlamaIndexDocumentLoader

class SearchStrategyType(Enum):
    """Types of search strategies available"""
    SIMPLE_VECTOR = "simple_vector"
    MULTI_DOCUMENT = "multi_document"

class SemanticSearchFactory:
    """Factory for creating and configuring semantic search components"""

    @staticmethod
    def create_strategy(
        strategy_type: SearchStrategyType,
        embeddings: Optional[Embeddings] = None,
        persist_directory: Optional[str] = None,
        **kwargs
    ) -> SearchStrategy:
        """
        Create a search strategy based on the specified type

        Args:
            strategy_type: Type of search strategy to create
            embeddings: Embedding model (required for SIMPLE_VECTOR)
            persist_directory: Directory to persist the index/vector store
            **kwargs: Additional arguments for specific strategy types

        Returns:
            An initialized search strategy
        """
        if strategy_type == SearchStrategyType.SIMPLE_VECTOR:
            if not embeddings:
                raise ValueError("Embeddings are required for SIMPLE_VECTOR strategy")

            collection_name = kwargs.get("collection_name", "default_collection")

            strategy = SimpleVectorSearch(
                embeddings=embeddings,
                collection_name=collection_name,
                persist_directory=persist_directory,
                search_type=kwargs.get("search_type", "similarity_score_threshold"),
                score_threshold=kwargs.get("score_threshold", 0.7)
            )

            # Initialize the VectorStoreManager with the strategy

            return strategy

        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

    @staticmethod
    def load_and_index_files(
            strategy: SearchStrategy,
            file_paths: Union[Path, List[Path]],
            embeddings: Optional[Embeddings] = None,
            **kwargs
    ) -> SearchStrategy:
        """
        Load files and add them to the search strategy

        Args:
            strategy: The search strategy to add documents to
            file_paths: Paths to the files to load
            embeddings: Embedding model (required for multi-document)
            **kwargs: Additional arguments for document loading

        Returns:
            The updated search strategy
        """
        if isinstance(strategy, SimpleVectorSearch):
            # For simple vector search, load as documents
            documents = DocumentLoader.load_from_files(
                file_paths,
                chunk_size=kwargs.get("chunk_size", 1000),
                chunk_overlap=kwargs.get("chunk_overlap", 200)
            )
            strategy.add_documents(documents)

        else:
            raise ValueError(f"Unsupported strategy type: {type(strategy)}")

        return strategy

    @staticmethod
    def load_and_index_urls(
        strategy: SearchStrategy,
        urls: Union[str, List[str]],
        **kwargs
    ) -> SearchStrategy:
        """
        Load URLs and add them to the search strategy

        Args:
            strategy: The search strategy to add documents to
            urls: URLs to load
            **kwargs: Additional arguments for document loading

        Returns:
            The updated search strategy
        """
        if not isinstance(strategy, SearchStrategy):
            raise ValueError("URL loading is only supported for SimpleVectorSearchStrategy")

        documents = DocumentLoader.load_from_urls(
            urls,
            chunk_size=kwargs.get("chunk_size", 1000),
            chunk_overlap=kwargs.get("chunk_overlap", 200)
        )
        strategy.add_documents(documents)

        return strategy