import configparser

from langchain_core.messages import HumanMessage

from langchain_openai import ChatOpenAI
from langchain import hub
from langsmith import evaluate
from langsmith.evaluation import LangChainStringEvaluator

from customer_onboarding.agents import ProblemSolverAgent
from customer_onboarding.commons import SupportedModel, initiate_model

default_model = SupportedModel.GPT_4_O

config = configparser.ConfigParser()
config.read('config.ini')
_problem_directory = config.get('ProblemSolverAgent', 'problem_directory')
_persist_directory = config.get('ProblemSolverAgent', 'persist_directory')


def test_problem_solver_agent():

    agent = ProblemSolverAgent(model_name=default_model,
                               problem_directory=_problem_directory,
                               persist_directory=_persist_directory)

    print("Test Problem 1 - OK - Answer")
    chat_history = []
    first_message = "Je n'ai pas recu d'email pour confirmer l'ouverture de mon compte."
    ai_msg_1 = agent.answer_question(first_message, chat_history)
    print(ai_msg_1)
    # TODO student exercice, FAQ agent prompt should be fixed to not answer when no context is provided.
    # assert "spam" in ai_msg_1.lower()

    # print("Test Problem 2 - OK - Answer")
    # chat_history = []
    # first_message = "Le code SMS que j'ai recu ne fonctionne pas."
    # ai_msg_1 = agent.answer_question(first_message, chat_history)
    # print(ai_msg_1)

    print("Test Problem 3 - OK - Answer")
    chat_history = []
    first_message = "J'ai le code d'erreur CONN-SMS-002."
    ai_msg_1 = agent.answer_question(first_message, chat_history)
    print(ai_msg_1)

    # assert "nouveau code" in ai_msg_1.lower()


# def test_problem_solver_agent_langsmith():
#
#     agent = ProblemSolverAgent(model_name=default_model,
#                      persist_directory=_persist_directory,
#                      problem_directory=_problem_directory)
#
#     prompt = hub.pull("customer-onboarding-evaluator")
#     eval_llm = initiate_model(model_name=default_model)
#
#     qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": prompt})
#
#     experiments_results = evaluate(
#         agent.runnable_chain,
#         data="FAQ-datasets-25-11-2024",
#         evaluators=[qa_evaluator],
#         experiment_prefix="test-faq-25-11-2024",
#     )