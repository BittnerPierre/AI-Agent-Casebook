# app/semantic_search/simple_core.py
import abc
import os
import uuid
from typing import List, Optional, Any

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from core.logger import logger

class SearchStrategy(abc.ABC):
    """Abstract base strategy for semantic search"""

    @abc.abstractmethod
    def retrieve(self, query: str, **kwargs) -> List[Any]:
        """Retrieve relevant items based on query"""
        pass

    @abc.abstractmethod
    async def aretrieve(self, query: str, **kwargs) -> List[Any]:
        """Asynchronously retrieve relevant items based on query"""
        pass


    @abc.abstractmethod
    def add_documents(self, documents: List[Any]) -> None:
        """Add documents to the search index"""
        pass


class SimpleVectorSearch(SearchStrategy):
    """
    Simple vector search implementation using Chroma DB.
    This class provides a straightforward approach to semantic search
    with minimal complexity.
    """

    def __init__(
            self,
            embeddings: Embeddings,
            collection_name: str = "default_collection",
            persist_directory: Optional[str] = None,
            score_threshold: float = 0.6,
            search_type: str = "similarity_score_threshold"
    ):
        """
        Initialize the vector search

        Args:
            embeddings: Embedding model to use
            collection_name: Name of the collection
            persist_directory: Directory to persist the vector store (if None, uses in-memory store)
            score_threshold: Minimum similarity score threshold for retrieval
        """
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.score_threshold = score_threshold
        self.search_type = search_type

        self.vectorstore = None
        self.retriever = None

        # Initialize the vector store
        self._initialize_vectorstore()

    def _initialize_vectorstore(self):
        """Initialize or load the vector store based on whether a persist directory is provided"""
        if self.persist_directory and os.path.exists(self.persist_directory):
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            try:
                client = chromadb.PersistentClient(path=self.persist_directory)

                # Get all collection names to check if our collection exists
                collection_names = client.list_collections()

                if self.collection_name in collection_names:
                    # Collection exists, load it
                    self.vectorstore = Chroma(
                        client=client,
                        collection_name=self.collection_name,
                        embedding_function=self.embeddings
                    )
                    logger.info(f"Loaded existing collection '{self.collection_name}'")

                    # Initialize retriever
                    self.retriever = self.vectorstore.as_retriever(
                        search_type=self.search_type,
                        search_kwargs={"score_threshold": self.score_threshold}
                    )
                else:
                    # Collection doesn't exist yet
                    logger.info(
                        f"Collection '{self.collection_name}' doesn't exist yet, will be created when documents are added")
                    self.vectorstore = None
                    self.retriever = None
            except Exception as e:
                logger.warning(f"Error loading vector store: {e}")
                self.vectorstore = None
                self.retriever = None
        else:
            storage_type = "memory" if not self.persist_directory else f"disk at {self.persist_directory}"
            logger.info(f"Initializing new vector store in {storage_type}")
            self.vectorstore = None
            self.retriever = None

    def _get_unique_documents(self, documents: List[Document]):
        """Filter out duplicate documents based on content"""
        id_bag = {}
        unique_docs = []
        for doc in documents:
            id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.page_content))
            doc.id = id
            if id not in id_bag:
                id_bag[id] = True
                unique_docs.append(doc)
        return unique_docs, id_bag

    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        if not documents:
            logger.warning("No documents provided to add to vector store")
            return

        logger.info(f"Adding {len(documents)} documents to vector store")

        # Get unique ids
        unique_docs, id_bag = self._get_unique_documents(documents)

        # Create new vector store if it doesn't exist
        if self.vectorstore is None:

            if self.persist_directory:
                # Ensure directory exists
                os.makedirs(self.persist_directory, exist_ok=True)
                client = chromadb.PersistentClient(path=self.persist_directory)

                self.vectorstore = Chroma.from_documents(
                    documents=unique_docs,
                    ids=list(id_bag.keys()),
                    embedding=self.embeddings,
                    collection_name=self.collection_name,
                    client=client
                )
            else:
                self.vectorstore = Chroma.from_documents(
                    documents=unique_docs,
                    embedding=self.embeddings,
                    collection_name=self.collection_name
                )
        else:
            # Add to existing vector store
            self.vectorstore.add_documents(unique_docs)


        # Update retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type=self.search_type,
            search_kwargs={"score_threshold": self.score_threshold}
        )

        # not needed anymore automatic if persist_directory is given, _client.persist() deprecated
        # # Persist automatically if using persistent storage
        # if self.persist_directory and hasattr(self.vectorstore, "_client") and hasattr(self.vectorstore._client,
        #                                                                                "persist"):
        #     self.vectorstore._client.persist()
        #     logger.info("Vector store persisted to disk")

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve documents using vector similarity"""
        if not self.retriever:
            logger.warning("No documents have been added to the vector store yet")
            return []

        return self.retriever.invoke(query, **kwargs)

    async def aretrieve(self, query: str, **kwargs) -> List[Document]:
        """Asynchronously retrieve documents using vector similarity"""
        if not self.retriever:
            logger.warning("No documents have been added to the vector store yet")
            return []
        return await self.retriever.ainvoke(query, **kwargs)


class VectorStoreManager:
    _instance = None
    _strategy: Optional[SearchStrategy] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, strategy: Optional[SearchStrategy] = None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            if strategy:
                self.set_strategy(strategy)

    @classmethod
    def get_strategy(cls) -> SearchStrategy:
        if not cls._strategy:
            raise ValueError("VectorStoreManager has not been initialized with a strategy")
        return cls._strategy

    @classmethod
    def set_strategy(cls, strategy: SearchStrategy):
        if cls._strategy:
            raise ValueError("Strategy is already set")
        cls._strategy = strategy