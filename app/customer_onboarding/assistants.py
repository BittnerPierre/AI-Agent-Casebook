import configparser
import logging
import sys
from typing import Optional, Annotated

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables import RunnableSerializable, RunnableWithMessageHistory
from langchain_core.tools import tool

from dotenv import load_dotenv, find_dotenv
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

from customer_onboarding.agents import FAQAgent, EligibilityAgent, ProblemSolverAgent
from customer_onboarding.commons import initiate_model, SupportedModel
from customer_onboarding.logger import setup_logger
from langgraph.checkpoint.memory import MemorySaver


logger = setup_logger(__name__, level=logging.INFO)


# TODO currently there is an issue with mistral due to reaching limit while langchain batch embeddings
default_model = SupportedModel.DEFAULT

__structured_chat_agent__ = '''Respond to the human as helpfully and accurately as possible. 
    You have access to the following tools:

    {tools}

    # DIRECTIVES
    - Only use information provided in the context. Do not respond directly to question.
    - Keep conversation as short as possible.
    - Use tools to retrieve relevant information.
    - Do NOT make any reference to tools to user.
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
    
    - For tools, always include both 'session_id' and 'input' when calling tools. 
    
    Format the action_input as:
    ```
    {{
      "session_id": "<SESSION_ID>",
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


def create_customer_onboarding_assistant(model_name: Optional[SupportedModel],
                                         faq_directory: str,
                                         problem_directory: str,
                                         persist_directory: str
                                         ) -> RunnableSerializable:
    human = '''Input: {input}
    
            Session_id: {user_session_id}

            Agent Scratchpad:
            {agent_scratchpad}
            '''

    prompt = (ChatPromptTemplate.from_messages(
        [
            ("system", __structured_chat_agent__),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human),
        ]
    ))

    llm = initiate_model(model_name)

    faq_agent = FAQAgent(model_name=default_model, faq_directory=faq_directory, persist_directory=persist_directory)

    @tool
    def faq_answerer(
        session_id: Annotated[str, "conversation session id of user"],
        input: Annotated[str, "User input which could be a question or an answer."]
    ) -> str:
        """
        Useful IF you need to answer a general question on bank products and offers.
        You must provide user session_id and user input.
        DO NOT USE MULTI-ARGUMENTS INPUT.
        """
        _chat_history = get_message_history(session_id)
        return faq_agent.answer_question(input, _chat_history.messages)

    eligibility_agent = EligibilityAgent(model_name=default_model)

    @tool
    def eligibility_checker(
            session_id: Annotated[str, "conversation session id of user"],
            input: Annotated[str, "User input which could be a question or an answer."]
        ) -> str:
        """
        Useful IF you need to determine whether a user is eligible to open a bank account.
        You must provide user session_id and user input.
        If eligibility cannot be confirmed, gracefully inform the user and suggest they contact support.
        """
        #         Do not interrupt or intervene during this process—wait for the Eligibility Agent to return a result.
        _chat_history = get_message_history(session_id)
        return eligibility_agent.answer_question(input, _chat_history.messages)

    # TODO make a real problem solver agent
    problem_solver_agent = ProblemSolverAgent(model_name=default_model,
                                              problem_directory=problem_directory,
                                              persist_directory=persist_directory)

    @tool
    def problem_solver(
            session_id: Annotated[str, "conversation session id of user"],
            input: Annotated[str, "User input which could be a question or an answer."]
    ) -> str:
        """
        Useful IF you need to solve a user problem while he is trying to open on bank account
            or subscribe to a product or service.
        You must provide user session_id and user input.
        ONLY USE if eligibility of user has been confirmed.
        DO NOT USE MULTI-ARGUMENTS INPUT.
        """
        chat_history = get_message_history(session_id)
        return problem_solver_agent.answer_question(input, chat_history.messages)

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

    lc_tools = [faq_answerer, eligibility_checker, problem_solver]

    llm.bind_tools(lc_tools)

    agent = create_structured_chat_agent(llm, lc_tools, prompt)

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
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    return customer_onboarding_assistant


def create_customer_onboarding_assistant_as_graph(model_name: Optional[SupportedModel],
                                         faq_directory: str,
                                         problem_directory: str,
                                         persist_directory: str
                                         ) -> CompiledGraph:
    human = '''Input: {input}

            Session_id: {user_session_id}

            Agent Scratchpad:
            {agent_scratchpad}
            '''

    prompt = (ChatPromptTemplate.from_messages(
        [
            ("system", __structured_chat_agent__),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human),
        ]
    ))

    llm = initiate_model(model_name)

    faq_agent = FAQAgent(model_name=default_model, faq_directory=faq_directory, persist_directory=persist_directory)

    @tool
    def faq_answerer(
            session_id: Annotated[str, "conversation session id of user"],
            user_input: Annotated[str, "User input which could be a question or an answer."]
    ) -> str:
        """
        Useful IF you need to answer a general question on bank products, offers and services.
        You must provide 'session_id' and 'user_input'.
        DO NOT USE MULTI-ARGUMENTS INPUT.
        """
        _chat_history = get_message_history(session_id)
        return faq_agent.answer_question(user_input, _chat_history.messages)

    eligibility_agent = EligibilityAgent(model_name=default_model)

    @tool
    def eligibility_checker(
            session_id: Annotated[str, "conversation session id of user"],
            user_input: Annotated[str, "User input which could be a question or an answer."]
    ) -> str:
        """
        MUST be used if you need to check ELIGIBILITY of user.
        You must provide 'session_id' and 'user_input'.
        If eligibility cannot be confirmed, gracefully inform the user and suggest to contact support.
        """
        #         Do not interrupt or intervene during this process—wait for the Eligibility Agent to return a result.
        _chat_history = get_message_history(session_id)
        return eligibility_agent.answer_question(user_input, _chat_history.messages)

    # TODO make a real problem solver agent
    problem_solver_agent = ProblemSolverAgent(model_name=default_model,
                                              problem_directory=problem_directory,
                                              persist_directory=persist_directory)

    @tool
    def problem_solver(
            session_id: Annotated[str, "conversation session id of user"],
            user_input: Annotated[str, "User input which could be a question or an answer."]
    ) -> str:
        """
        Useful IF you need to solve a user problem while he is trying to open a bank account
            or subscribe to a product or service.
        You must provide user 'session_id' and 'user_input'.
        ONLY USE if eligibility of user has been confirmed.
        DO NOT USE MULTI-ARGUMENTS INPUT.
        """
        chat_history = get_message_history(session_id)
        return problem_solver_agent.answer_question(user_input, chat_history.messages)

    lc_tools = [faq_answerer, eligibility_checker, problem_solver]

    llm.bind_tools(lc_tools)

    memory = MemorySaver()

    agent = create_react_agent(model=llm, tools=lc_tools, checkpointer=memory)

    return agent


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


if __name__ == "__main__":
    load_dotenv(find_dotenv())

    print(sys.path)

    # TODO TO REMOVE THIS IS TESTING

    config = configparser.ConfigParser()
    config.read('config.ini')
    _faq_directory = config.get('FAQAgent', 'faq_directory')
    _persist_directory = config.get('FAQAgent', 'persist_directory')
    _problem_directory = config.get('ProblemSolverAgent', 'problem_directory')

    graph = create_customer_onboarding_assistant_as_graph(model_name=SupportedModel.DEFAULT,
                                                      faq_directory=_faq_directory,
                                                      problem_directory=_problem_directory,
                                                      persist_directory=_persist_directory)

    try:
        # Generate the image bytes from the graph
        image_bytes = graph.get_graph().draw_mermaid_png()

        # Specify the filename where you want to save the image
        image_filename = "./state_graph.png"

        # Write the image bytes to the file
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)

        print(f"Graph image saved as {image_filename}")
    except Exception as e:
        print("An error occurred while generating the image:", str(e))


    chat_history = [
        HumanMessage(content="Je veux ouvrir un compte."),
        AIMessage(content="Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en France."),
        AIMessage(content="Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français."),
        AIMessage(content="Possédez-vous un compte bancaire en France ?"),
        HumanMessage(content="Oui.")
    ]

    inputs = {"messages": chat_history}
    config = {"configurable": {"thread_id": "1"}}
    print_stream(graph.stream(inputs, config=config,  stream_mode="values"))
    #
    # inputs = {"messages": [("user", "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?")]}
    # config = {"configurable": {"thread_id": "1"}}
    # print_stream(graph.stream(inputs, config=config, stream_mode="values"))
    #
    # inputs = {"messages": [("user", "Je ne reçois pas l'e-mail pour valider mon compte.")]}
    # config = {"configurable": {"thread_id": "1"}}
    # print_stream(graph.stream(inputs, config=config, stream_mode="values"))

    inputs = {"messages": [HumanMessage(content="Je ne reçois pas l'e-mail pour valider mon compte.")]}
    config = {"configurable": {"thread_id": "2"}}
    print_stream(graph.stream(inputs, config=config, stream_mode="values"))

    # assistant = create_customer_onboarding_assistant(model_name=SupportedModel.DEFAULT,
    #                                                  faq_directory=_faq_directory,
    #                                                  problem_directory=_problem_directory,
    #                                                  persist_directory=_persist_directory)
    #
    # chat_history = [
    #     HumanMessage(content="Je veux ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside en France."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Oui, je suis Français."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    #
    # session_id = '12345'
    # # message_history = get_message_history(session_id)
    # # # message_history.add_messages(chat_history)
    # #
    # # # human_msg1 = "Oui, j'ai un compte bancaire en France."
    # human_msg1 = "Je veux ouvrir un compte."
    # ai_msg_1 = assistant.invoke(input={'input': human_msg1, 'user_session_id': session_id},
    #                                                 config={'configurable': {'session_id': session_id}})
    # print(ai_msg_1)


    