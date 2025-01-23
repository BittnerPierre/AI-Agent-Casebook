from langchain import hub
from langsmith import evaluate
from langsmith.evaluation import LangChainStringEvaluator

from customer_onboarding.agents import ProblemSolverAgent
from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel

default_model = SupportedModel.DEFAULT

model = initiate_model(default_model)
embeddings = initiate_embeddings(default_model)


def test_problem_solver_agent(config):

    _chroma_persist_directory = config.get('Retrieval', 'persist_directory')
    _problem_directory = config.get('ProblemSolverAgent', 'problem_directory')
    _problem_file = config.get('ProblemSolverAgent', 'problem_file')
    _problem_database = config.get('ProblemSolverAgent', 'problem_database')

    agent = ProblemSolverAgent(model=model,
                               embeddings=embeddings,
                               problem_directory=_problem_directory,
                               persist_directory=_chroma_persist_directory,
                               problem_file=_problem_file)

    print("Test Problem 1 - OK - Answer")
    chat_history = []
    first_message = "Je n'ai pas recu d'email pour confirmer l'ouverture de mon compte."
    ai_msg_1 = agent.invoke(input={"input": [first_message], "chat_history": chat_history})
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
    ai_msg_1 = agent.invoke(input={"input": [first_message], "chat_history": chat_history})
    print(ai_msg_1)

    # assert "nouveau code" in ai_msg_1.lower()


def test_problem_solver_agent_langsmith(config):

    _chroma_persist_directory = config.get('Retrieval', 'persist_directory')
    _problem_directory = config.get('ProblemSolverAgent', 'problem_directory')
    _problem_file = config.get('ProblemSolverAgent', 'problem_file')

    agent = ProblemSolverAgent(model=model,
                               embeddings=embeddings,
                               persist_directory=_chroma_persist_directory,
                               problem_directory=_problem_directory,
                               problem_file=_problem_file)

    prompt = hub.pull("customer-onboarding-evaluator")
    eval_llm = initiate_model(model_name=default_model)

    qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": prompt})

    evaluate(
        agent.get_runnable,
        data="PROBLEM-datasets-03-12-2024",
        evaluators=[qa_evaluator],
        experiment_prefix="test-problem",
    )
