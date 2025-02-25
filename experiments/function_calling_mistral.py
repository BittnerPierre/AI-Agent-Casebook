import json
import os
from mistralai import Mistral
import pandas as pd

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

# Configuration variables
EXECUTE_PART_1 = False  # Set to True to execute Part 1
EXECUTE_PART_2 = True  # Set to True to execute Part 2

##########
# FIRST CHECK THAT MISTRAL LARGE FUNCTION CALLING BEHAVE AS EXPECTED AS IN MISTRAL DOCUMENTATION
# https://docs.mistral.ai/capabilities/function_calling/
#####

# Assuming we have the following data
data = {
    'transaction_id': ['T1001', 'T1002', 'T1003', 'T1004', 'T1005'],
    'customer_id': ['C001', 'C002', 'C003', 'C002', 'C001'],
    'payment_amount': [125.50, 89.99, 120.00, 54.30, 210.20],
    'payment_date': ['2021-10-05', '2021-10-06', '2021-10-07', '2021-10-05', '2021-10-08'],
    'payment_status': ['Paid', 'Unpaid', 'Paid', 'Paid', 'Pending']
}

# Create DataFrame
df = pd.DataFrame(data)

import functools


def retrieve_payment_status(df: data, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'status': df[df.transaction_id == transaction_id].payment_status.item()})
    return json.dumps({'error': 'transaction id not found.'})


def retrieve_payment_date(df: data, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'date': df[df.transaction_id == transaction_id].payment_date.item()})
    return json.dumps({'error': 'transaction id not found.'})


tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_payment_status",
            "description": "Get payment status of a transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction id.",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_payment_date",
            "description": "Get payment date of a transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction id.",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    }
]


names_to_functions = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df)
}


client = Mistral(api_key=api_key)
if EXECUTE_PART_1:

    import json
    import os
    from mistralai import Mistral

    api_key = os.environ["MISTRAL_API_KEY"]
    model = "mistral-large-latest"

    messages = [{"role": "user", "content": "What's the status of my transaction T1001?"}]

    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="any",
    )

    print(response)

    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    function_params = json.loads(tool_call.function.arguments)
    print("\nfunction_name: ", function_name, "\nfunction_params: ", function_params)

    function_result = names_to_functions[function_name](**function_params)

    # Check if function_result is equal to '{"status": "Paid"}'
    result_json = json.loads(function_result)
    if result_json.get('status') == 'Paid':
        print("The status is 'Paid'.")
    else:
        print("The status is not 'Paid'.")


##########
# SECOND PART
# CHECK THAT MISTRAL LARGE FUNCTION CALLING HAS AN ISSUE SYNTHETIZE from tool answer
# https://docs.mistral.ai/capabilities/function_calling/
#####

if EXECUTE_PART_2:
    tools2 = [
        {
            "type": "function",
            "function": {
                "name": "faq_answerer",
                "description": "Useful IF you need to answer a general question on bank products, offers and services.\n"
                               "You must provide 'input'.\n"
                               "DO NOT USE MULTI-ARGUMENTS INPUT.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "User input which could be a question or an answer."
                        }
                    },
                    "required": ["input"]
                }
            }
        }
    ]

    system = """You are an customer onboarding AI chatbot.
        Your goal is to answer questions on products and services offered by the company.
        
        You respond to the user as clearly with honest, helpful and accurate answer. 
        You do not answer question not related to your main goals.
        
        # DIRECTIVES
        - NEVER respond directly to a user question and use tools to retrieve relevant information.
        - Keep conversation as short as possible.
        - Ask question to user if his question needs clarification.
        - Do NOT make any reference to tools to user.
        - Never mention to user: action_name, tool_name, function,
            token or any internal informations used for processing conversation.
        
        # INSTRUCTIONS
        Step 1. You first greet the customer, then ask how you can help him
        Step 2. Answer his question 
        - If your answer is not satisfying, you ask for more details and clarification.
        Step 3. Asks if he has another question and answer it with the same process at Step 2.
        Step 4. Finally, if user does not have any more question, you ask for customer feedback on your service.
        
        # STYLE
        You respond in a short, conversational friendly tone.
        """

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "What should I do if my card is blocked at an ATM?"},
        {"role": "assistant", "content": "", "tool_calls":
            [{"id": "t1TO1tl5o", "function":
                {"name": "faq_answerer", "arguments":
                    {"input": "What should I do if my card is blocked at an ATM?"}}}]},
        {"role": "tool", "content": "If your card is blocked at an ATM,"
                                    " immediately report it using our mobile app under 'Card Services' > 'Block Card'"
                                    " and request a replacement.", "name": "faq_answerer",
         "tool_call_id": "t1TO1tl5o"},
    ]

    ######
    # TEST MISTRAL LARGE
    #####

    model = "mistral-small-latest"

    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools2,
        tool_choice="auto",
    )
    response_content = response.choices[0].message.content
    print("Response should be to immediately report the lost using the mobile app and not 'Any other question ?'")
    print(f"Model: '{model}'")
    print(f"Answer: '{response_content}'")

    ######
    # TEST MISTRAL SMALL
    #####

    model = "mistral-small-2402"

    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools2,
        tool_choice="auto",
    )
    response_content = response.choices[0].message.content
    print(f"Model: '{model}'")
    print(f"Answer: '{response_content}'")
