import configparser

from langchain_core.messages import HumanMessage, AIMessage

from customer_onboarding.commons import SupportedModel
from customer_onboarding.assistants import create_customer_onboarding_assistant


default_model = SupportedModel.DEFAULT


def test_customer_onboarding_assistant():

    config = configparser.ConfigParser()
    config.read('config.ini')
    _faq_directory = config.get('FAQAgent', 'faq_directory')
    _persist_directory = config.get('FAQAgent', 'persist_directory')

    customer_onboarding_assistant = create_customer_onboarding_assistant(model_name=default_model,
                                                                         faq_directory=_faq_directory,
                                                                         persist_directory=_persist_directory)

    chat_history = [
        HumanMessage(content="Je veux ouvrir un compte."),
        AIMessage(content="Question: Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en France."),
        AIMessage(content="Question:Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français."),
        AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    ]

    session_id = '12345'
    # message_history = get_message_history(session_id)
    # # message_history.add_messages(chat_history)
    #
    # # human_msg1 = "Oui, j'ai un compte bancaire en France."
    human_msg1 = "Je veux ouvrir un compte."
    ai_msg_1 = customer_onboarding_assistant.invoke(input={'input': human_msg1, 'user_session_id': session_id},
                                                    config={'configurable': {'session_id': session_id}})
    print(ai_msg_1)

    human_msg2 = "Je réside en France."
    ai_msg_2 = customer_onboarding_assistant.invoke(input={'input': human_msg2, 'user_session_id': session_id},
                                                    config={'configurable': {'session_id': session_id}})
    print(ai_msg_2)

    human_msg3 = "Oui, je suis Français."
    ai_msg_3 = customer_onboarding_assistant.invoke(input={'input': human_msg3, 'user_session_id': session_id},
                                                    config={'configurable': {'session_id': session_id}})
    print(ai_msg_3)

    human_msg4 = "Oui, j'ai déjà un compte bancaire en France dont je suis titulaire."
    ai_msg_3 = customer_onboarding_assistant.invoke(input={'input': human_msg4, 'user_session_id': session_id},
                                                    config={'configurable': {'session_id': session_id}})
    print(ai_msg_3)

    # session_id = '54321'
    # human_msg2 = "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?"
    # ai_msg_2 = customer_onboarding_assistant.invoke(input={'input': human_msg2, 'session_id': session_id},
    #                                                 config={'configurable': {'session_id': session_id}})
    #print(ai_msg_2)
