import abc
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Optional, List, Any, Union, Dict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable, RunnableMap
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.prebuilt import create_react_agent
from llama_index.core import Document as LlamaDocument, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.objects import ObjectIndex
from llama_index.core.schema import BaseNode

from agents.base import AbstractAgent
from agents.utils import get_doc_tools
from core.logger import logger

_RAG_AGENT_DEFAULT_COLLECTION_NAME = "ragagent"


class AbstractRAGAgent(AbstractAgent):

    def __init__(self,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 source_paths: Union[Path, List[Path]]):
        super().__init__(model=model)
        self.embeddings = embeddings  # self._initiate_embeddings()
        self.source_paths = source_paths
        print(f"Source path: '{self.source_paths}'")
        self.docs = self._initiate_docs(source_paths=self.source_paths)

    @abc.abstractmethod
    def _initiate_docs(self, source_paths: Union[Path, List[Path]])\
            -> Dict[Path, Union[List[Document], List[BaseNode]]]:
        """Abstract method to load and split documents."""
        pass


class SimpleRAGAgent(AbstractRAGAgent):

    # TODO add a in memory vectorstore...
    def __init__(self,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 source_paths: Path,
                 collection_name: Optional[str] = _RAG_AGENT_DEFAULT_COLLECTION_NAME,
                 # persist_directory: str,
                 ):
        super().__init__(model=model, embeddings=embeddings, source_paths=source_paths)
        self._collection_name = collection_name or _RAG_AGENT_DEFAULT_COLLECTION_NAME
        # self.persist_directory = persist_directory

        # RAG classic
        self.vectorstore = self._initiate_vectorstore()
        self.retriever = self._initiate_retriever()
        self.runnable = self._initiate_agent_chain()

    def _initiate_docs(self, source_paths: Union[Path, List[Path]]) -> Dict[Path, List[Document]]:
        """Load and split documents for langchain."""
        if isinstance(source_paths, Path):
            source_paths = [source_paths]
        else:
            source_paths = source_paths

        source_to_docs = {}
        for path in source_paths:
            documents = SimpleDirectoryReader(input_files=[path]).load_data()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=100,
                chunk_overlap=20,
                length_function=len,
                is_separator_regex=False,
            )
            split_docs = text_splitter.create_documents([doc.text for doc in documents])
            source_to_docs[path] = split_docs

        return source_to_docs

    def _initiate_vectorstore(self) -> VectorStore:
        logger.debug("Initiating VectorStore")
        # TODO check consistency with embedding, model and vectorstore
        # TODO memory only one
        # TODO check existing file to avoir reload (code above does not work an create an empty vectore store
        all_docs = [doc for docs in self.docs.values() for doc in docs]
        vectorstore = Chroma.from_documents(
            documents=all_docs,
            embedding=self.embeddings,
            collection_name=self._collection_name
            # persist_directory=self.persist_directory
        )
        return vectorstore

    def _initiate_retriever(self) -> VectorStoreRetriever:
        logger.debug("Initiating Retriever")
        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5})
        return retriever

    def _initiate_agent_chain(self) -> RunnableSerializable:
        logger.debug("Initiating Assistant")
        # TODO revoir le prompt il utilise ses propres connaissances.
        template = """Answer the question between triple single quotes based only on the following <Context/>.
        
        # Instructions
        - Respond in the same language as the question.
        - It is OK if context is not in the same language as the question.
        - DO NOT use your knowledge to answer. ONLY the context.
        - If context is empty, say you cannot answer but do not say your context is empty.
        
        <Context>
        {context}
        </Context>
        
        # Question: 
        '''{question}'''
        """
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()

        return RunnableMap({
            "context": lambda x: '\n\n'.join([doc.page_content for doc in self.retriever.invoke(x["question"])]),
            "question": lambda x: x["question"],
        }) | prompt | self.model | output_parser


class MultiDocumentRAGAgent(AbstractRAGAgent, ABC):

    def __init__(self,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 source_paths: Union[Path, List[Path]]):
        super().__init__(model=model, embeddings=embeddings, source_paths=source_paths)

        # RAG classic
        self.runnable = self._initiate_agent_chain()

    def _initiate_docs(self, source_paths: Union[Path, List[Path]]) -> Dict[Path, List[BaseNode]]:
        """Load and split documents for llama-index."""
        if isinstance(source_paths, Path):
            source_paths = [source_paths]
        else:
            source_paths = source_paths

        source_to_nodes = {}
        for path in source_paths:
            documents = SimpleDirectoryReader(input_files=[path]).load_data()
            splitter = SentenceSplitter(chunk_size=1024)
            nodes = splitter.get_nodes_from_documents(documents)
            source_to_nodes[path] = nodes

        return source_to_nodes

    def _initiate_agent_chain(self) -> RunnableSerializable:
        paper_to_tools_dict = {}
        for source, nodes in self.docs.items():
            vector_tool, summary_tool = get_doc_tools(self.embeddings, nodes, source.stem)
            paper_to_tools_dict[source] = [vector_tool, summary_tool]

        all_tools = [t for paper in self.docs for t in paper_to_tools_dict[paper]]

        obj_index = ObjectIndex.from_objects(
            all_tools,
            index_cls=VectorStoreIndex,
        )

        obj_retriever = obj_index.as_retriever(similarity_top_k=3)

        @tool
        def retriever(question: str) -> list[Any]:
            """Useful IF you need to answer a general question or need to have a holistic summary on knowledge.
            DO NOT use if you have specific question.
            DO NOT USE MULTI-ARGUMENTS INPUT."""
            return obj_retriever.retrieve(question)

        lc_tools = [retriever]

        llm_with_tools = self.model.bind_tools(lc_tools)

        # memory = MemorySaver()

        modifier = SystemMessage("You are an agent designed to answer queries over a set of given papers. "
                                 "Please always use the tools provided to answer a question. "
                                 "Do not rely on prior knowledge.")

        agent = create_react_agent(model=llm_with_tools, tools=lc_tools, state_modifier=modifier)

        return agent


class RAGAgentType(Enum):
    MULTI_DOCUMENT = "multi-document"
    SINGLE_DOCUMENT = "single-document"


class RAGAgentFactory:
    @staticmethod
    def create_agent(agent_type: RAGAgentType, **kwargs) -> AbstractRAGAgent:
        """Factory to create the appropriate RAG agent."""
        if agent_type == RAGAgentType.MULTI_DOCUMENT:
            return MultiDocumentRAGAgent(**kwargs)
        elif agent_type == RAGAgentType.SINGLE_DOCUMENT:
            return SimpleRAGAgent(**kwargs)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
