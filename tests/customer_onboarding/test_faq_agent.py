import pytest
from langchain import hub
from langsmith import evaluate
from langsmith.evaluation import LangChainStringEvaluator

from customer_onboarding.agents import FAQAgent
from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel

default_model = SupportedModel.DEFAULT

model = initiate_model(default_model)
embeddings = initiate_embeddings(default_model)


@pytest.fixture
def fag_agent(config):
    _faq_file = config.get('FAQAgent', 'faq_file')

    agent = FAQAgent(model=model,
                     embeddings=embeddings,
                     source_paths=_faq_file)

    return agent


def test_faq_agent(fag_agent):
    """
    This is to show that it is better to handle test with a dedicated framework...
    Returns:
    """
    print("Test FAQ 1 - OK - Answer")
    chat_history = []
    first_message = "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?"
    ai_msg_1 = fag_agent.invoke(input={"question": first_message, "chat_history": chat_history})
    print(ai_msg_1)
    # TODO student exercice, FAQ agent prompt should be fixed to not answer when no context is provided.
    assert "carte de crédit" in ai_msg_1.lower()
    assert "carte de débit" in ai_msg_1.lower()

    print("Test FAQ 2 - OK - No answer")
    chat_history = []
    first_message = ("Pouvez-vous me donner des conseils sur la meilleure destination de voyage"
                     " pour mes prochaines vacances ?")
    ai_msg_1 = fag_agent.invoke(input={"question": first_message, "chat_history": chat_history})
    print(ai_msg_1)

    assert "je ne peux pas répondre" in ai_msg_1.lower()


def test_faq_agent_langsmith(fag_agent):

    prompt = hub.pull("customer-onboarding-evaluator")
    eval_llm = initiate_model(model_name=default_model)

    qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": prompt})

    evaluate(
        fag_agent.get_runnable,
        data="FAQ-datasets-25-11-2024",
        evaluators=[qa_evaluator],
        experiment_prefix="test-faq",
    )
