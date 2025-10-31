from math import e
import asyncio

from getpass import getpass
from dotenv import load_dotenv, find_dotenv

from agents import Agent, Runner, SessionABC

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
    name: str | None = None
    email: str | None = None
    nationality: str | None = None
    bank: str | None = None
    city: str | None = None
    country: str | None = None
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
        file=open("./faq.json", "rb")
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
        file=open("./error_db.json", "rb")
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
def update_user_profile(context: RunContextWrapper[UserProfile], nationality: str, age: int, has_eu_bank_account: bool, name: str, email: str, bank: str, city: str, country: str) -> str:
    """
    Update the user profile.
    Args:
    - nationality: nationality (e.g., 'French', 'Belgian', etc.).
    - age: age in years.
    - has_eu_bank_account: True/False if the user already has
    a bank account in an EU country.
    - name: name of the user.
    - email: email of the user.
    - bank: bank of the user.
    - city: city of the user.
    - country: country of the user.
    """
    print(f"User profile updated with '{nationality}', '{age}', '{has_eu_bank_account}', '{name}', '{email}', '{bank}', '{city}', '{country}'.")
    if nationality is not None and nationality.strip():
        context.context.nationality = nationality
    if age is not None and str(age).strip():
        context.context.age = age
    if has_eu_bank_account is not None and str(has_eu_bank_account).strip():
        context.context.has_eu_bank_account = has_eu_bank_account
    if name is not None and name.strip():
        context.context.name = name
    if email is not None and email.strip():
        context.context.email = email
    if bank is not None and bank.strip():
        context.context.bank = bank
    if city is not None and city.strip():
        context.context.city = city
    if country is not None and country.strip():
        context.context.country = country
    return f"User profile updated with '{nationality}', '{age}', '{has_eu_bank_account}'."


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

    # Customer Onboarding Agent
    mcp_servers = [server] if server is not None else []

    # FAQ Agent
    faq_agent = Agent(
        name="FAQ Agent",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You help answer questions about offers and services using the provided FileSearchTool.
        If user asks about solving problems and issues, you must not reply.
        Answer by a single sentence whenever possible. Be polite and professional.
        """,
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

            You don't solve problems and issues or answer user questions on products and services.
            You only verify eligibility of the user.

            Check user profile to avoid asking questions that are already answered.

            If not, use hubspot tools to search in crm objects 'crm.objects.contacts.read' with email 
            or name to get the required contact information (`age`, `nationalite`, `banque`, `ville` and `pays`) and update the user profile.
            Additional hubspot fields are in french. You must NOT translate them to english.

            If you retrieve missing informations from hubspot, you must use update user profile tool to update the user profile.
            
            ### Process
            0. Check hubspot or user profile to avoid asking questions that are already answered.
            1. To validate eligibility, you need to be provided with nationality, age and
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
            - The applicant must already have a French bank account (such as BNP Paribas, Crédit Mutuel, Société Générale, Crédit Agricole, etc.) in their own name.
            - Only adults can open an account.
            
            ### Path Exploration
            - Only verify eligibility criteria when you know
                the country of residency, nationality and possession of a French bank account.
        
            ### Simulated Dialogue
            User: "I want to open an account."
            Assistant: "To validate eligibility, I need the country of residency,
                the applicant's nationality and verify that the user has a French bank account in their name."
            User: "I live in Canada, I am French nationality"
            Assistant: "Do you have a bank account in France in your name?"
            User: "Yes, I have an account in France in my name."
            Assistant: "Not eligible. This offer is reserved for people of French nationality.""",
        tools=[update_eligibility, update_user_profile],
        mcp_servers=mcp_servers,
    )

    # Problem Solver Agent
    problem_solver_agent = Agent[UserProfile](
        name="Problem solver agent",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are an AI agent in charge of solving problems encountered by users of an online bank mobile and web applications.
        You only reply if elligibility of user has been verified.
        If user is not eligible, you must not answer.
        If user asks about product and services, you must not answer.
        Use eligibility checker tool to verify eligibility of user.
        If eligibility has not been verified yet, you must not answer.
        Answer by a single sentence whenever possible. Be polite and professional.
        """,
        tools=[
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=[problem_vector_store.id],
            ),
            eligibility_checker
        ],
    )

    customer_onboarding_agent = Agent[UserProfile](
        name="customer_onboarding_agent",
        instructions=(
            "You are an AI assistant called `Elliott` in charge of customer onboarding for an online bank.\n"
            "You answer questions about offers and services and solve onboarding issues.\n"
            "First introduce yourself, greet the user, and explain how you can help them.\n"
            "Identify if the user has a question about products and services or onboarding problems and issues.\n"
            "If user's question is unclear, ask for more details.\n"
            "If user has problems and issues with onboarding, clarify if it is on mobile or web.\n"
            "You NEVER answer user questions or verify eligibility by yourself. You must use the appropriate tools to help you.\n"
            "\n\n"
            "When verifying eligibility, you, as the customer_onboarding_agent, must use the eligibility_agent tool to request and obtain necessary information.\n" 
            "Do not ask any eligibility questions directly to the user unless you are explicitly prompted to do so by the eligibility_agent tool.\n" 
            "This rule applies: you must use eligibility_agent to determine what eligibility questions to ask before presenting any eligibility-related question to a user.\n"
            "\n\n"
            "If user question is about products and services, use FAQ agent tool.\n"
            "If user has onboarding problems or issues, use problem solver agent tool.\n"
            "\n\n"
            "# Eligibility Process\n"
            "User's eligibility must be verified (i.e., `Eligible`) before using the problem solver agent tool.\n"
            "Use eligibility agent tool to verify eligibility.\n"
            "Do not ask questions directly to the user; instead, use the eligibility agent tool to request and obtain the necessary information.\n"
            "Only ask the user questions if prompted to do so by the eligibility agent tool—treat the eligibility agent tool as the expert that knows what is needed for eligibility checking,\n" 
            " and rely on it to provide the questions that should be presented to the user until the process is fully completed (user profile `is_eligible` is not None).\n"
            # "If additional informations are needed to verify eligibility, ask the user for the missing information "
            # " and use eligibility agent tool again until eligibility process is fully completed (user profile is eligible is True).\n"
            "You must never refer to the eligibility process in your answer to user as it for regulatory compliance.\n"
            "\n\n"
            "# User Profile\n\n"
            "If user says that he has already fill its personal informations in the application form and don't want to give it again,\n" 
            "ask him its name or email so you can retrieve it by yourself and update its user profile with the update user profile tool.\n"
            "Use hubspot tools to search in crm objects 'crm.objects.contacts.read' with email " 
            "or name to get the required contact information (`age`, `nationalite`, `banque`, `ville` and `pays`) and update the user profile.\n"
            "Additional hubspot fields are in **french**. You must NOT translate them to english.\n"
            "\n\n"
            "# Tone and Style \n\n"
            "Answer by a single sentence whenever possible. Be polite and professional.\n"
            "Answer in the same language as the user's question.\n"
            "You try to reduce the number of turns to answer the user's request.\n"
            "Terminate the conversation quickly when done and avoid chitchat.\n"
            "If user insist while you have already answered his question, you terminate the conversation politely.\n"
            "If you cannot find an answer to user's issue, you tell him that must contact the customer support."
        ),
        input_guardrails=[sensitive_data_guardrail],  # note this is a list of guardrails
        tools=[
            eligibility_agent.as_tool(tool_name="eligibility_agent", tool_description="Check if the user is eligible to open an account"),
            faq_agent.as_tool(tool_name="faq_agent", tool_description="Answer questions about products and services"),
            problem_solver_agent.as_tool(tool_name="problem_solver_agent", tool_description="Solve onboarding problems and issues"),
            update_user_profile
        ],
        mcp_servers=mcp_servers,
        #handoffs=[faq_agent, problem_solver_agent],
    )
    return customer_onboarding_agent


#### Grader
# 1. Identify the agent and its rules: customer_onboarding_agent must use eligibility_agent for eligibility and must not ask the user questions directly unless prompted by the eligibility tool.
# Rule applies: must use eligibility_agent before asking eligibility questions.
# 2. Review the first assistant response to the user.
# Assistant asked directly: “pourriez-vous me préciser si vous êtes majeur (18 ans ou plus) ?” without any preceding eligibility_agent tool call.
# 3. Check for any tool invocation preceding that question.
# No eligibility_agent (or other dedicated tool) was used before the eligibility question.
# 4. Assess subsequent behavior.
# Eligibility tool was used later, but the initial violation already occurred.
#### Grader

# async def create_agent() -> tuple[Agent[UserProfile], UserProfile]:
#     """
#     Create the customer onboarding agent without MCP server.
#     The MCP server should be initialized when running the agent.
#     """
#     try:

#         token = await oauth()

#         mcp_hubspot_server = MCPServerStreamableHttp(
#             name="Streamable HTTP Python Server",
#             params={
#                 "url": "https://mcp.hubspot.com",
#                 "headers": {"Authorization": f"Bearer {token['access_token']}"},
#                 "timeout": 10
#             },
#             cache_tools_list=True,
#             max_retry_attempts=3,
#         )

#         async with mcp_hubspot_server as server:
#             print("✅ Serveur MCP HubSpot connecté avec succès")
#             customer_onboarding_agent = _create_agents_with_mcp(server)

#             context = UserProfile()

#             return customer_onboarding_agent, context

#     except Exception as e:
#         print(f"❌ Erreur lors de l'exécution de l'agent: {e}")
#         raise



# async def run_agent_with_mcp(agent: Agent[UserProfile], conversation: list[dict[str, str]], context: UserProfile = None):
#     """
#     Run the agent with HubSpot MCP server connection.

#     Args:
#         agent: The agent to run
#         conversation: The conversation history
#         context: Optional user profile context

#     Returns:
#         The agent run result
#     """
#     token = await oauth()

#     mcp_hubspot_server = MCPServerStreamableHttp(
#         name="Streamable HTTP Python Server",
#         params={
#             "url": "https://mcp.hubspot.com",
#             "headers": {"Authorization": f"Bearer {token["access_token"]}"},
#             "timeout": 10
#         },
#         cache_tools_list=True,
#         max_retry_attempts=3,
#     )

#     async with mcp_hubspot_server as server:
#         print("✅ Serveur MCP HubSpot connecté avec succès")

#         # Update agent's MCP servers
#         agent.mcp_servers = [server]

#         # Run the agent
#         if context is None:
#             context = UserProfile()

#         result = await Runner.run(agent, conversation, context=context)
#         return result

########################################################
# Run Agents
########################################################


async def run_onboarding_agent_with_mcp(conversation: list[dict[str, str]], session: SessionABC = None):
    try:

        token = await oauth()

        mcp_hubspot_server = MCPServerStreamableHttp(
            name="Streamable HTTP Python Server",
            params={
                "url": "https://mcp.hubspot.com",
                "headers": {"Authorization": f"Bearer {token['access_token']}"},
                "timeout": 10
            },
            cache_tools_list=True,
            max_retry_attempts=3,
        )

        async with mcp_hubspot_server as server:
            # print("✅ Serveur MCP HubSpot connecté avec succès")
            customer_onboarding_agent = _create_agents_with_mcp(server)

            context = UserProfile()

            result = await Runner.run(customer_onboarding_agent, conversation, context=context, session=session)

            return result

    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de l'agent: {e}")
        raise



async def run_onboarding_agent_streamed(server, conversation: list[dict[str, str]]):
    """
    Run the onboarding agent with streaming support and MCP server.
    Returns a StreamedRunResult that can be used with stream_events().
    """

    print("✅ Serveur MCP HubSpot connecté avec succès (streaming)")
    customer_onboarding_agent = _create_agents_with_mcp(server)
    context = UserProfile()

    # Return the streamed result (not awaited)
    return Runner.run_streamed(customer_onboarding_agent, conversation, context=context)


def run_onboarding_agent(server, conversation: list[dict[str, str]]):
    """
    Run the onboarding agent with MCP server.
    Returns a RunResult that can be used with stream_events().
    """

    print("✅ Serveur MCP HubSpot connecté avec succès")
    customer_onboarding_agent = _create_agents_with_mcp(server)

    context = UserProfile()

    # Return the streamed result (not awaited)
    return Runner.run(customer_onboarding_agent, conversation, context=context)