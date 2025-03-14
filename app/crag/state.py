from typing import  List, TypedDict

from langchain_core.documents import Document

class CragAgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to add search
        documents: list of documents
    """

    question: str
    generation: str
    web_search: str
    query: str
    documents: List[Document]
