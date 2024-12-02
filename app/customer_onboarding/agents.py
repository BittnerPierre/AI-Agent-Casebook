import abc
import json
import os
from typing import Optional, List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable, Runnable, RunnableMap
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from pydantic import BaseModel, HttpUrl

from customer_onboarding.commons import SupportedModel, initiate_model, initiate_embeddings
from customer_onboarding.logger import logger


class FAQItem(BaseModel):
    url: HttpUrl
    cat: str
    sub_cat: str
    subsub_cat: str
    question: str
    answer: str


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
                 persist_directory: str):
        super().__init__(model_name=model_name)
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


class FAQAgent(RAGAgent):
    def __init__(self,
                 model_name: Optional[SupportedModel],
                 persist_directory: str,
                 faq_directory: str,
                 ):

        self.faq_directory = faq_directory
        super().__init__(model_name=model_name, persist_directory=persist_directory)

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

    def answer_question(self, message: str, chat_history: List[BaseMessage]) -> str:
        if not chat_history:
            chat_history = []
        return self.chain.invoke({"question": message, "chat_history": chat_history})


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


class ProblemSolverAgent(AbstractAgent):
    def __init__(self, model_name: Optional[SupportedModel]):
        super().__init__(model_name)

    def answer_question(self, message: HumanMessage, chat_history: List[BaseMessage]) -> str:
        # Check if eligibility has been confirmed in the chat history
        eligibility_confirmed = any(
            "Final Answer. Je confirme l'éligibilité" in message.content for message in chat_history
        )

        if not eligibility_confirmed:
            return ("Final Answer: L'éligibilité n'a pas été confirmée. "
                    "Veuillez compléter la vérification d'éligibilité avant de poser des questions sur l'ouverture de compte.")

        # Provide an answer only if the question relates to account opening problems after eligibility is confirmed
        response = self.model.chat([HumanMessage(content="Répond au problème lié à l'ouverture de compte: " + message.content)])
        return response.content
