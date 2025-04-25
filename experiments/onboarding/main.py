from __future__ import annotations
import asyncio
import os
from agents import Runner, Agent
from agents import function_tool

from openai.types.responses import (
    ResponseFunctionCallArgumentsDeltaEvent,  # tool call streaming
    ResponseCreatedEvent,  # start of new event like tool call or final answer
    ResponseTextDeltaEvent
)

from agents import (
    GuardrailFunctionOutput,
    RunContextWrapper,
    input_guardrail
)

from pydantic import BaseModel


from agents.extensions.models.litellm_model import LitellmModel


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


@function_tool
def eligibility_checker(
    nationality: str,
    age: int,
    has_eu_bank_account: bool
) -> str:
    """
    Checks if the user is eligible to open an account.

    - nationality: nationality (e.g., 'French', 'Belgian', etc.).
    - age: age in years.
    - has_eu_bank_account: True/False if the user already has
    a bank account in an EU country.

    Return: a text indicating "Eligible" or "Not Eligible".
    """

    # Règles simplifiées, vous adaptez à la réalité
    # 1. Être majeur (>=18 ans)
    # 2. Être de nationalité d'un pays de l'UE (on se limite à un set)
    # 3. Posséder déjà un compte bancaire dans l'UE

    EU_NATIONALITIES = {
        "française", "francais", "french", "belgium", "belge", "allemande", "german", "italienne", "italian",
        "espagnole", "spanish", "portugaise", "luxembourgeoise",  # etc.
    }

    # Convertir pour simplifier la comparaison
    nat_lower = nationality.lower().replace(" ", "")

    if age < 18:
        return "{'output': 'Non Eligible : l'utilisateur doit être majeur.'}"
    if nat_lower not in EU_NATIONALITIES:
        return "{'output': 'Non Eligible : la nationalité doit être européenne.'}"
    if not has_eu_bank_account:
        return "{'output': 'Non Eligible : l'utilisateur doit posséder un compte bancaire dans l'UE.'}"
    
    return "{'output': 'Eligible'}"



# define structure of output for any guardrail agents
class GuardrailOutput(BaseModel):
    is_triggered: bool
    reasoning: str



from agents import Runner,gen_trace_id, trace
from langsmith.wrappers import OpenAIAgentsTracingProcessor

#from agents import set_trace_processors
#set_trace_processors([OpenAIAgentsTracingProcessor()])

async def main(model: str, api_key: str, base_url: str):

    trace_id = gen_trace_id()
    with trace("Customer onboarding trace", trace_id=trace_id):
        print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")


        agent = Agent(
            name="Customer onboarding assistant",
            instructions=(
                "You are an AI assistant in charge of customer onboarding for an online bank."
                "You answer questions about banking offers and services."
                "Just answer the question in a short sentence."
            ),
            model=LitellmModel(model=model,
                                api_key=api_key,
                                base_url=base_url),
        )

        result = await Runner.run(
            starting_agent=agent,
            input="What is the difference between a credit and a debit card?"
        )
        print(result.final_output)

        ####
        # FUNCTION CALLING NOT WORKING WITH OLLAMA
        ####   
        # elligibility_agent = Agent(
        #     name="Elligibility agent",
        #     instructions=(
        #         "You are an AI assistant in charge of verifying a prospect's eligibility for an online bank. "
        #         "You can verify a prospect's eligibility using the `eligibility_checker` tool. "
        #         "If the prospect is eligible, just respond 'Eligible.' Otherwise, explain the reason. "
        #         "After calling the `eligibility_checker` tool and receiving its output, generate the final response based on the tool's output. "
        #         "Do not call the `eligibility_checker` tool again."
        #     ),
        #     model=LitellmModel(model=model,
        #                         api_key=api_key,
        #                         base_url=base_url),# "gpt-4o-mini",
        #     tools=[eligibility_checker],
        #     # input_guardrails=[sensitive_data_guardrail],  # note this is a list of guardrails
        # )

        # result = await Runner.run(
        #     starting_agent=elligibility_agent,
        #     input="I'm a french citizen, 25 years old, and I have a bank account in France. Am I eligible to open an account?"
        # )
        # print(result.final_output)

        ####
        # STRUCTURED OUTPUTS
        ####
        # structured output is not pass to ollama with litellm in metadata, so we need to pass it in the input
        sensitive_data_agent = Agent(
            name="Sensitive data check",
            instructions="""You are an AI that must respond with a JSON object strictly following the structure below:
            {
            "is_triggered": true,
            "reasoning": "A short explanation of why the event was triggered."
            }
            Only return the JSON. Do not add any other explanation.
            Check if the user is sharing sensitive financial data such as credit card numbers, CVV codes, IBAN numbers, or full account numbers.""",
            output_type=GuardrailOutput,
            model=LitellmModel(model=model,
                                api_key=api_key,
                                base_url=base_url),
        )

        query = "Mon numéro de carte est 4921 8532 7614 9023 avec le code 123 au dos, pouvez-vous vérifier si elle est bien enregistrée ?"

        result = await Runner.run(starting_agent=sensitive_data_agent, input=query)
        print(result.final_output)

        ####
        # GUARDRAILS
        ####

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

        agent = Agent(
                name="Customer onboarding assistant",
                instructions=(
                    "You are an AI assistant in charge of customer onboarding for an online bank.\n"
                    "You answer questions about banking offers and services.\n"
                    "Answer by a single sentence whenever possible."
                ),
                model=LitellmModel(model="mistral/mistral-small-latest"),
                # seems to complex to combine answer and function calling here (due to ollama?)
                # tools=[eligibility_checker],
                input_guardrails=[sensitive_data_guardrail],  # note this is a list of guardrails
            )

        result = await Runner.run(
            starting_agent=agent,
            input="Can you tell me if my card 4921 8532 7614 9023 is a credit card or a debit card?"
        )
        print(result.final_output)


def _get_api_key(provider: str):
    return os.environ.get(provider)


if __name__ == "__main__":

 # First try to get model/api key from args
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", type=str, required=False)
    parser.add_argument("--model", type=str, required=False)
    parser.add_argument("--api-key", type=str, required=False)
    args = parser.parse_args()

    ####
    # SETUP
    ####
    default_provider = "ollama"
    default_ollama_model = "hf.co/bartowski/Ministral-8B-Instruct-2410-GGUF:Q4_K_M"
    provider = args.provider
    if not provider:
        provider = input(f"Enter a provider name for Litellm (default is {default_provider}): ")

    model = args.model
    if not model:
        model = input("Enter a model name for Litellm (optional): ")

    api_key = args.api_key
    if not api_key:
        api_key = input("Enter an API key for Litellm (optional if in .env): ")

    base_url = None

    if not provider:
        provider = "ollama"

    if provider == "mistral":
        model = "mistral/mistral-small-latest"
        api_key = _get_api_key("MISTRAL_API_KEY")

    if provider == "anthropic":
        model = "claude-3-5-haiku-20241022"
        api_key = _get_api_key("ANTHROPIC_API_KEY")

    if provider=="ollama":
        print(f"Using default model '{default_ollama_model}' from provider '{provider}'")
        model = f"ollama/{default_ollama_model}" # "ollama/llama3.2:3b" # 
        base_url = "http://192.168.1.82:11434" # do not put "/" at the end of the base_url


    asyncio.run(main(model, api_key, base_url))  # Use asyncio.run to execute the function