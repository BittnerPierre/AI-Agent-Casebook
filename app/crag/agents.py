from pathlib import Path
from typing import Union, List, Dict

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
from core import SupportedModel, initiate_model, logger, initiate_embeddings


class Retriever(AbstractAgent):

    def __init__(self,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 ):

        self.embeddings = embeddings
        self.urls = [
            "https://lilianweng.github.io/posts/2023-06-23-agent/",
            "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
            "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
        ]
        print(f"Source path: '{self.urls}'")
        self.docs = self._initiate_docs(urls=self.urls)
        super().__init__(model=model)


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

retriever = Retriever(model, embeddings)

rag_chain = RAGChain(model)

retrieval_grader = RetrievalGrader(model)

question_rewriter = QuestionRewriter(model)

web_search_tool = TavilySearchResults(max_results=3)
