import configparser


from customer_onboarding.assistants import customer_onboarding



# TODO should assert returned value
def test_customer_onboarding_assistant_eligibility(assistant):

    # Note: Conversation is handled by Assistant so no need here

    session_id = '12345'
    human_msg1 = "Je veux ouvrir un compte."
    ai_msg_1 = customer_onboarding.invoke(input={'messages': human_msg1},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})
    print(ai_msg_1)

    human_msg2 = "Je réside en France."
    ai_msg_2 = customer_onboarding.invoke(input={'messages': human_msg2},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})
    print(ai_msg_2)

    human_msg3 = "Oui, je suis Français. J'ai 24 ans."
    ai_msg_3 = customer_onboarding.invoke(input={'messages': human_msg3},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})
    print(ai_msg_3)

    human_msg4 = "Oui, j'ai déjà un compte bancaire en France dont je suis titulaire."
    ai_msg_4 = customer_onboarding.invoke(input={'messages': human_msg4},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})
    print(ai_msg_4)


def test_customer_onboarding_assistant_faq(assistant):
    session_id = '97531'
    human_msg7 = "What should I do if my card is blocked at an ATM?"
    ai_msg_7 = customer_onboarding.invoke(input={'messages': human_msg7},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})
    # BASIC ANSWER
    print(ai_msg_7)


def test_customer_onboarding_assistant_problem(assistant):
    session_id = '13579'
    human_msg5 = "Je n'ai pas recu d'email pour confirmer l'ouverture de mon compte."
    ai_msg_5 = customer_onboarding.invoke(input={'messages': human_msg5},
                                config={'configurable': {'session_id': session_id, 'thread_id': session_id}})

    # TODO CHECK THAT IT ASK FOR ELIGIBILITY FIRST (this is the case)
    print(ai_msg_5)