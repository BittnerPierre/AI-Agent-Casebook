# app/semantic_search/usage_example.py
from langchain_community.embeddings import HuggingFaceEmbeddings  # or your preferred embedding model
from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings

from semantic_search.core import SimpleVectorSearch, VectorStoreManager
from core import initiate_model, SupportedModel
from crag.agents import Retriever2
from semantic_search.factory import SemanticSearchFactory, SearchStrategyType


def main():
    # Initialize embedding model
    embeddings = MistralAIEmbeddings()

    # Create persistent vector store with a directory
    # Or pass persist_directory=None for in-memory only

    search_strategy = SemanticSearchFactory.create_strategy(
        SearchStrategyType.SIMPLE_VECTOR,
        embeddings,
        kwargs={"collection_name", "my_documents"}
    )
    VectorStoreManager(search_strategy)

    search = VectorStoreManager.get_strategy()

    # search = SimpleVectorSearch(
    #     embeddings=embeddings,
    #     collection_name="my_documents",
    #     # persist_directory="./data/vector_store",
    #     score_threshold=0.6
    # )

    # Example documents
    documents = [
        Document(page_content="Machine learning is a subset of artificial intelligence", metadata={"source": "doc1"}),
        Document(page_content="Neural networks are computing systems vaguely inspired by biological networks",
                 metadata={"source": "doc2"}),
        Document(page_content="Python is a popular programming language for data science", metadata={"source": "doc3"}),
        Document(page_content="Transformers are a type of neural network architecture", metadata={"source": "doc4"})
    ]

    # Add documents to vector store
    search.add_documents(documents)

    # Query the vector store
    results = search.retrieve("Tell me about neural networks")

    # Print results
    print(f"Found {len(results)} relevant documents:")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i + 1} ---")
        print(f"Content: {doc.page_content}")
        print(f"Source: {doc.metadata.get('source')}")
        print(f"Score: {doc.metadata.get('score')}")

    # You can add more documents later
    more_documents = [
        Document(page_content="Large language models have transformed natural language processing",
                 metadata={"source": "doc5"})
    ]
    search.add_documents(more_documents)
    search.add_documents(more_documents)
    search.add_documents(more_documents)

    search2 = VectorStoreManager.get_strategy()
    retriever = Retriever2("test", search2)
    res = retriever.invoke("Tell me about Large language models")
    print(res)

if __name__ == "__main__":
    main()