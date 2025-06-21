# Advanced Retrieval for AI - Smoke Test

## Introduction to Advanced Retrieval Systems

Welcome to Advanced Retrieval for AI, where we explore building retrieval-augmented generation (RAG) systems. This module covers embeddings, vector databases, and RAG implementation patterns.

Modern AI applications rely on retrieval systems to ground language models in specific knowledge bases, enabling more accurate and contextually relevant responses.

## Understanding Embeddings

### What are Embeddings?

Embeddings are dense vector representations of text that capture semantic meaning in high-dimensional space. They enable semantic similarity matching beyond keyword-based search.

**Key Properties:**
- **Semantic Preservation**: Similar concepts cluster together
- **Dimensionality**: Typically 384 to 1536 dimensions
- **Distance Metrics**: Cosine similarity, dot product, Euclidean distance

### Vector Search Basics

**Basic Vector Search Process:**
1. **Encode Query**: Convert text query into embedding vector
2. **Similarity Computation**: Calculate distance to stored vectors
3. **Ranking**: Sort results by similarity score
4. **Retrieval**: Return top-k most similar documents

### Distance Metrics

**Cosine Similarity:**
```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

## ChromaDB Integration

### Basic ChromaDB Setup

```python
import chromadb

class VectorStore:
    def __init__(self, collection_name="documents"):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(collection_name)
        
    def add_documents(self, documents, ids):
        self.collection.add(
            documents=documents,
            ids=ids
        )
        
    def search(self, query, n_results=5):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
```

## Basic RAG Workflow

**Simple RAG Implementation:**
```python
class SimpleRAG:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        
    def query(self, question):
        # Retrieve relevant documents
        results = self.vector_store.search(question)
        context = "\n".join(results['documents'][0])
        
        # Generate response
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        return self.llm.generate(prompt)
```

This smoke test covers core retrieval and RAG implementation patterns.