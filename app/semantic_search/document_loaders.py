# app/semantic_search/document_loaders.py
from typing import List, Union, Dict, Optional, Tuple, Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, TextLoader, PyPDFLoader
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode

from app.core.logger import logger


class DocumentLoader:
    """Utility for loading and processing documents from various sources"""

    @staticmethod
    def load_from_file(file_path: Path,
                     chunk_size: int = 1000,
                     chunk_overlap: int = 200) -> List[Document]:
        """Load and split a single document file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Choose loader based on file extension
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        else:
            # Default to text loader
            loader = TextLoader(str(file_path))

        documents = loader.load()

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        split_docs = text_splitter.split_documents(documents)

        # Add source filename to metadata if not present
        for doc in split_docs:
            if 'source' not in doc.metadata:
                doc.metadata['source'] = file_path.name

        return split_docs

    @staticmethod
    def load_from_files(file_paths: Union[Path, List[Path]],
                       chunk_size: int = 1000,
                       chunk_overlap: int = 200) -> List[Document]:
        """Load and split multiple document files"""
        if isinstance(file_paths, Path):
            file_paths = [file_paths]

        all_docs = []
        for path in file_paths:
            try:
                docs = DocumentLoader.load_from_file(path, chunk_size, chunk_overlap)
                all_docs.extend(docs)
                logger.info(f"Loaded {len(docs)} chunks from {path}")
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")

        return all_docs

    @staticmethod
    def load_from_directory(directory_path: Path,
                          file_patterns: Optional[List[str]] = None,
                          chunk_size: int = 1000,
                          chunk_overlap: int = 200) -> List[Document]:
        """Load all documents from a directory matching the patterns"""
        if not directory_path.exists() or not directory_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory_path}")

        # Get all files matching patterns
        all_files = []
        if file_patterns:
            for pattern in file_patterns:
                all_files.extend(list(directory_path.glob(pattern)))
        else:
            # Default to common document types
            all_files.extend(list(directory_path.glob("*.txt")))
            all_files.extend(list(directory_path.glob("*.pdf")))
            all_files.extend(list(directory_path.glob("*.md")))

        return DocumentLoader.load_from_files(all_files, chunk_size, chunk_overlap)

    @staticmethod
    def load_from_urls(urls: Union[str, List[str]],
                      chunk_size: int = 1000,
                      chunk_overlap: int = 200) -> List[Document]:
        """Load and split documents from URLs"""
        if isinstance(urls, str):
            urls = [urls]

        all_docs = []
        for url in urls:
            try:
                docs = WebBaseLoader(url).load()
                all_docs.extend(docs)
                logger.info(f"Loaded content from URL: {url}")
            except Exception as e:
                logger.error(f"Error loading URL {url}: {e}")

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        doc_splits = text_splitter.split_documents(all_docs)

        # Add source URL to metadata if not present
        for i, doc in enumerate(doc_splits):
            if 'source' not in doc.metadata and i < len(urls):
                doc.metadata['source'] = urls[i]

        return doc_splits


class LlamaIndexDocumentLoader:
    """Utility for loading documents specifically for LlamaIndex"""

    @staticmethod
    def load_nodes_from_file(file_path: Path,
                           chunk_size: int = 1024) -> List[BaseNode]:
        """Load a single file as nodes for LlamaIndex"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        documents = SimpleDirectoryReader(input_files=[str(file_path)]).load_data()
        splitter = SentenceSplitter(chunk_size=chunk_size)
        nodes = splitter.get_nodes_from_documents(documents)

        return nodes

    @staticmethod
    def load_nodes_from_files(file_paths: Union[Path, List[Path]],
                            chunk_size: int = 1024) -> Dict[Path, List[BaseNode]]:
        """Load multiple files as nodes for LlamaIndex with file-based organization"""
        if isinstance(file_paths, Path):
            file_paths = [file_paths]

        file_to_nodes = {}
        for path in file_paths:
            try:
                nodes = LlamaIndexDocumentLoader.load_nodes_from_file(path, chunk_size)
                file_to_nodes[path] = nodes
                logger.info(f"Loaded {len(nodes)} nodes from {path}")
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")

        return file_to_nodes

    @staticmethod
    def create_document_tools(embeddings: Embeddings,
                            file_to_nodes: Dict[Path, List[BaseNode]]) -> List[Any]:
        """Create search and summary tools for each document"""
        from ai_agents.utils import get_doc_tools

        all_tools = []
        for file_path, nodes in file_to_nodes.items():
            vector_tool, summary_tool = get_doc_tools(embeddings, nodes, file_path.stem)
            all_tools.extend([vector_tool, summary_tool])

        return all_tools