import configparser

from langchain_core.messages import HumanMessage

from langchain_openai import ChatOpenAI
from langchain import hub
from langsmith import evaluate
from langsmith.evaluation import LangChainStringEvaluator

from customer_onboarding.agents import FAQAgent
from customer_onboarding.commons import SupportedModel, initiate_model

default_model = SupportedModel.GPT_4_O

config = configparser.ConfigParser()
config.read('config.ini')
_faq_directory = config.get('FAQAgent', 'faq_directory')
_persist_directory = config.get('FAQAgent', 'persist_directory')


def test_faq_agent():

    agent = FAQAgent(model_name=default_model,
                     persist_directory=_persist_directory,
                     faq_directory=_faq_directory)

    print("Test FAQ 1 - OK - Answer")
    chat_history = []
    first_message = "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?"
    ai_msg_1 = agent.answer_question(first_message, chat_history)
    print(ai_msg_1)
    # TODO student exercice, FAQ agent prompt should be fixed to not answer when no context is provided.
    assert "carte de crédit" in ai_msg_1.lower()
    assert "carte de débit" in ai_msg_1.lower()

    print("Test FAQ 2 - OK - No answer")
    chat_history = []
    first_message = "Pouvez-vous me donner des conseils sur la meilleure destination de voyage pour mes prochaines vacances ?"
    ai_msg_1 = agent.answer_question(first_message, chat_history)
    print(ai_msg_1)

    assert "désolé" in ai_msg_1.lower()
    assert "me donner des conseils sur les destinations de voyage"


def test_faq_agent_langsmith():

    agent = FAQAgent(model_name=default_model,
                     persist_directory=_persist_directory,
                     faq_directory=_faq_directory)

    prompt = hub.pull("customer-onboarding-evaluator")
    eval_llm = initiate_model(model_name=default_model)

    qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": prompt})

    experiments_results = evaluate(
        agent.runnable_chain,
        data="FAQ-datasets-25-11-2024",
        evaluators=[qa_evaluator],
        experiment_prefix="test-faq-25-11-2024",
    )