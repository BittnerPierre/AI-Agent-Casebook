import abc
import json
import os
import sqlite3
from typing import Optional, List

from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable, Runnable, RunnableMap
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from pydantic import BaseModel, HttpUrl

from customer_onboarding.commons import SupportedModel, initiate_model, initiate_embeddings
from customer_onboarding.logger import logger

_RAG_AGENT_DEFAULT_COLLECTION_NAME = "ragagent"


class FAQItem(BaseModel):
    url: HttpUrl
    cat: str
    sub_cat: str
    subsub_cat: str
    question: str
    answer: str


class ErrorItem(BaseModel):
    code: str
    category: str
    subcategory: str
    description: str
    details: str
    diagnostic_questions: List[str]
    resolution: str
    search_keys: List[str]


class RunnableMixin:
    def __init__(self):
        self.chain = None

    def invoke(self, input_data):
        """Implementation for invoking the agent."""
        return self.chain.invoke(input_data) if self.chain else None


class AbstractAgent(abc.ABC, RunnableMixin):

    def __init__(self, model_name: Optional[SupportedModel] = None):
        """
        Initialize the AbstractAgent.

        :param model_name: Type of the language model to use.
        """
        super().__init__()
        self.model_name = model_name
        self.model = self._initiate_model()

    def _initiate_model(self) -> Optional[BaseChatModel]:
        return initiate_model(self.model_name)

    @abc.abstractmethod
    def _initiate_agent_chain(self) -> RunnableSerializable:
        pass

    @property
    def runnable_chain(self) -> Optional[Runnable]:
        """Expose a property to get the chain if available."""
        return self.chain

    @abc.abstractmethod
    def answer_question(self, message: str, chat_history: List[BaseMessage]) -> str:
        pass

    def invoke(self, input_data):
        """Implement the Runnable interface to support invocation."""
        return self.chain.invoke(input_data) if self.chain else None


class RAGAgent(AbstractAgent):

    # TODO add a in memory vectorstore...
    def __init__(self,
                 model_name: Optional[SupportedModel],
                 collection_name: Optional[str],
                 persist_directory: str):
        super().__init__(model_name=model_name)
        self._collection_name = collection_name or _RAG_AGENT_DEFAULT_COLLECTION_NAME
        self.persist_directory = persist_directory
        # RAG classic
        self.embeddings = self._initiate_embeddings()
        self.docs = self._initiate_docs()
        self.vectorstore = self._initiate_vectorstore()
        self.retriever = self._initiate_retriever()
        self.chain = self._initiate_agent_chain()

    def _initiate_embeddings(self) -> Optional[Embeddings]:
        return initiate_embeddings(self.model_name)

    @abc.abstractmethod
    def _initiate_docs(self) -> Optional[List[Document]]:
        pass

    def _initiate_vectorstore(self) -> VectorStore:
        logger.debug("Initiating VectorStore")
        # TODO check consistency with embedding, model and vectorstore
        # TODO memory only one
        # TODO check existing file to avoir reload (code above does not work an create an empty vectore store
        vectorstore = Chroma.from_documents(
            documents=self.docs,
            embedding=self.embeddings,
            collection_name=self._collection_name
            # persist_directory=self.persist_directory
        )

        # try:
        #     logger.debug("Checking existing VectorStore for persistence")
        #     persistent_client = PersistentClient(path=self.persist_directory)
        #     vectorstore = Chroma(client=persistent_client, collection_name="my_collection",
        #                          embedding_function=self.embeddings)
        #     logger.info("Loaded existing vectorstore")
        # except Exception as e:
        #     logger.debug("Existing VectorStore not found or initialization failed, creating a new one")
        #     vectorstore = Chroma.from_documents(
        #         documents=self.docs,
        #         embedding=self.embeddings,
        #         persist_directory=self.persist_directory
        #     )
        #    logger.info("Created and persisted new vectorstore")
        return vectorstore

    def _initiate_retriever(self) -> VectorStoreRetriever:
        logger.debug("Initiating Retriever")
        retriever = self.vectorstore.as_retriever()
        return retriever

    def _initiate_agent_chain(self) -> RunnableSerializable:
        logger.debug("Initiating Assistant")
        # TODO revoir le prompt il utilise ses propres connaissances.
        template = """Answer the question based only on the following context:
        {context}

        Question: 
        {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        return RunnableMap({
            "context": lambda x: self.retriever.invoke(x["question"]),
            "question": lambda x: x["question"],
        }) | prompt | self.model | output_parser

    def answer_question(self, message: str, chat_history: List[BaseMessage]) -> str:
        if not chat_history:
            chat_history = []
        return self.chain.invoke({"input": message, "chat_history": chat_history})


class FAQAgent(RAGAgent):
    def __init__(self,
                 model_name: Optional[SupportedModel],
                 persist_directory: str,
                 faq_directory: str,
                 ):

        self.faq_directory = faq_directory
        super().__init__(model_name=model_name, collection_name="faq", persist_directory=persist_directory)

    def _initiate_docs(self) -> list[Document]:
        try:
            logger.debug("Initiating Docs")
            # Ensure the JSON file path is correct
            faq_file_path = os.path.join(self.faq_directory, 'faq.json')

            # Load FAQ data from JSON file
            with open(faq_file_path, 'r', encoding='utf-8') as file:
                faq_dict = json.load(file)

            faq_items = [FAQItem(**item) for item in faq_dict.values()]

            # Extract text from each FAQ entry to create documents
            return [Document(page_content=f"Question: {item.question}\nAnswer: {item.answer}",
                             metadata={"url": str(item.url), "cat": item.cat, "sub_cat": item.sub_cat,
                                       "subsub_cat": item.subsub_cat}) for item in faq_items]
        except Exception as e:
            # TODO should not silently failed.
            logger.error(f"Error loading FAQs: {e}")
            return []



class EligibilityAgent(AbstractAgent):
    def __init__(self, model_name: Optional[SupportedModel] = None):
        super().__init__(model_name=model_name)
        self.chain = self._initiate_agent_chain()

    def _initiate_agent_chain(self) -> RunnableSerializable:
        logger.debug("Initiating Eligibility Assistant")
        system_prompt = """### Contexte
        Tu es un agent chargé de déterminer si un prospect est éligible à l'ouverture d'un compte bancaire.
        Tu donnes des instructions à un assistant conversationnel qui traite directement avec l'utilisateur.
        
        ### Processus
        1. Pour valider l'éligibilité, il faut te transmettre le pays de résidence fiscale, la nationalité et 
            vérifier si l'utilisateur possède d’un compte bancaire français à son nom.
        2. Si on vous fournit des informations partielles, répondez par les informations manquante.
        3. Une fois TOUTES les informations transmises, tu vérifies les critères d'éligibilités:
            - Si une condition ne correspond pas aux règles métier d'éligibilité,
             terminez la conversation par "Non éligible. " e, expliquant pourquoi.
             - Si le prospect répond à l'ensemble des critères d'éligibilité et uniquement si,
             termine la conversation par "Eligible". 
        
        ### Critères d'éligibilités
        - Les nationalités éligibles sont celles de l'Union Européenne.
        - Les pays de résidences autorisés sont ceux de l'Union Européenne.
        - Le demandeur doit déjà être titulaire d'un compte bancaire en France à son nom.
        - Seules les personnes majeures peuvent ouvrir un compte.
        
        ### Exploration des chemins
        - Vérifiez les critères d'éligibilité qu'à condition de connaitre
            le pays de résidence, la nationalité et la détention d'un compte bancaire français.
       
        ### Dialogue simulé
        Utilisateur: "Je veux ouvrir un compte."
        Assistant: "Pour valider l'éligibilité, il faut me transmettre le pays de résidence fiscale,
            la nationalité du demandeur et vérifier que l'utilisateur possède d’un compte bancaire français à son nom."
        Utilisateur: "Je réside au Canada, je ne suis de nationalité Française"
        Assistant: "Avez-vous un compte en France à votre nom?"
        Utilisateur: Oui, j'ai un compte en France à mon nom."
        Assistant: "Non éligible. Cette offre est réservée aux personnes de nationalité française."
        """

        system_message = SystemMessagePromptTemplate.from_template(
            system_prompt
        )
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder("chat_history"),
            ("placeholder", "{msgs}")]
        )
        output_parser = StrOutputParser()

        # Assuming eligibility questions are different; adjust as necessary
        return prompt | self.model | output_parser

    def answer_question(self, message: str, chat_history: list[BaseMessage]) -> str:
        if not chat_history:
            chat_history = []
        return self.chain.invoke({"msgs": [message], "chat_history": chat_history})


@tool
def search_errors_in_db(
    code: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search_keys: Optional[str] = None,
    limit: int = 20,
) -> List[dict]:
    """
    Search for errors based on code, category, subcategory, or search keys.
    Useful when you **DO** have error code to look up answer and no description of error.

    Args:
    - code (Optional[str]): The error code to search for.
    - category (Optional[str]): The error category to search for.
    - subcategory (Optional[str]): The error subcategory to search for.
    - search_keys (Optional[str]): The search keys to search for.
    - limit (int): The maximum number of results to return.

    Returns:
    - List[dict]: A list of dictionaries representing the matching errors.
    """
    conn = sqlite3.connect('data/parsed/error_db.sqlite')
    cursor = conn.cursor()

    query = "SELECT * FROM errors WHERE 1 = 1"
    params = []

    if code:
        query += " AND code = ?"
        params.append(code)
    if category:
        query += " AND category = ?"
        params.append(category)
    if subcategory:
        query += " AND subcategory = ?"
        params.append(subcategory)
    if search_keys:
        query += " AND search_keys LIKE ?"
        params.append(f"%{search_keys}%")

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results


@tool
def search_errors_in_vectordb(
    problem: str
) -> str:
    """
    Search for errors based on description, details, diagnostic questions, or resolution by semantic similarities.
    Useful when you **DON'T** have error code to look up answer but have description of the problem.
    """
    model = initiate_model(SupportedModel.DEFAULT)

    vectorstore = Chroma(
        collection_name="errors"
    )
    retriever = vectorstore.as_retriever()

    template = """Answer the question based only on the following context:
            {context}

            Question: 
            {question}
            """
    prompt = ChatPromptTemplate.from_template(template)
    output_parser = StrOutputParser()
    chain = RunnableMap({
        "context": lambda x: retriever.invoke(x["question"]),
        "question": lambda x: x["question"],
    }) | prompt | model | output_parser

    return chain.invoke(problem)

# HYBRID database like weaviate would be a nice solution.
class ProblemSolverAgent(RAGAgent):

    def __init__(self,
                 model_name: Optional[SupportedModel],
                 persist_directory: str,
                 problem_directory: str,
                 ):

        self.problem_directory = problem_directory
        super().__init__(model_name=model_name, collection_name="errors", persist_directory=persist_directory)

    def _initiate_docs(self) -> Optional[List[Document]]:
        try:
            logger.debug("Initiating Docs")
            # Ensure the JSON file path is correct
            error_db_file_path = os.path.join(self.problem_directory, 'error_db.json')

            # Load data from the JSON file
            with open(error_db_file_path, 'r', encoding='utf-8') as file:
                error_db = json.load(file)

                error_items = [ErrorItem(**item) for item in error_db["errors"]]

                # Extract and process each entry to create documents
                return [
                    Document(
                        page_content=(
                            f"Code: {entry.code}\n"
                            f"Category: {entry.category}\n"
                            f"Subcategory: {entry.subcategory}\n"
                            f"Description: {entry.description}\n"
                            f"Details: {entry.details}\n"
                            f"Diagnostic Questions: {', '.join(entry.diagnostic_questions)}\n"
                            f"Resolution: {entry.resolution}\n"
                            f"Search Keys: {', '.join(entry.search_keys)}"
                        ),
                        metadata={
                            "code": entry.code,
                            "category": entry.category,
                            "subcategory": entry.subcategory,
                            #"search_keys": entry.search_keys
                        }
                    ) for entry in error_items
                ]

        except Exception as e:
            # Log the error and return an empty list
            logger.error(f"Error loading error database: {e}")
            return []

    def _initiate_agent_chain(self) -> RunnableSerializable:
        lc_tools = [search_errors_in_db, search_errors_in_vectordb]

        prompt = hub.pull("hwchase17/structured-chat-agent")

        agent = create_structured_chat_agent(self.model, lc_tools, prompt)
        # Create the agent executor
        agent_executor = AgentExecutor(agent=agent, tools=lc_tools, verbose=True, handle_parsing_errors=True)

        # Test the agent executor
        return agent_executor
