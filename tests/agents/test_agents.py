from pathlib import Path

from llama_index.core import Settings

from agents import RAGAgentType, RAGAgentFactory
from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel

from llama_index.embeddings.mistralai import MistralAIEmbedding

single_source_paths = Path("agents/res/example_file.txt")

multi_source_paths = [
    Path("agents/res/example_file.txt"),
    Path("agents/res/example_file_2.txt"),
    Path("agents/res/example_file_3.txt"),
]

model = initiate_model(SupportedModel.DEFAULT)
embeddings = initiate_embeddings(SupportedModel.DEFAULT)


Settings.embed_model=MistralAIEmbedding()


def test_simple_rag_agent():
    # Example of loading documents for llamaindex

    kwargs = {
        "model": model,
        "embeddings": embeddings,
        "source_paths": single_source_paths
    }

    rag_agent = RAGAgentFactory.create_agent(RAGAgentType.SINGLE_DOCUMENT,
                                             **kwargs)
    documents = rag_agent.docs
    assert documents, "No documents loaded"


def test_multi_document_rag_agent():
    # Example of loading documents for llamaindex
    source_path = "res"
    kwargs = {
        "model": model,
        "embeddings": embeddings,
        "source_paths": multi_source_paths
    }

    rag_agent = RAGAgentFactory.create_agent(RAGAgentType.MULTI_DOCUMENT, **kwargs)
    documents = rag_agent.docs
    assert documents, "No documents loaded"

