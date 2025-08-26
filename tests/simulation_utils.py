import functools
from typing import Annotated, Any, Callable, Dict, List, Optional, Union

from langchain_community.adapters.openai import convert_message_to_dict
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.runnables import chain as as_runnable
from langchain_openai import ChatOpenAI

from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph, START
import logging

logging.basicConfig(level=logging.DEBUG)

def langchain_to_openai_messages(messages: List[BaseMessage]):
    """
    Convert a list of langchain base messages to a list of openai messages.

    Parameters:
        messages (List[BaseMessage]): A list of langchain base messages.

    Returns:
        List[dict]: A list of openai messages.
    """

    return [
        convert_message_to_dict(m) if isinstance(m, BaseMessage) else m
        for m in messages
    ]


def create_simulated_user(
    system_prompt: str, llm: Runnable | None = None
) -> Runnable[Dict, AIMessage]:
    """
    Creates a simulated user for chatbot simulation.

    Args:
        system_prompt (str): The system prompt to be used by the simulated user.
        llm (Runnable | None, optional): The language model to be used for the simulation.
            Defaults to gpt-3.5-turbo.

    Returns:
        Runnable[Dict, AIMessage]: The simulated user for chatbot simulation.
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    ) | (llm or ChatOpenAI(model="gpt-3.5-turbo")).with_config(
        run_name="simulated_user"
    )


Messages = Union[list[AnyMessage], AnyMessage]


def add_messages(left: Messages, right: Messages) -> Messages:
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return left + right


class SimulationState(TypedDict):
    """
    Represents the state of a simulation.

    Attributes:
        messages (List[AnyMessage]): A list of messages in the simulation.
        inputs (Optional[dict[str, Any]]): Optional inputs for the simulation.
    """

    messages: Annotated[List[AnyMessage], add_messages]
    inputs: Optional[dict[str, Any]]


def create_chat_simulator(
    assistant: (
        Callable[[List[AnyMessage]], str | AIMessage]
        | Runnable[List[AnyMessage], str | AIMessage]
    ),
    simulated_user: Runnable[Dict, AIMessage],
    *,
    input_key: str,
    max_turns: int = 6,
    should_continue: Optional[Callable[[SimulationState], str]] = None,
):
    """Creates a chat simulator for evaluating a chatbot.

    Args:
        assistant: The chatbot assistant function or runnable object.
        simulated_user: The simulated user object.
        input_key: The key for the input to the chat simulation.
        max_turns: The maximum number of turns in the chat simulation. Default is 6.
        should_continue: Optional function to determine if the simulation should continue.
            If not provided, a default function will be used.

    Returns:
        The compiled chat simulation graph.

    """
    graph_builder = StateGraph(SimulationState)
    graph_builder.add_node(
        "user",
        _create_simulated_user_node(simulated_user),
    )
    graph_builder.add_node(
        "assistant", _fetch_messages | assistant | _coerce_to_message
    )
    graph_builder.add_edge("assistant", "user")
    graph_builder.add_conditional_edges(
        "user",
        should_continue or functools.partial(_should_continue, max_turns=max_turns),
    )
    # If your dataset has a 'leading question/input', then we route first to the assistant, otherwise, we let the user take the lead.
    graph_builder.add_edge(START, "assistant" if input_key is not None else "user")

    return (
        RunnableLambda(_prepare_example).bind(input_key=input_key)
        | graph_builder.compile()
    )


## Private methods


def _prepare_example(inputs: dict[str, Any], input_key: Optional[str] = None):
    if input_key is not None:
        if input_key not in inputs:
            raise ValueError(
                f"Dataset's example input must contain the provided input key: '{input_key}'.\nFound: {list(inputs.keys())}"
            )
        messages = [HumanMessage(content=inputs[input_key])]
        return {
            "inputs": {k: v for k, v in inputs.items() if k != input_key},
            "messages": messages,
        }
    return {"inputs": inputs, "messages": []}


def _invoke_simulated_user(state: SimulationState, simulated_user: Runnable):
    """Invoke the simulated user node."""
    runnable = (
        simulated_user
        if isinstance(simulated_user, Runnable)
        else RunnableLambda(simulated_user)
    )
    inputs = state.get("inputs", {})
    inputs["messages"] = state["messages"]
    return runnable.invoke(inputs)


# def _swap_roles(state: SimulationState):
#     new_messages = []
#     logging.debug(f"#### Swap Role Start ####")
#     inputs = state.get("inputs", {})
#     logging.debug(f"State Inputs: {inputs}")
#     for m in state["messages"]:
#         logging.debug(f"Message Type: {type(m)}, Message Content: {getattr(m, 'content', None)}")
#         if isinstance(m, AIMessage):
#             # tool call: [{'name': 'eligibility_checker', 'args': {'session_id': '20240423083528', 'user_input': "Il est étudiant de 17 ans et n'a pas de compte à son nom"}, 'id': '7OE3A88Lf', 'type': 'tool_call'}].
#             if isinstance(m.content, list) and any(
#                     isinstance(item, dict) and item.get("type") == "tool_call" for item in m.content
#             ):
#                 logging.debug("Ignored AIMessage with tool call type in content.")
#                 continue
#             new_messages.append(HumanMessage(content=m.content))
#         elif isinstance(m, HumanMessage):
#             new_messages.append(AIMessage(content=m.content))
#         # If m is AddableValuesDict, handle nested messages as before.
#         # Adjust import statement according to the real path for AddableValuesDict.
#         elif isinstance(m, AddableValuesDict):
#             logging.debug("Ignored AddableValuesDict type message.")
#             # Simply skip any AddableValuesDict instance
#             continue
#             # for key, value in m.items():
#             #     if isinstance(value, AIMessage):
#             #         new_messages.append(HumanMessage(content=value.content))
#             #     elif isinstance(value, HumanMessage):
#             #         new_messages.append(AIMessage(content=value.content))
#             #     elif isinstance(value, list):
#             #         for item in value:
#             #             if isinstance(item, AIMessage):
#             #                 new_messages.append(HumanMessage(content=item.content))
#             #             elif isinstance(item, HumanMessage):
#             #                 new_messages.append(AIMessage(content=item.content))
#             #             else:
#             #                 logging.debug(f"Unexpected item type in list: {type(item)}, ignoring the item.")
#             #     else:
#             #         logging.debug(f"Unexpected message type in AddableValuesDict: {type(value)}, ignoring the value.")
#         elif isinstance(m, ToolMessage):  # Assuming ToolMessage is your tool message type
#             logging.debug("Preserved ToolMessage type message.")
#             continue
#             # new_messages.append(m)  # Preserve tool messages as-is
#         else:
#             # Log and skip messages that are not AIMessage or HumanMessage
#             logging.debug(f"Ignored message type: {type(m)}")
#
#     logging.debug(f"Return messages: {new_messages}")
#     logging.debug(f"#### Swap Role END ####")
#     return {
#         "inputs": state.get("inputs", {}),
#         "messages": new_messages,
#     }

# def _swap_roles(state: SimulationState):
#     new_messages = []
#     logging.debug(f"#### Swap Role Start ####")
#     inputs = state.get("inputs", {})
#     logging.debug(f"State Inputs: {inputs}")
#
#     # Iterate over all messages
#     for m in state["messages"]:
#         logging.debug(f"Message Type: {type(m)}, Message Content: {getattr(m, 'content', None)}")
#
#         if isinstance(m, HumanMessage):
#             # Directly adding HumanMessage to new messages
#             # new_messages.append(AIMessage(content=m.content))
#             continue
#         elif isinstance(m, AIMessage):
#             # Adding AIMessage if it does not contain a tool call
#             continue
#             # if not (isinstance(m.content, list) and any(isinstance(item, dict) and item.get("type") == "tool_call" for item in m.content)):
#             #     new_messages.append(HumanMessage(content=m.content))
#
#         elif isinstance(m, AddableValuesDict):
#             # Properly handling AddableValuesDict
#             logging.debug("Processing AddableValuesDict type message.")
#             for item in m.get("messages", []):
#                 if isinstance(item, HumanMessage):
#                     new_messages.append(AIMessage(content=item.content))
#                 elif isinstance(item, AIMessage):
#                     # if not any(
#                     #     isinstance(call, dict) and call.get("type") == "tool_call"
#                     #     for call in item.additional_kwargs.get("tool_calls", [])
#                     # ):
#                     #     new_messages.append(HumanMessage(content=item.content))
#                     if isinstance(item.content, list) and any(
#                             isinstance(item2, dict) and item.get("type") == "tool_call" for item2 in item.content
#                     ):
#                         logging.debug("Ignored AIMessage with tool call type in content.")
#                         continue
#                     new_messages.append(HumanMessage(content=item.content))
#                 # Continue preserving logic for other possible messages, like ToolMessage
#         elif isinstance(m, ToolMessage):
#             logging.debug("Ignored ToolMessage type message.")
#             continue
#         else:
#             logging.debug(f"Ignored message type: {type(m)}")
#
#     logging.debug(f"Return messages: {new_messages}")
#     logging.debug(f"#### Swap Role END ####")
#     return {
#         "inputs": state.get("inputs", {}),
#         "messages": new_messages,
#     }

def _swap_roles(state: SimulationState):
    new_messages = []
    logging.debug("#### Swap Role Start ####")
    inputs = state.get("inputs", {})
    logging.debug(f"State Inputs: {inputs}")

    for m in state["messages"]:
        logging.debug(f"Message Type: {type(m)}, Message Content: {getattr(m, 'content', None)}")

        if isinstance(m, HumanMessage):
            if m.content.strip():
                new_messages.append(AIMessage(content=m.content))
            else:
                logging.debug("Ignored HumanMessage with empty content.")

        elif isinstance(m, AIMessage):
            # Check if it's a tool call and skip if it is
            if hasattr(m, 'tool_calls') and m.tool_calls:
                logging.debug("Ignored AIMessage that is a tool call.")
                continue

            if m.content.strip():
                new_messages.append(HumanMessage(content=m.content))
            else:
                logging.debug("Ignored AIMessage with empty content.")

        elif isinstance(m, ToolMessage):
            if m.content.strip():
                new_messages.append(HumanMessage(content=m.content))
            else:
                logging.debug("Ignored ToolMessage with empty content.")

        # elif isinstance(m, AddableValuesDict):
        #     messages = m.get("messages", [])
        #     if messages and messages[0].content == (new_messages[-1].content if new_messages else ""):
        #         messages = messages[1:]
        #     logging.debug(f"Processing AddableValuesDict type message. Messages: {messages}")
        #     for item in messages:
        #         if isinstance(item, HumanMessage) and item.content.strip():
        #             new_messages.append(AIMessage(content=item.content))
        #         elif isinstance(item, AIMessage):
        #             if (not hasattr(item, 'tool_calls') or not item.tool_calls) and item.content.strip():
        #                 new_messages.append(HumanMessage(content=item.content))
        #             else:
        #                 logging.debug("Ignored AIMessage with tool call or empty content.")
        #         elif isinstance(item, ToolMessage) and item.content.strip():
        #             new_messages.append(HumanMessage(content=item.content))

        else:
            logging.debug(f"Ignored message type: {type(m)}")

    logging.debug(f"Return messages: {new_messages}")
    logging.debug("#### Swap Role END ####")
    return {
        "inputs": state.get("inputs", {}),
        "messages": new_messages,
    }


@as_runnable
def _fetch_messages(state: SimulationState):
    """Invoke the simulated user node."""
    return state["messages"]


def _convert_to_human_message(message: BaseMessage):
    return {"messages": [HumanMessage(content=message.content)]}


def _create_simulated_user_node(simulated_user: Runnable):
    """Simulated user accepts a {"messages": [...]} argument and returns a single message."""
    return (
        _swap_roles
        | RunnableLambda(_invoke_simulated_user).bind(simulated_user=simulated_user)
        | _convert_to_human_message
    )


def _coerce_to_message(assistant_output: str | BaseMessage):
    if isinstance(assistant_output, str):
        return {"messages": [AIMessage(content=assistant_output)]}
    else:
        return {"messages": [assistant_output]}


def _should_continue(state: SimulationState, max_turns: int = 6):
    messages = state["messages"]
    # TODO support other stop criteria
    if len(messages) > max_turns:
        return END
    elif messages[-1].content.strip() == "FINISHED":
        return END
    else:
        return "assistant"