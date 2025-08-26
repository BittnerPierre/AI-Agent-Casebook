from pathlib import Path
from typing import Optional, Annotated

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable, RunnableWithMessageHistory
from langchain_core.tools import tool

from app.core.base import SupportedModel
from app.core.commons import initiate_model, initiate_embeddings
from app.core.config_loader import load_config
from app.core.logger import get_logger
from app.customer_onboarding.agents import ProblemSolverAgent, FAQAgent, EligibilityAgent

_ = load_dotenv(find_dotenv())

logger = get_logger()


_config = load_config()


# RETRIEVAL SETUP
_chroma_persist_directory = _config.get('Retrieval', 'persist_directory')
# FAQ SETUP
_faq_file = Path(_config.get('FAQAgent', 'faq_file'))

# PROBLEM SETUP
_problem_directory = _config.get('ProblemSolverAgent', 'problem_directory')
_problem_file = _config.get('ProblemSolverAgent', 'problem_file')
_problem_database = _config.get('ProblemSolverAgent', 'problem_database')

# Model
_default_model = _config.get('CustomerOnboarding', 'model', fallback="MISTRAL_SMALL")

# TODO currently there is an issue with mistral due to reaching limit while langchain batch embeddings
default_model = SupportedModel[_default_model]

model = initiate_model(default_model)
embeddings = initiate_embeddings(default_model)


faq_agent = FAQAgent(name="FAQAgent", 
                     model=model,
                     embeddings=embeddings,
                     source_paths=_faq_file
                     )

@tool
def faq_answerer(
        input: Annotated[str, "User input which could be a question or an answer."]
) -> str:
    """
    Useful IF you need to answer a general question on bank products, offers and services.
    You must provide 'input'.
    DO NOT USE MULTI-ARGUMENTS INPUT.
    """
    return faq_agent.invoke(input={"question": input})


eligibility_agent = EligibilityAgent(name="EligibilityAgent", model=model)

@tool
def eligibility_checker(
        nationality: Annotated[str, "Nationality"],
        country_of_tax_residence: Annotated[str, "Country of Tax Residence"],
        has_an_european_bank_account: Annotated[bool, "Has an European bank account"],
        age: Annotated[int, "Age"],
) -> str:
    """
    MUST be used to check ELIGIBILITY.
    You must provide 'nationality', 'country_of_tax_residence', 'est_titulaire_compte_bancaire'.
    If eligibility cannot be confirmed, gracefully inform the user and suggest to contact support.
    """
    return eligibility_agent.invoke(input={"nationalite": nationality,
                                           "pays_de_residence_fiscale": country_of_tax_residence,
                                           "est_titulaire_compte_bancaire": has_an_european_bank_account,
                                           "age": age})


problem_solver_agent = ProblemSolverAgent(name="ProblemSolverAgent",
                                          model=model,
                                          embeddings=embeddings,
                                          problem_directory=_problem_directory,
                                          persist_directory=_chroma_persist_directory,
                                          problem_file=_problem_file)

@tool
def problem_solver(
        input: Annotated[str, "User input which could be a question or an answer."]
) -> str:
    """
    YOU MUST CHECK eligibility of user FIRST.
    Useful to solve a problem with application.
    You must provide user input.
    DO NOT USE MULTI-ARGUMENTS INPUT.
    """
    # TODO session_id and message handling should disappear
    return problem_solver_agent.invoke(input={"input": [input]})

    # THIS IS NOT WORKING : TypeError: 'RunnableSequence' object is not callable
    # faq_answerer = faq_agent.runnable_chain().as_tool(
    #     name="faq_answerer",
    #     description="Useful IF you need to solve a user problem while he is trying to open on bank account.",
    #     arg_types={"session_id": str, "input": str}
    # )
    # eligibility_checker = eligibility_agent.runnable_chain().as_tool(
    #     name = "eligibility_checker",
    #     description="Useful IF you need to solve a user problem while he is trying to open on bank account.",
    #     arg_types={ "session_id": str, "input": str }
    # )



# Dictionary to store chat histories per session ID
session_histories = {}


def get_message_history(session_id: str) -> BaseChatMessageHistory:
    # return SQLChatMessageHistory(session_id, "sqlite:///memory.db")
    if session_id not in session_histories:
        session_histories[session_id] = InMemoryChatMessageHistory()

        # Clean up unwanted messages from chat history
    clean_messages = [
        message for message in session_histories[session_id].messages
        if not (isinstance(message,
                           AIMessage) and "Agent stopped due to iteration limit or time limit." in message.content)
    ]
    session_histories[session_id].messages = clean_messages
    return session_histories[session_id]



def create_customer_onboarding_assistant_as_chain(model_name: Optional[SupportedModel],
                                                  ) -> RunnableSerializable:

    llm = initiate_model(model_name)
    lc_tools = [faq_answerer, eligibility_checker, problem_solver]
    llm_with_tools = llm.bind_tools(lc_tools)

    prompt = (ChatPromptTemplate.from_messages(
        [
            ("system", __structured_chat_agent__),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", __human__),
        ]
    ))

    agent = create_structured_chat_agent(llm_with_tools, lc_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=lc_tools,
        handle_parsing_errors=
        "Check your output and make sure it includes an action that conforms to the expected format (json blob)!"
        " Do not output an action and a final answer at the same time."
    )
    customer_onboarding_assistant = RunnableWithMessageHistory(
        agent_executor,
        get_message_history,
        input_messages_key="messages",  # CHANGED HERE INPUT TO MESSAGES FOR LANGGRAPH COMPATIBILITY
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    return customer_onboarding_assistant


__human__ = '''
        Input:
        {messages}

        Agent Scratchpad:
        {agent_scratchpad}
        '''

__structured_chat_agent__ = '''Respond to the human as helpfully and accurately as possible. 
    You have access to the following tools:

    {tools}

    # DIRECTIVES
    - CRITICAL: Before calling any tool, ensure you have ALL required information.
    - If ANY required information is missing, ask the user for it FIRST.
    - NEVER call tools with empty or invalid parameters.
    - For eligibility_checker, you need: nationality, country_of_tax_residence, has_an_european_bank_account, age
    - Only call tools when you have complete, valid information.
    - Only use information provided in the context. Do not respond directly to question.
    - Keep conversation as short as possible.
    - Use tools to retrieve relevant information.
    - Do NOT make any reference to tools to user.
    - Ask question to user if information are missing.
    - Do NOT give session_id, action_name, tool_name, token or any internal informations used for processing conversation.
    - ALWAYS includes a valid json blob to give the next action. No exceptions.
    - If a tool asked for additional information from user, "action" is "Final Answer" and
     "action_input" is the information needed by the tool that you have to ask to user.
    - Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

    Format is Action:```$JSON_BLOB``` then Observation
    
    - ALWAYS return a valid JSON blob, even when providing the final answer to the user.
    
    - For final answers, the JSON blob must include:
    ```
    {{
      "action": "Final Answer",
      "action_input": "Final response to human"
    }}
    
    - For tools, always include 'input' when calling tools. 
    
    Format the action_input as:
    ```
    {{
      "input": "<USER_INPUT>"
    }}
    ```
    
    Valid "action" values: "Final Answer" or {tool_names}

    Provide only ONE action per $JSON_BLOB, as shown:
    ```
    {{
      "action": $TOOL_NAME,
      "action_input": $INPUT
    }}
    ```

    # EXAMPLE
    Question: input question to answer
    Thought: consider previous and subsequent steps
    Action:
    ```
    $JSON_BLOB
    ```
    Observation: action result
    ... (repeat Thought/Action/Observation N times)
    Thought: I know what to respond
    Action:
    ```
    {{
      "action": "Final Answer",
      "action_input": "Final response to human"
    }}
    ```
    '''
