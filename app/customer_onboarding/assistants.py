import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Annotated, TypedDict

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables import RunnableSerializable, RunnableWithMessageHistory, RunnableLambda
from langchain_core.tools import tool

from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from core.config_loader import load_config
from customer_onboarding.agents import FAQAgent, EligibilityAgent, ProblemSolverAgent
from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel
from core.logger import setup_logger
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph.message import add_messages, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

_ = load_dotenv(find_dotenv())

logger = setup_logger(__name__, level=logging.INFO)


_config = load_config()
# RETRIEVAL SETUP
_chroma_persist_directory = _config.get('Retrieval', 'persist_directory')
# FAQ SETUP
_faq_file = Path(_config.get('FAQAgent', 'faq_file'))

# PROBLEM SETUP
_problem_directory = _config.get('ProblemSolverAgent', 'problem_directory')
_problem_file = _config.get('ProblemSolverAgent', 'problem_file')
_problem_database = _config.get('ProblemSolverAgent', 'problem_database')

# TODO currently there is an issue with mistral due to reaching limit while langchain batch embeddings
default_model = SupportedModel.DEFAULT

model = initiate_model(default_model)
embeddings = initiate_embeddings(default_model)

__structured_chat_agent__ = '''Respond to the human as helpfully and accurately as possible. 
    You have access to the following tools:

    {tools}

    # DIRECTIVES
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

__langgraph_chat_agent__ = '''You are an customer onboarding AI chatbot for an online bank.
    Your goal is to answer questions on products and services offered by the company AND to solve issues with 
    web and mobile app during onboarding process.
    
    You respond to the user as clearly with honest, helpful and accurate answer. 
    You do not answer question not related to your main goals.
    
    # DIRECTIVES
    - NEVER respond directly to a user question and use tools to retrieve relevant information.
    - Keep conversation as short as possible.
    - Ask question to user if information is missing or if his question needs clarification.
    - Do NOT make any reference to tools to user.
    - Never mention to user: session_id, thread_id, action_name, tool_name,
        token or any internal informations used for processing conversation.
    
    # INSTRUCTIONS
    Step 1. You first greet the customer, then ask how you can help him
    Step 2. Answer his question 
    - Make sure to clarify all options to identify if its a problem with an app or a question on product and services.
    - If your answer is not satisfying, you ask for more details and clarification.
    Step 3. Asks if he has another question and answer it with the same process at Step 2.
    Step 4. Finally, if user does not have any more question, you ask for customer feedback on your service.
    
    # STYLE
    You respond in a short, conversational friendly tone.
    '''


__human__ = '''
        Input:
        {messages}

        Agent Scratchpad:
        {agent_scratchpad}
        '''


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



faq_agent = FAQAgent(model=model,
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


eligibility_agent = EligibilityAgent(model=model)

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


problem_solver_agent = ProblemSolverAgent(model=model,
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


def create_customer_onboarding_assistant_as_react_graph(model_name: Optional[SupportedModel]
                                                        ) -> CompiledGraph:

    llm = initiate_model(model_name)

    lc_tools = [faq_answerer, eligibility_checker, problem_solver]

    llm_with_tools = llm.bind_tools(lc_tools)

    memory = MemorySaver()

    prompt = ChatPromptTemplate.from_messages([
        ("system", __langgraph_chat_agent__),
        MessagesPlaceholder("messages", optional=True),
    ])

    def format_for_model(state: AgentState):
        # You can do more complex modifications here
        return prompt.invoke({"messages": state["messages"]})

    agent = create_react_agent(model=llm_with_tools, tools=lc_tools, checkpointer=memory,
                               state_modifier=format_for_model,
                               debug=True)

    return agent



class State(TypedDict):
    messages: Annotated[list, add_messages]


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def create_customer_onboarding_assistant_as_graph(model_name: Optional[SupportedModel],
                                                  ) -> CompiledStateGraph:
    # bind_tools return a new LLM as runnable
    llm = initiate_model(model_name)
    agent_tools = [faq_answerer, eligibility_checker, problem_solver]
    llm_with_tools = llm.bind_tools(agent_tools)

    def _customer_onboarding(state: State):
        messages = [
           {"role": "system", "content": __langgraph_chat_agent__},
        ] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then we route to the "tools" node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we stop (reply to the user)
        return END

    graph_builder = StateGraph(State)
    graph_builder.add_node("customer-onboarding", _customer_onboarding)
    graph_builder.add_node("faq", faq_agent)
    graph_builder.add_node("eligibility", eligibility_agent)
    graph_builder.add_node("problem", problem_solver_agent)

    tool_node = ToolNode(tools=[faq_answerer, eligibility_checker, problem_solver])  # faq_answerer
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "customer-onboarding",
        tools_condition,
    )
    graph_builder.add_edge(START, "customer-onboarding")
    graph_builder.add_edge("tools", "customer-onboarding")
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_conditional_edges("customer-onboarding", _should_continue, ["tools", END])
    graph = graph_builder.compile(checkpointer=MemorySaver())
    return graph


customer_onboarding = create_customer_onboarding_assistant_as_graph(SupportedModel.DEFAULT)


DEFAULT_ASSISTANT = "customer-onboarding"

@dataclass
class Assistant:
    description: str
    graph: CompiledStateGraph


assistants: dict[str, Assistant] = {
    "customer-onboarding": Assistant(description="A customer onboarding assistant.", graph=customer_onboarding),
}


def get_assistant(assistant_id: str) -> CompiledStateGraph:
    return assistants[assistant_id].graph



