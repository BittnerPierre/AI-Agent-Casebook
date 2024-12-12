import configparser
import uuid
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.pregel.io import AddableValuesDict
from langsmith import Client, evaluate, aevaluate

from langchain_openai import ChatOpenAI

from customer_onboarding.assistants import create_customer_onboarding_assistant_as_react_graph, \
    create_customer_onboarding_assistant_as_chain
from customer_onboarding.commons import SupportedModel
from simulation.simulation_utils import create_simulated_user

from simulation.simulation_utils import create_chat_simulator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

import logging

logging.basicConfig(level=logging.DEBUG)


_ = load_dotenv(find_dotenv())

dataset_name = "CUSTOMER-ONBOARDING-datasets-03-12-2024"
client = Client()

app = create_customer_onboarding_assistant_as_chain(model_name=SupportedModel.DEFAULT)


def assistant(messages: list, config: Optional[RunnableConfig] = None) -> str:
    try:
        new_messages = []

        for m in messages:
            # should not occur anymore. Was happening because I was sending val and not val["output"]
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
        return val["output"]

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
    return {"score": 1 if result.did_succeed else 0, "comment": result.reasoning}


system_prompt_template = """As a part of a Quality Assurance effort,
you are tasked with role playing as a potential customer of an online bank company.

You are interacting with an AI customer support agent that aims to assist prospects to open a bank account or answer FAQs.

Instructions for this conversation: {instructions}

You will start the conversation, and respond with your next message as the customer.
When you have a good and clear answer, finish politely the conversation.

Do not ask any follow-up questions even if you are invited to by the conversational agent.

Suppose you are using a 'chat' interface like WhatsApp, Discord, or Slack. Keep sentences short.

Give short and clear answers to questions and follow the guidelines given by the assistant.
If the assistant suggests an action that needs to be done offline or asynchronously,
close the conversation.

When you are finished with the conversation, respond with a single word 'FINISHED'.

If the action can be done immediately, simulate that you do it successfully.

Do not break character in role-playing as a customer, or give away that you yourself are an AI.

Additionally, ensure that the AI assistant does not ask for any personal information or follow-up questions."""


def test_customer_onboarding():
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
    # experiment_name = results.experiment_name
    # print(experiment_name)
    # resp = client.read_project(project_name=results.experiment_name, include_stats=True)
    # print(resp.json(indent=2))
    # average_score = resp.feedback_stats["did_succeed"]["avg"]
    # assert average_score > 0.8, f"Average feedback score is {average_score}, which is below the threshold of 0.8"

