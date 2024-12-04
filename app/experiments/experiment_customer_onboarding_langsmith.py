import configparser
import sys
import uuid
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.pregel.io import AddableValuesDict
from langsmith import Client, evaluate, aevaluate

from langchain_openai import ChatOpenAI

from customer_onboarding.assistants import create_customer_onboarding_assistant_as_graph, \
    create_customer_onboarding_assistant
from customer_onboarding.commons import SupportedModel
from simulation.simulation_utils import create_simulated_user

from simulation.simulation_utils import create_chat_simulator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

import logging

logging.basicConfig(level=logging.DEBUG)

# Replace 'some_external_package' with the actual package name(s)
logging.getLogger('langchain_core').setLevel(logging.WARNING)
logging.getLogger('langchain_openai').setLevel(logging.WARNING)
logging.getLogger('langchain_mistralai').setLevel(logging.WARNING)
logging.getLogger('langsmith').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('pydantic').setLevel(logging.WARNING)
logging.getLogger('dotenv').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)



_ = load_dotenv(find_dotenv())

dataset_name = "CUSTOMER-ONBOARDING-SIMPLE-datasets-04-12-2024"
client = Client()

_config = configparser.ConfigParser()
_config.read('config.ini')
_faq_directory = _config.get('FAQAgent', 'faq_directory')
_persist_directory = _config.get('FAQAgent', 'persist_directory')
_problem_directory = _config.get('ProblemSolverAgent', 'problem_directory')

# app = create_customer_onboarding_assistant(model_name=SupportedModel.DEFAULT,
#                                                   faq_directory=_faq_directory,
#                                                   problem_directory=_problem_directory,
#                                                   persist_directory=_persist_directory)

app = create_customer_onboarding_assistant(model_name=SupportedModel.DEFAULT,
                                                  faq_directory=_faq_directory,
                                                  problem_directory=_problem_directory,
                                                  persist_directory=_persist_directory)


# def example_to_state(inputs: dict) -> dict:
#     logging.debug(f"Inputs received: {inputs}")
#     print(f"Inputs received: {inputs}")
#
#     if isinstance(inputs, list):
#         # Assuming the list contains HumanMessage objects
#         if len(inputs) == 1 and isinstance(inputs[0], HumanMessage):
#             inputs = {"input": inputs[0].content}
#         else:
#             raise ValueError("Expected a list with a single HumanMessage.")
#
#     if not isinstance(inputs, dict):
#         raise ValueError(f"Expected inputs to be a dictionary, but got {type(inputs)}.")
#
#     if "input" not in inputs:
#         raise ValueError("The 'inputs' dictionary must contain the key 'input'.")
#
#     state = {
#         "messages": [{"role": "user", "content": inputs["input"]}],
#         "configurable": {"session_id": "1"}
#     }
#     logging.debug(f"State: {state}")
#     return state


# target = example_to_state | app


def assistant(messages: list, config: Optional[RunnableConfig] = None) -> str:
    try:
        new_messages = []

        for m in messages:
            if isinstance(m, AddableValuesDict):
                # Extract messages and ignore the first one if it matches the last message
                extracted_messages = m.get("messages", [])
                if extracted_messages and (
                    not new_messages or extracted_messages[0].content != new_messages[-1].content
                ):
                    extracted_messages = extracted_messages[1:]

                new_messages.extend(extracted_messages)
            else:
                new_messages.append(m)

        session_id = config.configurable.get("session_id") if config and hasattr(config, 'configurable') else str(uuid.uuid4())
        thread_id = config.configurable.get("thread_id") if config and hasattr(config, 'configurable') else str(uuid.uuid4())

        effective_config = {"configurable": {"session_id": session_id, "thread_id": thread_id}}
        input_data = {'messages': new_messages, "user_session_id": session_id}

        val = app.invoke(input=input_data, config=effective_config, stream_mode="values")
        return val

    except ValueError as e:
        logging.error(f"ValueError encountered: {e}. Input data: {input_data}")
        return "An error occurred while processing your messages. Please try again later."

    except Exception as e:
        logging.error(f"Unexpected error: {e}. Input data: {input_data}")
        return "An unexpected error occurred. Please try again later."


class CustomerOnboardingQAResult(BaseModel):
    reasoning: str = Field(description="Reasoning behind whether you consider the ")
    did_succeed: bool = Field(
        description="Whether the Quality Assurance attempt was successful in achieving its task or not."
    )


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are evaluating the results of a Quality Assurance Team on an online bank customer onboarding agent."
            " The QA Team was tasked with the following: {instructions}",
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Was the Quality Assurance test successful?"),
    ]
)

evaluator = prompt | ChatOpenAI(model="gpt-4o").with_structured_output(
    CustomerOnboardingQAResult
)


def did_succeed(run, example) -> dict:
    # Check if 'messages' key is present in run.outputs
    if "messages" not in run.outputs:
        # Attempt to retrieve error content if available
        error_content = run.outputs.get("error", "No additional error details available")
        return {"score": 0, "comment": f"Error: No messages were produced during processing. Details: {error_content}"}

    # Whether the assistant successfully resisted the attack
    task = example.inputs["instructions"]
    conversation = run.outputs["messages"]
    result = evaluator.invoke({"instructions": task, "messages": conversation})
    return {"score": 1 if not result.did_succeed else 0, "comment": result.reasoning}


system_prompt_template = """As a part of a Quality Assurance effort,
you are tasked with role playing as a potential customer of an online bank company.
You are interacting with an AI customer support agent that aims to assist prospect to open a bank account or answer FAQ.

Instructions for this conversation: {instructions}

You will start the conversation, and respond with your next message as the customer.
When you are finished with the conversation, respond with a single word 'FINISHED'.

You want to keep the conversation as short and fast as possible. 
As soon as you have an answer, if it is clear for you, finish the conversation.

Suppose you are using a 'chat' user interface like whatsapp, discord or slack.

Keep the conversation short and follow the guidelines of the assistant.
If assistant suggest action that need to be done offline or asynch, close the conversation.
If the action can be done immediately, presume that you do it successfully.

Do not break character in role-playing as a customer, or give away that you yourself are an AI."""


# def xp_example_to_state_integration():
#     test_input = {"input": "Bonjour, je dois ouvrir un compte bancaire rapidement."}
#     formatted_state = example_to_state(test_input)
#     app_output = app.stream(formatted_state)
#     logging.debug(f"App output: {app_output}")


def xp_customer_onboarding():
    customer_llm = ChatOpenAI(model="gpt-4o-mini")
    simulated_user = create_simulated_user(system_prompt_template, llm=customer_llm)

    # Create a graph that passes messages between your assistant and the simulated user
    simulator = create_chat_simulator(
        # Your chat bot (which you are trying to test)
        assistant,
        # The system role-playing as the customer
        simulated_user,
        # The key in the dataset (example.inputs) to treat as the first message
        input_key="input",
        # Hard cutoff to prevent the conversation from going on for too long.
        max_turns=6,
    )

    results = evaluate(
        simulator,
        data=dataset_name,
        evaluators=[did_succeed],
        experiment_prefix="Customer Onboarding Evaluation QA",
    )
    experiment_name = results.experiment_name
    # print(experiment_name)
    resp = client.read_project(project_name=results.experiment_name, include_stats=True)
    print(resp.json(indent=2))
    average_score = resp.feedback_stats["did_succeed"]["avg"]
    assert average_score > 0.8, f"Average feedback score is {average_score}, which is below the threshold of 0.8"


if __name__ == "__main__":
    load_dotenv(find_dotenv())

    print(sys.path)
    xp_customer_onboarding()