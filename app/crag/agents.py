from pathlib import Path
from typing import Union, List, Dict, Any

from langchain import hub
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import TavilySearchResults
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import Field, BaseModel

from agents import AbstractAgent
from agents.base import Input, Output, Agent
from core import SupportedModel, initiate_model, logger, initiate_embeddings
from semantic_search.core import SearchStrategy, SimpleVectorSearch, VectorStoreManager
from semantic_search.factory import SemanticSearchFactory, SearchStrategyType


class Retriever(AbstractAgent):

    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 urls: Union[str, List[str]]
                 ):

        self.embeddings = embeddings
        self.urls = urls
        self.docs = self._initiate_docs(urls=self.urls)
        super().__init__(name=name, model=model)


    def _initiate_docs(self, urls: Union[str, List[str]]) -> List[Document]:
        """
        Initialize documents from source paths.
        This is an instance method because it's part of the object's initialization process
        and may need access to instance attributes like self.embeddings
        """
        if isinstance(urls, str):
            source_paths = [urls]

        docs = [WebBaseLoader(url).load() for url in urls]
        docs_list = [item for sublist in docs for item in sublist]

        # text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=100,
        #     chunk_overlap=20,
        #     length_function=len,
        #     is_separator_regex=False,
        # )
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=250, chunk_overlap=0
        )
        doc_splits = text_splitter.split_documents(docs_list)

        return doc_splits

    def _initiate_runnable(self):
        # Add to vectorDB
        vectorstore = Chroma.from_documents(
            documents=self.docs,
            collection_name="crag-chroma",
            embedding=self.embeddings,
        )
        _retriever = vectorstore.as_retriever()
        return _retriever


class Retriever2(Agent):
    """Agent that uses a search strategy to retrieve documents"""

    def __init__(self,
                 name: str,
                 search_strategy: SearchStrategy):
        self.search_strategy = search_strategy
        super().__init__(name=name)

    # def _initiate_runnable(self):
    #     def retriever_func(query):
    #         results = self.search_strategy.retrieve(query)
    #         # Return the raw results for further processing
    #         return results
    #
    #     return self.search_strategy.retrieve


    def invoke(self, input: Input, **kwargs: Any) -> Output:
        response = self.search_strategy.retrieve(input)
        return response


class QuestionRewriter(AbstractAgent):

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Writer Agent")

        # Prompt
        system = """You a question re-writer that converts an input question to a better version that is optimized 
             for web search. Look at the input and try to reason about the underlying semantic intent / meaning.
             Please provide an answer with a maximum of 350 characters."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Here is the initial question: '''\n\n {question} \n''' Formulate an improved question.",
                ),
            ]
        )
        _question_rewriter = re_write_prompt | self.model | StrOutputParser()
        return _question_rewriter


### Retrieval Grader

class RetrievalGrader(AbstractAgent):

    def _initiate_runnable(self) -> RunnableSerializable:
        # Data model
        class GradeDocuments(BaseModel):
            """Binary score for relevance check on retrieved documents."""

            binary_score: str = Field(
                description="Documents are relevant to the question, 'yes' or 'no'"
            )


        # LLM with function call
        structured_llm_grader = self.model.with_structured_output(GradeDocuments)

        # Prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
            If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )

        _retrieval_grader = grade_prompt | structured_llm_grader
        return _retrieval_grader


class RAGChain(AbstractAgent):
    def _initiate_runnable(self):
        # GENERATE

        prompt = hub.pull("rlm/rag-prompt")

        # Post-processing
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Chain
        _rag_chain = prompt | self.model | StrOutputParser()
        return _rag_chain


model = initiate_model(SupportedModel.DEFAULT)
embeddings = initiate_embeddings(SupportedModel.DEFAULT)

search = SemanticSearchFactory.create_strategy(
    SearchStrategyType.SIMPLE_VECTOR,
    embeddings,
    kwargs={"collection_name", "simple-vector-store"}
)
VectorStoreManager(search)

retriever = Retriever2("retriever", search)

rag_chain = RAGChain("rag_chain", model)

retrieval_grader = RetrievalGrader("retrieval_grader", model)

question_rewriter = QuestionRewriter("question_writer", model)

web_search_tool = TavilySearchResults(max_results=3)
