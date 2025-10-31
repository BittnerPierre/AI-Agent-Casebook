import asyncio
from typing import List
from agents import gen_trace_id, trace, SQLiteSession
from langchain_core.messages import BaseMessage
from openevals.simulators import create_llm_simulated_user, run_multiturn_simulation
from openevals.types import ChatCompletionMessage
from openevals import create_llm_as_judge
from langchain_community.adapters.openai import convert_message_to_dict
from my_agents.agents import run_onboarding_agent_with_mcp
from agents import OpenAIConversationsSession
from evals_utils import format_evaluation_report

# Create a session instance with a session ID
session = OpenAIConversationsSession()

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

def my_app(inputs: ChatCompletionMessage, *, thread_id: str, **kwargs):
    output = "3.11 is greater than 3.9."
    # TODO this is not working
    # When using session memory, provide only a string input to append to the conversation
    user_input = inputs['content']
    print(f"➡️ {user_input}")
    result = asyncio.run(run_onboarding_agent_with_mcp(user_input, session))
    output = result.final_output
    print(f"⬅️ {output}")
    return {"role": "assistant", "content": output, "id": result.last_response_id}

user = create_llm_simulated_user(
    system="""You are a user who wants to open a new account. 
        You are French, 25 years old, and you have a bank account in France (LCL) in your name.
        You are a resident of France (Dunkerque).
        You are using the mobile application to open a new account.
        You are stucked at the confirmation email step that you didn't receive.
        You are asking for help to solve this issue.
        You talk to an ai chatbot. As a human, you can make typo time to time as you were writing on a mobile phone.
        You say nothing at the end of the conversation.
        You say nothing at the end of the conversation: no thank you, no goodbye, no nothing.
        """,
    model="openai:gpt-4.1-mini",
    fixed_responses=[
        {"role": "user", "content": "I want to open a new account."},
    ],
)

trajectory_evaluator = create_llm_as_judge(
    model="openai:gpt-4o-mini",
    prompt="Based on the below conversation, has the user's needs have been satisfied?\n{outputs}",
    feedback_key="satisfaction",
)

trace_id = gen_trace_id()
with trace("Customer Onboarding", trace_id=trace_id):
    print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")

    # Run the simulation directly with the customized user function
    simulator_result = run_multiturn_simulation(
        app=my_app,
        user=user,
        trajectory_evaluators=[trajectory_evaluator],
        max_turns=7,
    )


success = format_evaluation_report(simulator_result)