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


def my_app(inputs: ChatCompletionMessage, *, thread_id: str, **kwargs):
    # When using session memory, provide only a string input to append to the conversation
    user_input = inputs['content']
    print(f"➡️ {user_input}")
    result = asyncio.run(run_onboarding_agent_with_mcp(user_input, session))
    output = result.final_output
    print(f"⬅️ {output}")
    return {"role": "assistant", "content": output, "id": result.last_response_id}

user = create_llm_simulated_user(
    system="""You are a user who wants to open a new account via the mobile application. 
        You are using an ai chatbot inside the application to help you finalize your onboarding process.
        You have confirmed your email address but you want to apply the discount code 'TEST2' at the payment step.
        You have already filled your profile informations (age, nationality, bank, city, country) in the application and don't want to tell it to a bot.
        If the agent asks you for your profile informations, you must refuse but you have to share your name or email in the conversation
         so it can lookup your profile in the system.
        You don't ask to check your user profile by yourself.
        If the bot insists to get your personal informations (age, nationality, bank account, city, country),
         you ask him to check back office or CRM to retrieve your profile informations.
        If and only if the chat bot asks you, you can confirm that your bank account is in France and in your name and that your tax residence is in France.
        Tax residence, bank account location or bank account ownership are not known by the agent or the CRM so it is legit to ask those questions.
        Your email is 'marc.lefevre+test2@example.com'.
        Your name is 'Marc Lefévre'.
        You talk in french.
        You are using in a small chat interface so you don't thank the agent at each turn.
        As a human, you can make typo time to time as you are typing on a mobile phone.
        You terminate the conversation quickly, you don't insist and avoid chitchat: no thank you, no goodbye, no nothing.
        You don't ask additional questions.
        """,
    model="openai:gpt-4.1-mini",
    fixed_responses=[
        {"role": "user", "content": ("Bonjour, je n'arrive pas à finaliser mon inscription. Pouvez-vous m'aider ?")},
    ],
)

satifsaction_evaluator = create_llm_as_judge(
    model="openai:gpt-4o-mini",
    prompt="Based on the below conversation, has the user's get an answer to his question?\n{outputs}",
    feedback_key="satisfaction",
)

trajectory_evaluator = create_llm_as_judge(
    model="openai:gpt-4o-mini",
    prompt="Based on the conversation, does the user give its personal informations (age, nationality, bank, city, country) to the bot? "
    "Tax residence, bank account location and bank account ownership are not known by the agent or the CRM so it is legit to ask those questions.\n{outputs}",
    feedback_key="no_profile_informatio_given",
)

trace_id = gen_trace_id()
with trace("Customer Onboarding", trace_id=trace_id):
    print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")

    # Run the simulation directly with the customized user function
    simulator_result = run_multiturn_simulation(
        app=my_app,
        user=user,
        trajectory_evaluators=[satifsaction_evaluator, trajectory_evaluator],
        max_turns=7,
    )




# Utilisez cette fonction à la place du print simple
success = format_evaluation_report(simulator_result)