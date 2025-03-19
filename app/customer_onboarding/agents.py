import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Union, Dict

from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableSerializable, RunnableMap
from langchain_core.tools import tool
from pydantic import BaseModel, HttpUrl

from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel
from ai_agents import AbstractAgent, SimpleRAGAgent
from core.config_loader import load_config
from core.logger import logger


_config = load_config()
_problem_directory = _config.get('ProblemSolverAgent', 'problem_directory')
_problem_database = _config.get('ProblemSolverAgent', 'problem_database')
_problem_db_path = os.path.join(_problem_directory, _problem_database)


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


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


class FAQAgent(SimpleRAGAgent):
    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 source_paths: Path,
                 ):
        super().__init__(name=name, model=model, embeddings=embeddings, source_paths=source_paths, collection_name="faq")
        # super().set_runnable(self._initiate_runnable())

    def _initiate_docs(self, source_paths: Union[Path, List[Path]]) -> Dict[Path, List[Document]]:
        source_to_docs = {}
        try:
            logger.debug("Initiating Docs")
            # Load FAQ data from JSON file
            with open(source_paths, 'r', encoding='utf-8') as file:
                faq_dict = json.load(file)
            faq_items = [FAQItem(**item) for item in faq_dict.values()]
            # Extract text from each FAQ entry to create documents
            documents = [
                Document(
                    page_content=f"Question: {item.question}\nAnswer: {item.answer}",
                    metadata={
                        "url": str(item.url),
                        "cat": item.cat,
                        "sub_cat": item.sub_cat,
                        "subsub_cat": item.subsub_cat
                    }
                )
                for item in faq_items
            ]
            source_to_docs[source_paths] = documents
        except Exception as e:
            # TODO should not silently fail.
            logger.error(f"Error loading FAQs: {e}")
            source_to_docs[source_paths] = []

        return source_to_docs


class EligibilityAgent(AbstractAgent):
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name=name, model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Eligibility Assistant")
        system_prompt = """### Contexte
        Tu es un agent chargé de déterminer si un prospect est éligible à l'ouverture d'un compte bancaire.
        Tu réponds aux instructions d'un assistant conversationnel qui traite directement avec l'utilisateur.
        
        ### Processus
        1. Pour valider l'éligibilité, il faut te transmettre le pays de résidence fiscale, la nationalité, son age et 
            vérifier si l'utilisateur possède d’un compte bancaire européen à son nom.
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

        human_prompt = '''Vérifie l'éligibilité en te basant uniquement sur les informations suivantes.
                    Nationalité: {nationalite}
                    Pays de résidence fiscale: {pays_de_residence_fiscale}
                    Est titulaire d'un compte bancaire en UE: {est_titulaire_compte_bancaire}
                    Age: {age}
                    '''

        system_message = SystemMessagePromptTemplate.from_template(
            system_prompt
        )
        human_message = HumanMessagePromptTemplate.from_template(human_prompt)
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            # MessagesPlaceholder("chat_history"),
            human_message]
        )
        output_parser = StrOutputParser()

        # Assuming eligibility questions are different; adjust as necessary
        return prompt | self.model | output_parser

    # def answer_question(self, message: str, chat_history: list[BaseMessage]) -> str:
    #     if not chat_history:
    #         chat_history = []
    #     return self.chain.invoke({"msgs": [message], "chat_history": chat_history})


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

    conn = sqlite3.connect(_problem_db_path)
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
    question: str
) -> str:
    """
    Search for errors based on description, details, diagnostic questions, or resolution by semantic similarities.
    Useful when you **DON'T** have error code to look up answer but have description of the problem.
    """
    model = initiate_model(SupportedModel.DEFAULT)
    embeddings = initiate_embeddings(SupportedModel.DEFAULT)
    vectorstore = Chroma(
        collection_name="errors",
        embedding_function=embeddings
    )
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5})

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
    chain = RunnableMap({
        "context": lambda x: '\n\n'.join([doc.page_content for doc in retriever.invoke(x["question"])]),
        "question": lambda x: x["question"],
    }) | prompt | model | output_parser

    return chain.invoke({"question": question})


class ProblemSolverAgent(SimpleRAGAgent):
    """
    Problem Solver Agent use function calling with SQLite for code error lookup within a SQLite DB
    and retrieval search from vector db.
    HYBRID database like weaviate would be a nice solution here but I wanted to showcase a SQL Query
    We don't use a RAG chain but use function calling instead.
    We are using the RAGAgent to load error_db.json and initiate the vector database that is use as tool.
    """
    def __init__(self,
                 name: str,
                 model: BaseChatModel,
                 embeddings: Embeddings,
                 persist_directory: str,
                 problem_directory: str,
                 problem_file: str = 'error_db.json',
                 ):

        self.problem_directory = Path(problem_directory)
        self.problem_file = Path(problem_file)
        self.source_paths = self.problem_directory / self.problem_file
        super().__init__(name=name, model=model, embeddings=embeddings, source_paths=self.source_paths, collection_name="errors")

    def _initiate_docs(self, source_paths: Union[Path, List[Path]]) -> Dict[Path, List[Document]]:
        source_to_docs = {}
        try:
            logger.debug("Initiating Docs")
            # Ensure the JSON file path is correct
            problem_file_path = os.path.join(self.problem_directory, self.problem_file)

            # Load data from the JSON file
            with open(problem_file_path, 'r', encoding='utf-8') as file:
                error_db = json.load(file)

                error_items = [ErrorItem(**item) for item in error_db["errors"]]

                # Extract and process each entry to create documents
                documents = [
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
                            # "search_keys": entry.search_keys
                        }
                    ) for entry in error_items
                ]
                source_to_docs[source_paths] = documents
        except Exception as e:
            # Log the error and return an empty list
            logger.error(f"Error loading error database: {e}")
            source_to_docs[source_paths] = []

        return source_to_docs

    def _initiate_runnable(self) -> RunnableSerializable:
        lc_tools = [search_errors_in_db, search_errors_in_vectordb]

        prompt = hub.pull("hwchase17/structured-chat-agent")

        agent = create_structured_chat_agent(self.model, lc_tools, prompt)
        # Create the agent executor
        agent_executor = AgentExecutor(agent=agent,
                                       tools=lc_tools,
                                       max_iterations=4,
                                       verbose=False,
                                       handle_parsing_errors=True)

        # Test the agent executor
        return agent_executor

