from langchain_core.messages import HumanMessage, AIMessage

from customer_onboarding.agents import EligibilityAgent
from customer_onboarding.commons import SupportedModel

default_model = SupportedModel.DEFAULT


def test_eligibility_agent():
    # TEST 1 SHOULD BE KO
    print("Test 1 - KO")
    chat_history = [
        HumanMessage(content="Je souhaite ouvrir un compte."),
        AIMessage(content="Question: Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside au Canada."),
        AIMessage(content="Question:Êtes-vous de nationalité française ?"),
        HumanMessage(content="Non, je suis Italien."),
        AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    ]
    agent = EligibilityAgent(model_name=default_model)
    fourth_message = HumanMessage(content="Oui, j'ai un compte bancaire en France.")
    ai_msg_4 = agent.answer_question(fourth_message, chat_history)
    chat_history.extend([fourth_message, AIMessage(content=ai_msg_4)])
    print(ai_msg_4)

    # TEST 2 SHOULD BE KO
    print("Test 2 - KO")
    chat_history = [
        HumanMessage(content="Je souhaite ouvrir un compte."),
        AIMessage(content="Question: Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en Belgique."),
        AIMessage(content="Question:Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français."),
        AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    ]
    fourth_message = HumanMessage(content="Non, je n'ai pas de compte bancaire en France.")
    ai_msg_4 = agent.answer_question(fourth_message, chat_history)
    chat_history.extend([fourth_message, AIMessage(content=ai_msg_4)])
    print(ai_msg_4)

    # TEST KO
    print("Test 3 - KO")
    chat_history = [
        HumanMessage(content="Je souhaite ouvrir un compte."),
        AIMessage(content="Question: Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en Belgique."),
        AIMessage(content="Question:Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français."),
        AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    ]
    forth_message = HumanMessage(content="J'ai un compte bancaire mais il est au nom de mon père. J'ai 14 ans.")
    agent = EligibilityAgent(model_name=default_model)
    ai_msg_4 = agent.answer_question(forth_message, chat_history)
    chat_history.extend([forth_message, AIMessage(content=ai_msg_4)])
    print(ai_msg_4)

    # TEST OK
    print("Test 4 - Test OK")
    agent = EligibilityAgent(model_name=default_model)
    chat_history = [
        HumanMessage(content="Je veux ouvrir un compte."),
        AIMessage(content="Question: Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en France."),
        AIMessage(content="Question:Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français."),
        AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    ]
    forth_message = HumanMessage(content="Oui, j'ai un compte bancaire en France.")
    ai_msg_4 = agent.answer_question(forth_message, chat_history)
    chat_history.extend([forth_message, AIMessage(content=ai_msg_4)])
    print(ai_msg_4)
