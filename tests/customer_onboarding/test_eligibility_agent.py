from customer_onboarding.agents import EligibilityAgent
from core.commons import SupportedModel, initiate_model

default_model = SupportedModel.DEFAULT

model = initiate_model(default_model)

def test_eligibility_agent():
    # TEST 1 SHOULD BE KO
    print("Test 1 - KO")
    agent = EligibilityAgent(model=model)
    # chat_history = [
    #     HumanMessage(content="Je souhaite ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside au Canada."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Non, je suis Italien."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    # fourth_message = HumanMessage(content="Oui, j'ai un compte bancaire en France.")
    # ai_msg_4 = agent.invoke(input={"input": fourth_message, "chat_history": chat_history})
    # chat_history.extend([fourth_message, AIMessage(content=ai_msg_4)])

    est_titulaire_compte_bancaire = "Oui"
    age = ""
    nationality = "Italienne"
    pays_de_residence_fiscale="Canada"
    ai_msg_4 = agent.invoke(input={"est_titulaire_compte_bancaire":est_titulaire_compte_bancaire,
                                   "age": age,
                                   "nationalite": nationality,
                                   "pays_de_residence_fiscale": pays_de_residence_fiscale})
    print(ai_msg_4)

    # TEST 2 SHOULD BE KO
    print("Test 2 - KO")
    # chat_history = [
    #     HumanMessage(content="Je souhaite ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside en Belgique."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Oui, je suis Français."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    # fourth_message = HumanMessage(content="Non, je n'ai pas de compte bancaire en France.")
    # ai_msg_4 = agent.invoke(input={"input": fourth_message, "chat_history": chat_history})
    # chat_history.extend([fourth_message, AIMessage(content=ai_msg_4)])

    est_titulaire_compte_bancaire = "Non"
    age = "21"
    nationality = "Française"
    pays_de_residence_fiscale = "Belgique"
    ai_msg_4 = agent.invoke(input={"est_titulaire_compte_bancaire": est_titulaire_compte_bancaire,
                                   "age": age,
                                   "nationalite": nationality,
                                   "pays_de_residence_fiscale": pays_de_residence_fiscale})
    print(ai_msg_4)

    # TEST KO
    print("Test 3 - KO")
    # chat_history = [
    #     HumanMessage(content="Je souhaite ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside en Belgique."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Oui, je suis Français."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    # forth_message = HumanMessage(content="J'ai un compte bancaire mais il est au nom de mon père. J'ai 14 ans.")
    # agent = EligibilityAgent(model_name=default_model)
    # ai_msg_4 = agent.invoke(input={"input": forth_message, "chat_history": chat_history})
    # chat_history.extend([forth_message, AIMessage(content=ai_msg_4)])

    est_titulaire_compte_bancaire = "Non"
    age = "14"
    nationality = "Française"
    pays_de_residence_fiscale = "Belgique"
    ai_msg_4 = agent.invoke(input={"est_titulaire_compte_bancaire": est_titulaire_compte_bancaire,
                                   "age": age,
                                   "nationalite": nationality,
                                   "pays_de_residence_fiscale": pays_de_residence_fiscale})

    print(ai_msg_4)

    # TEST OK
    print("Test 4 - Test OK")
    # agent = EligibilityAgent(model_name=default_model)
    # chat_history = [
    #     HumanMessage(content="Je veux ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside en France."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Oui, je suis Français."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    # forth_message = HumanMessage(content="Oui, j'ai un compte bancaire en France.")
    # ai_msg_4 = agent.invoke(input={"input": [forth_message], "chat_history": chat_history})
    # chat_history.extend([forth_message, AIMessage(content=ai_msg_4)])

    est_titulaire_compte_bancaire = "Oui"
    age = "31"
    nationality = "Française"
    pays_de_residence_fiscale = "France"
    ai_msg_4 = agent.invoke(input={"est_titulaire_compte_bancaire": est_titulaire_compte_bancaire,
                                   "age": age,
                                   "nationalite": nationality,
                                   "pays_de_residence_fiscale": pays_de_residence_fiscale})

    print(ai_msg_4)
