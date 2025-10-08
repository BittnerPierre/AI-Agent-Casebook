
from math import e
import asyncio

from getpass import getpass
from dotenv import load_dotenv, find_dotenv

from agents import Agent, Runner

import openai
from openai.types.responses import ResponseTextDeltaEvent

from openai.types.vector_store import ExpiresAfter
from pydantic import BaseModel

from agents import function_tool

from agents import FileSearchTool

from agents.mcp import MCPServerSse, MCPServerStdio
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings

from agents import (
    GuardrailFunctionOutput,
    RunContextWrapper,
    input_guardrail
)

from dataclasses import dataclass
from typing import Optional


from openai import AsyncOpenAI, OpenAI

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from openai.types.responses import (
    ResponseFunctionCallArgumentsDeltaEvent,  # tool call streaming
    ResponseCreatedEvent,  # start of new event like tool call or final answer
)

from .oauth import oauth


_ = load_dotenv(find_dotenv())


########################################################
# Global Variables
########################################################

client = OpenAI()

########################################################
# Global Schema
########################################################

@dataclass
class UserProfile:  
    nationality: str | None = None
    age: int | None = None
    has_eu_bank_account: bool | None = None
    is_elligible: bool | None = None

########################################################
# OAuth
########################################################




########################################################
# Global Functions
########################################################


async def process_stream_events(response):
    """
    Process and print stream events from an agent response.
    
    Args:
        response: The response object containing stream events
    """
    async for event in response.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseFunctionCallArgumentsDeltaEvent):
                # this is streamed parameters for our tool call
                print(event.data.delta, end="", flush=True)
            elif isinstance(event.data, ResponseTextDeltaEvent):
                # this is streamed final answer tokens
                print(event.data.delta, end="", flush=True)
        elif event.type == "agent_updated_stream_event":
            # this tells us which agent is currently in use
            print(f"> Current Agent: {event.new_agent.name}")
        elif event.type == "run_item_stream_event":
            # these are events containing info that we'd typically
            # stream out to a user or some downstream process
            if event.name == "tool_called":
                # this is the collection of our _full_ tool call after our tool
                # tokens have all been streamed
                print()
                if hasattr(event.item.raw_item, 'name'):
                    print(f"> Tool Called, name: {event.item.raw_item.name}")
                else:
                    print(f"> Tool Called, name: ResponseFileSearchToolCall")
            elif event.name == "tool_output":
                # this is the response from our tool execution
                print(f"> Tool Output: {event.item.raw_item['output']}")


########################################################
# Knowledge Base
########################################################


# Product & Services FAQ

faq_vector_store_id = None
problem_vector_store_id = None

vector_stores = client.vector_stores.list()
for vector_store in vector_stores:
    # if (vector_store.name == "Support FAQ" or vector_store.name == "Problem Database"):
    #     print(f"deleting vector store : '{vector_store.id}'")
    #     try:
    #         client.vector_stores.delete(vector_store.id)
    #         print(f"vector store '{vector_store.name}' deleted")
    #     except openai.NotFoundError as e:
    #         print(f"error deleting vector store '{vector_store.name}': {e}")

    # FAQ Database
    if vector_store.name == "Support FAQ":
        faq_vector_store_id = vector_store.id

    # Problem Database
    if vector_store.name == "Problem Database":
        problem_vector_store_id = vector_store.id

# FAQ Database

if not faq_vector_store_id:
    faq_vector_store = client.vector_stores.create(        # Create vector store
        name="Support FAQ",
        expires_after=ExpiresAfter(anchor="last_active_at", days=1)
    )
    client.vector_stores.files.upload_and_poll(        # Upload file
        vector_store_id=faq_vector_store.id,
        file=open("./experiments/customer_onboarding/faq.json", "rb")
    )
else:
    faq_vector_store = client.vector_stores.retrieve(faq_vector_store_id)

# Problem Database

if not problem_vector_store_id:
    problem_vector_store = client.vector_stores.create(        # Create vector store
        name="Problem Database",
        expires_after=ExpiresAfter(anchor="last_active_at", days=1)
    )

    client.vector_stores.files.upload_and_poll(        # Upload file
        vector_store_id=problem_vector_store.id,
        file=open("./experiments/customer_onboarding/error_db.json", "rb")
    )
else:
    problem_vector_store = client.vector_stores.retrieve(problem_vector_store_id)



########################################################
# Test Knowledge Base
########################################################


# user_query = "How do I change my card PIN?"

# results = client.vector_stores.search(
#     vector_store_id=vector_store.id,
#     query=user_query,
# )
# print(results)


# user_query = "I've forgotten my PIN"

# results = client.vector_stores.search(
#     vector_store_id=vector_store_problem.id,
#     query=user_query,
# )
# print(results)

########################################################
# Tools
########################################################


# Eligibility Agent


@function_tool
def update_eligibility(context: RunContextWrapper[UserProfile], nationality: str, age: int, has_eu_bank_account: bool, is_elligible: bool) -> str:
    """
    Update the eligibility status of the user.
    Args:
    - nationality: nationality (e.g., 'French', 'Belgian', etc.).
    - age: age in years.
    - has_eu_bank_account: True/False if the user already has
    a bank account in an EU country.
    - is_elligible: True/False if the user is eligible to open an account.
    """
    print(f"Eligibility status verified from user input '{nationality}', '{age}', '{has_eu_bank_account}'. Status is {is_elligible}.")
    context.context.nationality = nationality
    context.context.age = age
    context.context.has_eu_bank_account = has_eu_bank_account
    context.context.is_elligible = is_elligible
    assert context.context.is_elligible is not None, "Eligibility status is required"
    return f"Eligibility status verified from user input '{nationality}', '{age}', '{has_eu_bank_account}'. Status is {is_elligible}."



@function_tool
def eligibility_checker(
    context: RunContextWrapper[UserProfile]
) -> str:
    """
    Checks if eligibility  to open an account has been verifieed.

    Return: a text indicating "Eligible" or "Not Eligible".
    """

    # Règles simplifiées, vous adaptez à la réalité
    # 1. Être majeur (>=18 ans)
    # 2. Être de nationalité d'un pays de l'UE (on se limite à un set)
    # 3. Posséder déjà un compte bancaire dans l'UE


    if context.context.is_elligible is None:
        return "Eligibility status not verified. Need Verification"
    elif context.context.is_elligible:
        return "Eligible"
    else:
        return "Non Eligible"

########################################################
# Guardrails
########################################################

# Sensitive Data Guardrail

# define structure of output for any guardrail agents
class GuardrailOutput(BaseModel):
    is_triggered: bool
    reasoning: str

# define an agent that checks if user is asking about political opinions
sensitive_data_agent = Agent(
    name="Sensitive data check",
    instructions="Check if the user is sharing sensitive financial data such as credit card numbers, CVV codes, IBAN numbers, or full account numbers",
    output_type=GuardrailOutput,
)

# this is the guardrail function that returns GuardrailFunctionOutput object
@input_guardrail
async def sensitive_data_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    # run agent to check if guardrail is triggered
    response = await Runner.run(starting_agent=sensitive_data_agent, input=input)
    # format response into GuardrailFunctionOutput
    return GuardrailFunctionOutput(
        output_info=response.final_output,
        tripwire_triggered=response.final_output.is_triggered,
    )


########################################################
# Create Agents
########################################################

def _create_agents_with_mcp(server) -> Agent[UserProfile]:
    # FAQ Agent
    faq_agent = Agent(
        name="FAQ Agent",
        instructions="You help answer questions about offers and services using the provided FileSearchTool.",
        tools=[
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=[faq_vector_store.id],
            ),
        ],
    )

    # Eligibility Agent
    eligibility_agent = Agent[UserProfile](
        name="Eligibility agent",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}            
            You are an agent in charge of determining if a prospect is eligible to open a bank account.
            
            ### Process
            1. To validate eligibility, you need to be provided with the country of tax residence, nationality, age and
                verify if the user has a European bank account in their own name.
            2. If partial information is provided, respond with the missing information.
            3. Once ALL information is transmitted, verify the eligibility criteria:
                - If a condition does not meet business eligibility rules,
                end the conversation with "Not eligible. " and explain why.
                - If the prospect meets all eligibility criteria and only if so,
                end the conversation with "Eligible".
            4. Use the update eligibility tool to update the eligibility of the user.
            
            ### Eligibility Criteria
            - Eligible nationalities are those of the European Union.
            - Authorized countries of residence are those of the European Union.
            - The applicant must already have a bank account in France in their name.
            - Only adults can open an account.
            
            ### Path Exploration
            - Only verify eligibility criteria when you know
                the country of residence, nationality and possession of a French bank account.
        
            ### Simulated Dialogue
            User: "I want to open an account."
            Assistant: "To validate eligibility, I need the country of tax residence,
                the applicant's nationality and verify that the user has a French bank account in their name."
            User: "I live in Canada, I am French nationality"
            Assistant: "Do you have an account in France in your name?"
            User: "Yes, I have an account in France in my name."
            Assistant: "Not eligible. This offer is reserved for people of French nationality.""",
        tools=[update_eligibility]
    )

    # Problem Solver Agent
    problem_solver_agent = Agent[UserProfile](
        name="Problem solver agent",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are an AI agent in charge of solving problems encountered by users of an online bank mobile and web applications.
        You only reply if elligibility has been verified.
        Use eligibility checker tool to verify eligibility.
        """,
        tools=[
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=[problem_vector_store.id],
            ),
            eligibility_checker
        ],
    )

    # Customer Onboarding Agent
    mcp_servers = [server] if server is not None else []

    customer_onboarding_agent = Agent[UserProfile](
        name="Customer onboarding assistant",
        instructions=(
            "You are an AI assistant in charge of customer onboarding for an online bank.\n"
            "You answer questions about offers and services and solve issues.\n"
            "You have to verify prospect's eligibility before solving problem and issues.\n"
            "If they ask about product and services, handoff to the FAQ agent.\n"
            "If they ask about problem and issues, handoff to the Problem solver agent.\n"
            "You can use hubspot tools to search crm objects 'crm.objects.contacts.read' via email or name (if available) to get additional contact information (age, nationalite, banque, ville, pays) and fill the user profile.\n"
            "Answer by a single sentence whenever possible."
        ),
        input_guardrails=[sensitive_data_guardrail],  # note this is a list of guardrails
        handoffs=[faq_agent, eligibility_agent, problem_solver_agent],
        mcp_servers=mcp_servers,
    )
    return customer_onboarding_agent

def create_agent() -> Agent[UserProfile]:
    """
    Create the customer onboarding agent without MCP server.
    The MCP server should be initialized when running the agent.
    """
    return _create_agents_with_mcp(None)


async def run_agent_with_mcp(agent: Agent[UserProfile], conversation: list[dict[str, str]], context: UserProfile = None):
    """
    Run the agent with HubSpot MCP server connection.

    Args:
        agent: The agent to run
        conversation: The conversation history
        context: Optional user profile context

    Returns:
        The agent run result
    """
    token = await oauth()

    mcp_hubspot_server = MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={
            "url": "https://mcp.hubspot.com",
            "headers": {"Authorization": f"Bearer {token["access_token"]}"},
            "timeout": 10
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    )

    async with mcp_hubspot_server as server:
        print("✅ Serveur MCP HubSpot connecté avec succès")

        # Update agent's MCP servers
        agent.mcp_servers = [server]

        # Run the agent
        if context is None:
            context = UserProfile()

        result = await Runner.run(agent, conversation, context=context)
        return result

########################################################
# Run Agents
########################################################


async def run_onboarding_agent(conversation: list[dict[str, str]]):
    try:

        token = await oauth()

        mcp_hubspot_server = MCPServerStreamableHttp(
            name="Streamable HTTP Python Server",
            params={
                "url": "https://mcp.hubspot.com",
                "headers": {"Authorization": f"Bearer {token["access_token"]}"},
                "timeout": 10
            },
            cache_tools_list=True,
            max_retry_attempts=3,
        )

        async with mcp_hubspot_server as server:
            print("✅ Serveur MCP HubSpot connecté avec succès")
            customer_onboarding_agent = _create_agents_with_mcp(server)

            context = UserProfile()

            # conversation = [
            #     {"role": "user", "content": "Salut, je suis Allemande, j'ai 25 ans et j'ai déjà un compte en France. Je réside fiscalement en France. Je veux ouvrir un compte bancaire."
            #     "Mais je ne recois pas l'email de confirmation. Comment puis-je résoudre ce problème ?"}
            # ]

            result = await Runner.run(customer_onboarding_agent, conversation, context=context)
            print(result.final_output)

    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de l'agent: {e}")
        raise


