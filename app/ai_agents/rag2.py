# app/agents/rag.py (modified version)
import abc
from abc import ABC
from enum import Enum
from typing import Optional, List, Any, Union, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable, RunnableMap
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from llama_index.core.agent.runner.base import BaseAgentRunner

from ai_agents.base import AbstractAgent, Input, Output
from semantic_search.core import SearchStrategy
from core.logger import logger


class AbstractRAGAgent(AbstractAgent):
    """Base class for all RAG agents"""

    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 search_strategy: SearchStrategy):
        super().__init__(name=name, model=model)
        self.search_strategy = search_strategy


class SimpleRAGAgent(AbstractRAGAgent):
    """Simple RAG agent that uses a search strategy"""

    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 search_strategy: SearchStrategy):
        super().__init__(name=name, model=model, search_strategy=search_strategy)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Assistant")
        template = """Answer the question between the XML <Question> tag based only on the content
         within the following <Context/> XML tag.
        Ignore any other input outside the tags.
        
        # Instructions
        - Respond in the same language as the question.
        - It is OK if context is not in the same language as the question.
        - DO NOT use your knowledge to answer. ONLY the context.
        - If context is empty, say you cannot answer but do not say your context is empty.
        
        <Context>
        {context}
        </Context>
        
        <Question> 
        {question}
        </Question>
        """
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()

        def get_context(x):
            results = self.search_strategy.retrieve(x["question"])
            if hasattr(results[0], 'page_content') if results else False:
                # Handle langchain Document objects
                return '\n\n'.join([doc.page_content for doc in results])
            else:
                # Handle other types of results
                return '\n\n'.join([str(doc) for doc in results])

        return RunnableMap({
            "context": get_context,
            "question": lambda x: x["question"],
        }) | prompt | self.model | output_parser


class MultiDocumentRAGAgent(AbstractRAGAgent):
    """RAG agent that uses tool-based search strategy for multiple documents"""

    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 search_strategy: SearchStrategy):
        super().__init__(name=name, model=model, search_strategy=search_strategy)
        self._agent_runner = self._initiate_agent()

    def _initiate_agent(self) -> BaseAgentRunner:
        # For MultiDocumentIndexStrategy, we need to access the underlying retriever
        if not hasattr(self.search_strategy, 'retriever') or self.search_strategy.retriever is None:
            raise ValueError("The search strategy does not have an initialized retriever")

        agent_worker = FunctionCallingAgentWorker.from_tools(
            tool_retriever=self.search_strategy.retriever,
            system_prompt=""" \
        You are an agent designed to answer queries over a set of given papers.
        Please always use the tools provided to answer a question. Do not rely on prior knowledge.\
        """,
            verbose=True
        )
        return AgentRunner(agent_worker)

    def invoke(self, input: Input, **kwargs: Any) -> Output:
        response = self._agent_runner.query(input)
        return response


class RAGAgentType(Enum):
    MULTI_DOCUMENT = "multi-document"
    SINGLE_DOCUMENT = "single-document"


class RAGAgentFactory:
    @staticmethod
    def create_agent(agent_type: RAGAgentType,
                   model: BaseChatModel,
                   search_strategy: SearchStrategy,
                   name: Optional[str] = None) -> AbstractRAGAgent:
        """Factory to create the appropriate RAG agent."""
        agent_name = name or f"{agent_type.value}-agent"

        if agent_type == RAGAgentType.MULTI_DOCUMENT:
            return MultiDocumentRAGAgent(name=agent_name, model=model, search_strategy=search_strategy)
        elif agent_type == RAGAgentType.SINGLE_DOCUMENT:
            return SimpleRAGAgent(name=agent_name, model=model, search_strategy=search_strategy)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")