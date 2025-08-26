import uuid
from typing import TypedDict, Literal

from langchain import hub
from langchain_core.messages import HumanMessage
from langchain_openai import OpenAI
from langsmith import evaluate, wrappers
from langsmith.evaluation import LangChainStringEvaluator

from app.core.commons import initiate_model
from app.core.base import SupportedModel
from app.video_script.assistant import create_video_script_agent

default_model = SupportedModel.DEFAULT

TESTING = False

agent = create_video_script_agent()

# FOR TESTING THE TEST :)
TEST_SCRIPT_FILENAME = "tests/video_script/test_script.txt"


def load_test_script(logger):
    try:
        with open(TEST_SCRIPT_FILENAME, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"No guidelines available {TEST_SCRIPT_FILENAME}.")
        return "No script guidelines available."


class ScriptEvaluatorFeedback(TypedDict):
    Grade: Literal['ACCEPTABLE', 'UNACCEPTABLE']
    Score: int
    Comment: str


eval_llm = initiate_model(default_model)

script_evaluator_prompt = hub.pull("video-script-evaluator")

script_evaluator = script_evaluator_prompt | eval_llm.with_structured_output(ScriptEvaluatorFeedback)


def valid_script(input: str, output: str) -> ScriptEvaluatorFeedback:
  """Use an LLM to judge if the script is consistent."""

  res = script_evaluator.invoke(input={"input": input, "response": output})
  return res


async def test_video_script_evaluator(config, logger):
    logger.info(f"test_video_script_evaluator START (test_mode={TESTING})")

    input = ("Je voudrais une vidéo en deux chapitres d'une durée de 2 minutes et contenant 450 mots sur le sujet "
             "`L'IA ne prendra pas votre travail. Ceux qui utilisent l'IA, oui !`, s'il vous plaît !")

    if TESTING:
        output = load_test_script(logger)
    else:

        session_id = config.configurable.get("session_id") if config and hasattr(config, 'configurable') else str(
            uuid.uuid4())
        thread_id = config.configurable.get("thread_id") if config and hasattr(config, 'configurable') else str(
            uuid.uuid4())

        effective_config = {"configurable": {"session_id": session_id, "thread_id": thread_id}, "recursion_limit": 99}

        input_data = {'messages': [HumanMessage(content=input)],}

        steps = [step async for step in agent.astream(input=input_data, config=effective_config, stream_mode="values")]

        # Access the last step
        last_step = steps[-1]

        # Print the last message of the last step
        last_message = last_step["messages"][-1]
        output = last_message.pretty_repr()

    res = valid_script(input, output)

    logger.info(f"test_video_script_evaluator END {res} (test_mode={TESTING})")
    assert res["Grade"], "Acceptable"

    # qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": prompt})
    #
    # evaluate(
    #     output,
    #     data="PROBLEM-datasets-03-12-2024",
    #     evaluators=[qa_evaluator],
    #     experiment_prefix="video-script-evaluator",
    # )
